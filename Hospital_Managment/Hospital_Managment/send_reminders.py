from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from twilio.rest import Client
from Hospital_Managment.models import Appointment

class Command(BaseCommand):
    help = 'Sends WhatsApp reminders to patients 1 day before their appointment'

    def handle(self, *args, **kwargs):
        # Calculate date for tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        
        # Filter appointments for tomorrow that haven't received a reminder yet
        appointments = Appointment.objects.filter(
            appointment_date=tomorrow,
            reminder_sent=False
        ).exclude(status__in=['Cancelled', 'Completed'])

        if not appointments.exists():
            self.stdout.write("No appointments tomorrow requiring reminders.")
            return

        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

        for appointment in appointments:
            try:
                body = (
                    f"Hello {appointment.patient.full_name}, this is a reminder for your "
                    f"appointment with Dr. {appointment.doctor.full_name} tomorrow "
                    f"at {appointment.appointment_time.strftime('%I:%M %p')}. "
                    f"Reason: {appointment.reason}"
                )

                client.messages.create(
                    from_=settings.TWILIO_WHATSAPP_NUMBER,
                    body=body,
                    to=f"whatsapp:{appointment.patient.phone}"
                )

                appointment.reminder_sent = True
                appointment.save()
                self.stdout.write(self.style.SUCCESS(f"Sent reminder to {appointment.patient.full_name}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Error sending to {appointment.patient.phone}: {e}"))