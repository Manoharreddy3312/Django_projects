"""Shared logic after a payment is confirmed (Razorpay or bank transfer)."""
from django.utils import timezone

from .emails import send_order_confirmation
from .models import Cart, Order, Payment


def finalize_order_after_payment(order: Order, user) -> bool:
    """
    Set order placed, payment success, decrement stock, clear cart.
    Idempotent: returns False if order was already placed.
    Caller should send confirmation email when True (after commit).
    Must be called inside transaction.atomic().
    """
    order = Order.objects.select_for_update().get(pk=order.pk)
    if order.status == Order.Status.PLACED:
        return False
    pay = Payment.objects.select_for_update().get(order_id=order.pk)
    pay.status = Payment.Status.SUCCESS
    pay.save(update_fields=['status', 'updated_at'])
    order.status = Order.Status.PLACED
    order.confirmed_at = timezone.now()
    order.tracking_email_phase = 1
    order.save(update_fields=['status', 'confirmed_at', 'tracking_email_phase'])
    try:
        cart = Cart.objects.select_for_update().get(user=user)
    except Cart.DoesNotExist:
        cart = None
    if cart:
        for ci in cart.items.select_related('product'):
            p = ci.product
            p.stock = max(0, p.stock - ci.quantity)
            p.save(update_fields=['stock'])
        cart.items.all().delete()
    return True
