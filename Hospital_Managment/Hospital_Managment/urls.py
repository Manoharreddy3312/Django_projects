from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'patients', views.PatientViewSet, basename='api-patient')
router.register(r'doctors', views.DoctorViewSet, basename='api-doctor')
router.register(r'appointments', views.AppointmentViewSet, basename='api-appointment')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('patient/add/', views.add_patient, name='add_patient'),
    path('appointment/book/', views.book_appointment, name='book_appointment'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/prescribe/', views.add_prescription, name='add_prescription'),
    path('patient/<int:pk>/history/', views.patient_history, name='patient_history'),
    path('reports/', views.reports, name='reports'),
    path('doctor/<int:pk>/update-status/', views.update_doctor_status, name='update_doctor_status'),
    # API URLs
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)