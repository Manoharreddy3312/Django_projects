from rest_framework import serializers

from ..models import (
    BankDetail,
    Cart,
    CartItem,
    Category,
    Order,
    OrderItem,
    Payment,
    Product,
    ProductImage,
    Review,
    ShippingAddress,
    WishlistItem,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'is_active')


class ProductListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'sku',
            'description',
            'price',
            'compare_at_price',
            'stock',
            'main_image',
            'category',
            'category_name',
            'average_rating',
            'is_active',
        )

    def get_average_rating(self, obj):
        return obj.average_rating


class ProductImageNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'sort_order')


class ReviewSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'product', 'user', 'user_email', 'rating', 'title', 'body', 'created_at')
        read_only_fields = ('user', 'user_email', 'created_at')

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class ProductDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    images = ProductImageNestedSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id',
            'name',
            'slug',
            'sku',
            'description',
            'price',
            'compare_at_price',
            'stock',
            'main_image',
            'images',
            'category',
            'category_name',
            'reviews',
            'average_rating',
            'is_active',
        )

    def get_average_rating(self, obj):
        return obj.average_rating


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True), source='product', write_only=True
    )

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_id', 'quantity')
        read_only_fields = ('product',)

    def validate_quantity(self, v):
        if v < 1:
            raise serializers.ValidationError('Min 1')
        return v


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ('id', 'items', 'total', 'updated_at')
        read_only_fields = fields

    def get_total(self, obj):
        return str(sum(i.line_total() for i in obj.items.all()))


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True), source='product', write_only=True
    )

    class Meta:
        model = WishlistItem
        fields = ('id', 'product', 'product_id')
        read_only_fields = ('product',)


class ShippingAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShippingAddress
        fields = (
            'id',
            'full_name',
            'phone',
            'line1',
            'line2',
            'city',
            'state',
            'postal_code',
            'country',
            'is_default',
        )

    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    line_total = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'quantity', 'unit_price', 'line_total')
        read_only_fields = fields

    def get_line_total(self, obj):
        return str(obj.line_total())


class BankDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BankDetail
        fields = (
            'id',
            'title',
            'account_holder_name',
            'bank_name',
            'branch',
            'account_number',
            'ifsc_code',
            'upi_id',
            'instructions',
        )
        read_only_fields = fields


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = (
            'id',
            'method',
            'provider',
            'razorpay_order_id',
            'razorpay_payment_id',
            'bank_reference',
            'bank_submitted_at',
            'amount_paise',
            'currency',
            'status',
            'created_at',
        )
        read_only_fields = fields


class OrderSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'status', 'total', 'created_at', 'confirmed_at')
        read_only_fields = fields


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    payment = PaymentSerializer(read_only=True)
    tracking = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id',
            'status',
            'shipping_address',
            'subtotal',
            'total',
            'created_at',
            'confirmed_at',
            'items',
            'payment',
            'tracking',
        )
        read_only_fields = fields

    def get_tracking(self, obj):
        from ..tracking import compute_tracking_display, refresh_order_tracking

        refresh_order_tracking(obj, send_mail_flag=False)
        obj.refresh_from_db()
        d = compute_tracking_display(obj)
        return {'progress': d['progress'], 'label': d['label'], 'phase': d['phase']}
