from django.contrib import admin
from django.db import transaction
from django.utils.translation import gettext_lazy as _

from .emails import send_order_confirmation
from .models import (
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
from .payment_flow import finalize_order_after_payment


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(BankDetail)
class BankDetailAdmin(admin.ModelAdmin):
    list_display = ('title', 'bank_name', 'account_holder_name', 'ifsc_code', 'is_active', 'sort_order')
    list_filter = ('is_active',)
    search_fields = ('title', 'bank_name', 'account_number', 'ifsc_code')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'created_at')


@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'city', 'is_default')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    inlines = [CartItemInline]


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'status', 'total', 'created_at')
    list_filter = ('status',)
    inlines = [OrderItemInline]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'order',
        'method',
        'provider',
        'status',
        'amount_paise',
        'bank_reference',
        'created_at',
    )
    list_filter = ('method', 'status', 'provider')
    search_fields = ('order__id', 'razorpay_order_id', 'bank_reference')
    readonly_fields = ('created_at', 'updated_at', 'raw_response')
    actions = ['confirm_bank_transfer']

    @admin.action(description=_('Confirm bank transfer — mark paid & fulfill order'))
    def confirm_bank_transfer(self, request, queryset):
        confirmed = 0
        for pay in queryset.select_related('order', 'order__user'):
            if pay.method != Payment.Method.BANK_TRANSFER:
                continue
            if pay.status != Payment.Status.PENDING_VERIFICATION:
                continue
            order = pay.order
            user = order.user
            with transaction.atomic():
                ok = finalize_order_after_payment(order, user)
            if ok:
                send_order_confirmation(order)
                confirmed += 1
        self.message_user(
            request,
            _('Confirmed %(count)s bank transfer(s).') % {'count': confirmed},
        )
