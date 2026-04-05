import razorpay
from django.conf import settings
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..emails import send_order_confirmation
from ..models import (
    BankDetail,
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Payment,
    Product,
    Review,
    ShippingAddress,
    WishlistItem,
)
from ..payment_flow import finalize_order_after_payment
from ..tracking import compute_tracking_display, refresh_order_tracking
from .permissions import IsAdminOrReadOnly
from .serializers import (
    BankDetailSerializer,
    CartSerializer,
    CategorySerializer,
    OrderSerializer,
    OrderSummarySerializer,
    ProductDetailSerializer,
    ProductListSerializer,
    ReviewSerializer,
    ShippingAddressSerializer,
    WishlistSerializer,
)


class BankDetailViewSet(viewsets.ReadOnlyModelViewSet):
    """Active bank accounts for manual transfer (NEFT/IMPS/UPI)."""

    serializer_class = BankDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return BankDetail.objects.filter(is_active=True).order_by('sort_order', 'id')


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        qs = Category.objects.all()
        if not (self.request.user and self.request.user.is_staff):
            qs = qs.filter(is_active=True)
        return qs


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.filter(is_active=True).select_related('category').prefetch_related(
        'images', 'reviews'
    )
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category']
    search_fields = ['name', 'description', 'sku']
    ordering_fields = ['price', 'created_at', 'name']
    ordering = ['-created_at']

    def get_permissions(self):
        if self.action == 'retrieve':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer


class CartViewSet(viewsets.GenericViewSet):
    serializer_class = CartSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Cart.objects.all()

    def get_cart(self):
        cart, _ = Cart.objects.get_or_create(user=self.request.user)
        return cart

    def list(self, request):
        cart = self.get_cart()
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['post'], url_path='items')
    def add_item(self, request):
        cart = self.get_cart()
        pid = request.data.get('product_id')
        product = get_object_or_404(Product, pk=pid, is_active=True)
        qty = max(1, int(request.data.get('quantity', 1)))
        item, created = CartItem.objects.get_or_create(cart=cart, product=product, defaults={'quantity': qty})
        if not created:
            item.quantity = qty
            item.save(update_fields=['quantity'])
        return Response(CartSerializer(cart).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch', 'put'], url_path=r'items/(?P<item_id>[^/.]+)')
    def update_item(self, request, item_id=None):
        cart = self.get_cart()
        item = get_object_or_404(CartItem, pk=item_id, cart=cart)
        q = int(request.data.get('quantity', item.quantity))
        if q < 1:
            item.delete()
        else:
            item.quantity = q
            item.save(update_fields=['quantity'])
        return Response(CartSerializer(cart).data)

    @action(detail=False, methods=['delete'], url_path=r'items/(?P<item_id>[^/.]+)/remove')
    def remove_item(self, request, item_id=None):
        cart = self.get_cart()
        CartItem.objects.filter(pk=item_id, cart=cart).delete()
        return Response(CartSerializer(cart).data)


class WishlistViewSet(viewsets.ModelViewSet):
    serializer_class = WishlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return WishlistItem.objects.filter(user=self.request.user).select_related('product', 'product__category')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='toggle')
    def toggle(self, request):
        pid = request.data.get('product_id')
        product = get_object_or_404(Product, pk=pid, is_active=True)
        w = WishlistItem.objects.filter(user=request.user, product=product).first()
        if w:
            w.delete()
            return Response({'in_wishlist': False})
        WishlistItem.objects.create(user=request.user, product=product)
        return Response({'in_wishlist': True}, status=status.HTTP_201_CREATED)


class ShippingAddressViewSet(viewsets.ModelViewSet):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ShippingAddress.objects.filter(user=self.request.user)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderSummarySerializer
        return OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related('items__product', 'payment')
            .order_by('-created_at')
        )

    @action(detail=True, methods=['get'])
    def tracking(self, request, pk=None):
        order = self.get_object()
        refresh_order_tracking(order, send_mail_flag=True)
        order.refresh_from_db()
        d = compute_tracking_display(order)
        return Response({'order_id': order.id, **d, 'status': order.status})

    @action(detail=False, methods=['post'], url_path='checkout')
    def checkout(self, request):
        """Create pending order; Razorpay order or bank-transfer instructions."""
        payment_method = (request.data.get('payment_method') or 'razorpay').lower()
        if payment_method not in ('razorpay', 'bank_transfer'):
            return Response({'detail': 'payment_method must be razorpay or bank_transfer'}, status=400)

        if payment_method == 'bank_transfer':
            bank_qs = BankDetail.objects.filter(is_active=True).order_by('sort_order', 'id')
            if not bank_qs.exists():
                return Response(
                    {'detail': 'Bank transfer unavailable. Add active bank details in admin.'},
                    status=400,
                )

        address_id = request.data.get('address_id')
        addr = get_object_or_404(ShippingAddress, pk=address_id, user=request.user)
        cart, _ = Cart.objects.get_or_create(user=request.user)
        items = list(cart.items.select_related('product'))
        if not items:
            return Response({'detail': 'Cart is empty'}, status=400)
        for ci in items:
            if ci.product.stock < ci.quantity:
                return Response(
                    {'detail': f'Insufficient stock for {ci.product.name}'},
                    status=400,
                )
        lines = '\n'.join(
            [
                f'{addr.full_name}, {addr.phone}\n{addr.line1}\n{addr.line2}\n'
                f'{addr.city}, {addr.state} {addr.postal_code}\n{addr.country}'
            ]
        )
        subtotal = sum(ci.line_total() for ci in items)
        amount_paise = int(subtotal * 100)
        is_bank = payment_method == 'bank_transfer'
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                status=Order.Status.PENDING_PAYMENT,
                shipping_address=lines,
                subtotal=subtotal,
                total=subtotal,
            )
            for ci in items:
                OrderItem.objects.create(
                    order=order,
                    product=ci.product,
                    quantity=ci.quantity,
                    unit_price=ci.product.price,
                )
            pay = Payment.objects.create(
                order=order,
                method=(
                    Payment.Method.BANK_TRANSFER if is_bank else Payment.Method.RAZORPAY
                ),
                provider='bank_transfer' if is_bank else 'razorpay',
                amount_paise=amount_paise,
                currency='INR',
                status=(
                    Payment.Status.PENDING_VERIFICATION
                    if is_bank
                    else Payment.Status.CREATED
                ),
            )

        if is_bank:
            return Response(
                {
                    'order': OrderSerializer(order).data,
                    'payment_method': 'bank_transfer',
                    'bank_details': BankDetailSerializer(bank_qs, many=True).data,
                    'razorpay': None,
                },
                status=status.HTTP_201_CREATED,
            )

        key = settings.RAZORPAY_KEY_ID
        secret = settings.RAZORPAY_KEY_SECRET
        if not key or not secret:
            return Response(
                {
                    'order': OrderSerializer(order).data,
                    'payment_method': 'razorpay',
                    'razorpay': None,
                    'detail': 'Razorpay not configured — set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET',
                },
                status=status.HTTP_201_CREATED,
            )
        client = razorpay.Client(auth=(key, secret))
        rp = client.order.create(
            {
                'amount': amount_paise,
                'currency': 'INR',
                'receipt': f'ord_{order.pk}',
                'notes': {'order_id': order.pk},
            }
        )
        pay.razorpay_order_id = rp['id']
        pay.raw_response = rp
        pay.save(update_fields=['razorpay_order_id', 'raw_response'])
        return Response(
            {
                'order': OrderSerializer(order).data,
                'payment_method': 'razorpay',
                'razorpay': {
                    'key_id': key,
                    'order_id': rp['id'],
                    'amount': amount_paise,
                    'currency': 'INR',
                },
            },
            status=status.HTTP_201_CREATED,
        )


class PaymentViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]
    queryset = Payment.objects.all()

    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        order_id = request.data.get('order_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature = request.data.get('razorpay_signature')
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        pay = get_object_or_404(Payment, order=order)
        if pay.method != Payment.Method.RAZORPAY:
            return Response({'detail': 'This order uses bank transfer, not Razorpay.'}, status=400)
        if pay.status == Payment.Status.SUCCESS:
            return Response({'detail': 'Already paid', 'order': OrderSerializer(order).data})
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        try:
            client.utility.verify_payment_signature(
                {
                    'razorpay_order_id': razorpay_order_id,
                    'razorpay_payment_id': razorpay_payment_id,
                    'razorpay_signature': razorpay_signature,
                }
            )
        except razorpay.errors.SignatureVerificationError:
            pay.status = Payment.Status.FAILED
            pay.save(update_fields=['status', 'updated_at'])
            order.status = Order.Status.FAILED
            order.save(update_fields=['status'])
            return Response({'detail': 'Invalid signature'}, status=400)
        finalized = False
        with transaction.atomic():
            pay.razorpay_payment_id = razorpay_payment_id
            pay.razorpay_signature = razorpay_signature
            pay.status = Payment.Status.SUCCESS
            pay.save(
                update_fields=[
                    'razorpay_payment_id',
                    'razorpay_signature',
                    'status',
                    'updated_at',
                ]
            )
            finalized = finalize_order_after_payment(order, request.user)
        if finalized:
            send_order_confirmation(order)
        return Response({'ok': True, 'order': OrderSerializer(order).data})

    @action(detail=False, methods=['post'], url_path='bank-reference')
    def bank_reference(self, request):
        """Customer submits UTR / transaction id after NEFT/IMPS/UPI."""
        order_id = request.data.get('order_id')
        ref = (request.data.get('bank_reference') or '').strip()
        if not ref or len(ref) < 6:
            return Response({'detail': 'Enter a valid transaction reference / UTR (min 6 chars).'}, status=400)
        order = get_object_or_404(Order, pk=order_id, user=request.user)
        pay = get_object_or_404(Payment, order=order)
        if pay.method != Payment.Method.BANK_TRANSFER:
            return Response({'detail': 'Not a bank transfer order.'}, status=400)
        if pay.status == Payment.Status.SUCCESS:
            return Response(
                {'detail': 'Order already confirmed.', 'order': OrderSerializer(order).data}
            )
        pay.bank_reference = ref[:120]
        pay.bank_submitted_at = timezone.now()
        pay.save(update_fields=['bank_reference', 'bank_submitted_at', 'updated_at'])
        return Response(
            {
                'ok': True,
                'detail': 'Reference received. We will verify your payment and confirm the order.',
                'order': OrderSerializer(order).data,
            }
        )


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        qs = Review.objects.select_related('user', 'product')
        pid = self.request.query_params.get('product')
        if pid:
            qs = qs.filter(product_id=pid)
        return qs

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
