from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from twilio.rest import Client
from rest_framework import viewsets
from .models import Patient, Doctor, Appointment
from .forms import PatientForm, AppointmentForm
from .serializers import PatientSerializer, DoctorSerializer, AppointmentSerializer
from datetime import date
from django.db.models import Count, Q

@login_required
def dashboard(request):
    patient_count = Patient.objects.count()
    doctor_count = Doctor.objects.count()
    pending_appointments = Appointment.objects.filter(status='Pending').count()
    return render(request, 'dashboard.html', {
        'patient_count': patient_count,
        'doctor_count': doctor_count,
        'pending_appointments': pending_appointments
    })

@login_required
def add_patient(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Patient added successfully!")
            return redirect('dashboard')
    else:
        form = PatientForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Add New Patient'})

@login_required
def book_appointment(request):
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment booked successfully!")
            return redirect('appointment_list')
    else:
        form = AppointmentForm()
    return render(request, 'form_template.html', {'form': form, 'title': 'Book Appointment'})

@login_required
def appointment_list(request):
    query = request.GET.get('q')
    # Performance optimization: Fetch patient and doctor in the same query
    appointments = Appointment.objects.select_related('patient', 'doctor').all()
    
    if query:
        appointments = appointments.filter(
            Q(patient__full_name__icontains=query) | 
            Q(doctor__full_name__icontains=query)
        )
        
    appointments = appointments.order_by('-appointment_date', '-appointment_time')
    return render(request, 'appointment_list.html', {'appointments': appointments, 'query': query})

@login_required
def add_prescription(request, pk):
    appointment = get_object_or_404(Appointment, pk=pk)
    if request.method == 'POST':
        appointment.prescription = request.POST.get('prescription')
        appointment.status = 'Completed'
        appointment.save()

        subject = f"Prescription from Dr. {appointment.doctor.full_name}"
        message_body = (
            f"Hello {appointment.patient.full_name},\n\n"
            f"Your consultation is complete.\n"
            f"Prescription:\n{appointment.prescription}\n\n"
            f"Get well soon!"
        )

        # 1. Send via Email
        if appointment.patient.email:
            try:
                send_mail(subject, message_body, settings.EMAIL_HOST_USER, [appointment.patient.email])
                messages.success(request, "Prescription sent via Email.")
            except Exception as e:
                messages.error(request, f"Email failed: {str(e)}")

        # 2. Send via WhatsApp
        try:
            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            client.messages.create(
                from_=settings.TWILIO_WHATSAPP_NUMBER,
                body=message_body,
                to=f"whatsapp:{appointment.patient.phone}"
            )
            messages.success(request, "Prescription sent via WhatsApp.")
        except Exception as e:
            messages.warning(request, f"WhatsApp failed: {str(e)}")

        return redirect('appointment_list')
    return render(request, 'add_prescription.html', {'appointment': appointment})

@login_required
def patient_history(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    history = Appointment.objects.filter(patient=patient).order_by('-appointment_date')
    return render(request, 'patient_history.html', {'patient': patient, 'history': history})

@login_required
def reports(request):
    today = date.today()
    daily_appointments = Appointment.objects.filter(appointment_date=today)
    doctor_stats = Doctor.objects.annotate(appointment_count=Count('appointments'))
    return render(request, 'reports.html', {
        'daily_appointments': daily_appointments,
        'doctor_stats': doctor_stats
    })

@login_required
def update_doctor_status(request, pk):
    doctor = get_object_or_404(Doctor, pk=pk)
    doctor.availability_status = not doctor.availability_status
    doctor.save()
    return redirect('dashboard')

# --- API ViewSets ---

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer