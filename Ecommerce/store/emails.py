from django.conf import settings
from django.core.mail import send_mail


def send_order_confirmation(order):
    lines = []
    for it in order.items.all():
        lines.append(f'- {it.product.name} x {it.quantity} @ {it.unit_price}')
    body = (
        f'Thank you for your order #{order.pk}.\n\n'
        f'Total: {order.total} INR\n\n'
        f'Items:\n' + '\n'.join(lines) + '\n\n'
        f'— FlipMart'
    )
    send_mail(
        f'Order #{order.pk} confirmed',
        body,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        fail_silently=True,
    )
