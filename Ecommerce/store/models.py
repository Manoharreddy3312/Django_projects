from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=280, unique=True)
    sku = models.CharField(max_length=64, unique=True, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    compare_at_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    @property
    def average_rating(self):
        agg = self.reviews.aggregate(avg=Avg('rating'))
        return float(agg['avg'] or 0)


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/extra/')
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [['product', 'user']]
        ordering = ['-created_at']


class ShippingAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    line1 = models.CharField(max_length=255)
    line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_default', '-id']

    def __str__(self):
        return f'{self.full_name} — {self.city}'


class Cart(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart')
    updated_at = models.DateTimeField(auto_now=True)

    def total(self):
        return sum(item.line_total() for item in self.items.all())


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = [['cart', 'product']]

    def line_total(self):
        return self.product.price * self.quantity


class WishlistItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wishlist')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    class Meta:
        unique_together = [['user', 'product']]


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = 'pending_payment', 'Pending payment'
        PLACED = 'placed', 'Order Placed'
        SHIPPING = 'shipping', 'Order Shipping'
        DISPATCHED = 'dispatched', 'Order Dispatched'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'
        FAILED = 'failed', 'Payment failed'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING_PAYMENT)
    shipping_address = models.TextField(help_text='Snapshot of address at checkout')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    tracking_email_phase = models.PositiveSmallIntegerField(
        default=0,
        help_text='0=none, 1=placed 50%, 2=shipping 75%, 3=dispatched 100%',
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'Order #{self.pk} — {self.user.email}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    def line_total(self):
        return self.unit_price * self.quantity


class BankDetail(models.Model):
    """Business bank account shown to customers for NEFT/IMPS/UPI transfers."""

    title = models.CharField(max_length=120, default='Primary account')
    account_holder_name = models.CharField(max_length=255)
    bank_name = models.CharField(max_length=255)
    branch = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(max_length=64)
    ifsc_code = models.CharField(max_length=20)
    upi_id = models.CharField(max_length=120, blank=True, help_text='Optional UPI VPA for QR / apps')
    instructions = models.TextField(
        blank=True,
        help_text='Shown on checkout (e.g. use order id as payment note).',
    )
    is_active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort_order', 'id']

    def __str__(self):
        return f'{self.title} — {self.bank_name}'


class Payment(models.Model):
    class Method(models.TextChoices):
        RAZORPAY = 'razorpay', 'Razorpay'
        BANK_TRANSFER = 'bank_transfer', 'Bank transfer'

    class Status(models.TextChoices):
        CREATED = 'created', 'Created'
        PENDING_VERIFICATION = 'pending_verification', 'Pending verification'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=32, choices=Method.choices, default=Method.RAZORPAY)
    provider = models.CharField(max_length=32, default='razorpay')
    razorpay_order_id = models.CharField(max_length=120, blank=True)
    razorpay_payment_id = models.CharField(max_length=120, blank=True)
    razorpay_signature = models.CharField(max_length=256, blank=True)
    bank_reference = models.CharField(
        max_length=120,
        blank=True,
        help_text='UTR / transaction id submitted by customer',
    )
    bank_submitted_at = models.DateTimeField(null=True, blank=True)
    amount_paise = models.PositiveIntegerField(default=0)
    currency = models.CharField(max_length=8, default='INR')
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.CREATED)
    raw_response = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
