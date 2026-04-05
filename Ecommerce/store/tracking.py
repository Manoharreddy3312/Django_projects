from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import Order


def _hours_since(dt):
    if not dt:
        return 0
    return (timezone.now() - dt).total_seconds() / 3600.0


def compute_tracking_display(order):
    if order.status in (Order.Status.PENDING_PAYMENT, Order.Status.FAILED, Order.Status.CANCELLED):
        return {'progress': 0, 'label': order.get_status_display(), 'phase': 0}
    start = order.confirmed_at or order.created_at
    h = _hours_since(start)
    if h < 24:
        return {'progress': 50, 'label': 'Order Placed', 'phase': 1}
    if h < 48:
        return {'progress': 75, 'label': 'Order Shipping', 'phase': 2}
    if h < 72:
        return {'progress': 100, 'label': 'Order Dispatched', 'phase': 3}
    return {'progress': 100, 'label': 'Delivered', 'phase': 4}


def send_tracking_email(order, subject, body):
    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [order.user.email],
        fail_silently=True,
    )


def _status_for_phase(phase):
    if phase <= 1:
        return Order.Status.PLACED
    if phase == 2:
        return Order.Status.SHIPPING
    if phase == 3:
        return Order.Status.DISPATCHED
    return Order.Status.DELIVERED


def refresh_order_tracking(order, send_mail_flag=True):
    if order.status in (
        Order.Status.PENDING_PAYMENT,
        Order.Status.FAILED,
        Order.Status.CANCELLED,
    ):
        return order
    if order.status == Order.Status.DELIVERED and order.tracking_email_phase >= 4:
        return order

    disp = compute_tracking_display(order)
    target_phase = disp['phase']
    old_phase = order.tracking_email_phase
    new_status = _status_for_phase(target_phase)

    updates = []
    if new_status and order.status != new_status:
        order.status = new_status
        updates.append('status')
    if target_phase > order.tracking_email_phase:
        order.tracking_email_phase = target_phase
        updates.append('tracking_email_phase')
    if updates:
        order.save(update_fields=updates)

    if send_mail_flag and target_phase > old_phase and old_phase > 0:
        subj = f'Order #{order.pk} update: {disp["label"]}'
        body = (
            f'Hi,\n\nYour order #{order.pk} status: {disp["label"]}.\n'
            f'View details in your account.\n\n— FlipMart'
        )
        send_tracking_email(order, subj, body)

    return order
