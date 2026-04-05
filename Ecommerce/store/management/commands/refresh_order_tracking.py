from django.core.management.base import BaseCommand

from store.models import Order
from store.tracking import refresh_order_tracking


class Command(BaseCommand):
    help = 'Advance order tracking stages and send status emails (run via cron every hour).'

    def handle(self, *args, **options):
        qs = Order.objects.exclude(
            status__in=[
                Order.Status.PENDING_PAYMENT,
                Order.Status.FAILED,
                Order.Status.CANCELLED,
            ]
        )
        n = 0
        for order in qs.iterator():
            refresh_order_tracking(order, send_mail_flag=True)
            n += 1
        self.stdout.write(self.style.SUCCESS(f'Processed {n} orders.'))
