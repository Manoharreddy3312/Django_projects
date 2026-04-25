from django.db import models

class Patient(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    profile_pic = models.ImageField(upload_to='patients/', null=True, blank=True)

    def __str__(self):
        return self.full_name

class Doctor(models.Model):
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    specialization = models.CharField(max_length=100)
    experience_years = models.IntegerField()
    availability_status = models.BooleanField(default=True)
    profile_pic = models.ImageField(upload_to='doctors/', null=True, blank=True)

    def __str__(self):
        return self.full_name

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    ]
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='appointments')
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    reason = models.TextField()
    prescription = models.TextField(blank=True, null=True)
    reminder_sent = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.patient} - {self.doctor} ({self.appointment_date})"