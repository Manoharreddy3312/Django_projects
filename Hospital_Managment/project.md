PROJECT NAME :

 HOSPITAL MANAGEMENT SYSTEM WITH AUTOMATED NOTIFICATIONS
 ========================================================

## 1. ABSTRACT
The Hospital Management System (HMS) is a comprehensive software solution designed to streamline healthcare operations. This project implements a robust digital platform for managing patient records, doctor specializations, and appointment scheduling. A key innovation in this system is the integration of automated communication channels—specifically WhatsApp via Twilio API and Email via SMTP—to deliver real-time prescriptions and appointment reminders. By digitizing medical history and automating follow-ups, the system reduces administrative overhead and improves patient care quality.

---

## 2. INTRODUCTION
In the modern healthcare era, efficient data management is critical. Traditional manual methods of maintaining patient records often lead to data inconsistency and delayed communication. This project aims to bridge that gap by providing a web-based management portal.
- **Scope:** Covers patient registration, doctor availability tracking, and prescription management.
- **Objectives:** 
    - To provide a secure login for administrative staff.
    - To automate appointment reminders 24 hours in advance.
    - To deliver digital prescriptions instantly via WhatsApp and Email.

---

## 3. LITERATURE SURVEY
Traditional Hospital Management Systems focused primarily on local database storage. Recent trends show a shift toward "Patient-Centric" systems. Research into Telemedicine and automated notification systems (like Twilio integration) indicates a 30% reduction in "no-show" appointments. This project builds upon these findings by implementing a proactive notification engine.

---

## 4. SYSTEM ANALYSIS
### 4.1 EXISTING SYSTEM
- **Manual Records:** Dependent on paper files or simple spreadsheets.
- **No Reminders:** Patients often forget appointments, leading to idle resources.
- **Physical Prescriptions:** Hard copies are easily lost and difficult to track for medical history.
### 4.2 PROPOSED SYSTEM
- **Automated Logic:** Uses Django management commands to scan for upcoming visits.
- **Unified Communication:** Integrated WhatsApp and Email delivery.
- **Media Handling:** Supports profile images for doctors and patients for better identification.

---

## 5. SYSTEM REQUIREMENTS SPECIFICATION (SRS)
### 5.1 HARDWARE REQUIREMENTS
- **Processor:** Intel Core i3 or higher.
- **RAM:** 4GB minimum.
- **Storage:** 500MB of available space for SQLite database and media files.
### 5.2 SOFTWARE REQUIREMENTS
- **Operating System:** Windows 10/11.
- **Language:** Python 3.10+.
- **Framework:** Django 6.0.4, Django REST Framework.
- **Database:** SQLite3.
- **Third-Party APIs:** Twilio (WhatsApp), SMTP (Gmail).

---

## 6. FEASIBILITY STUDY
- **Technical Feasibility:** The use of Python and Django provides a high-level, secure, and scalable environment.
- **Operational Feasibility:** The UI is built with Bootstrap 5, making it intuitive for hospital staff with minimal training.
- **Economic Feasibility:** Uses open-source technologies and pay-as-you-go API models (Twilio).

---

## 7. TECHNOLOGIES
- **Django:** The core "Batteries Included" web framework.
- **SQLite3:** A serverless, zero-configuration database engine.
- **Twilio API:** For programmatic WhatsApp messaging.
- **Bootstrap 5:** For responsive and modern UI design.
- **Pillow:** For processing patient and doctor profile images.

---

## 8. SYSTEM DESIGN
### 8.1 Class Diagram
The system revolves around three core entities: **Patient**, **Doctor**, and **Appointment**.
### 8.2 Database Schema
- **Patient Table:** Stores demographics and profile images.
- **Doctor Table:** Stores specialization and availability status.
- **Appointment Table:** Links patients and doctors with date, time, and prescription status.

---

## 9. SYSTEM IMPLEMENTATION
### 9.1 Key Modules
1. **Authentication Module:** Secure login/logout using Django Auth.
2. **Appointment Module:** Functional views for booking and searching appointments.
3. **Notification Module:** A dedicated management command (`send_reminders.py`) and a background batch script (`send_whatsapp.bat`).
4. **API Module:** RESTful endpoints for mobile or external integration.

---

## 10. ALGORITHM
### 10.1 Appointment Reminder Algorithm
1. **Start:** Triggered daily by `send_whatsapp.bat`.
2. **Query:** Fetch all Appointments where `appointment_date == (current_date + 1 day)` AND `reminder_sent == False`.
3. **Loop:** For each appointment found:
    - Initialize Twilio Client.
    - Construct a message string with Patient Name, Doctor Name, and Time.
    - Call Twilio API to send to `whatsapp:patient_phone`.
    - If successful, set `reminder_sent = True`.
4. **Log:** Write execution results to `cron_log.txt`.
5. **End.**

---

## 11. SCREEN SHOTS
*(Note: In your final doc, insert images of the following views)*
1. **Login Page:** The entry point for staff.
2. **Dashboard:** Showing counts of Patients, Doctors, and Pending Appointments.
3. **Appointment List:** Featuring the search bar and "Add Prescription" buttons.
4. **Patient History:** Chronological view of all visits for a specific patient.
5. **Prescription Form:** Text area for entering medication details.
6. **WhatsApp Notification:** Screenshot of the message received on a mobile device.

---

## 12. TESTING
- **Unit Testing:** Verified that `PatientForm` and `AppointmentForm` validate data correctly.
- **Integration Testing:** Verified that saving a prescription triggers both the SMTP email and Twilio WhatsApp message.
- **Performance Testing:** Used `select_related` in `appointment_list` to ensure fast loading times with large datasets.

---

## 13. CONCLUSION
The developed Hospital Management System successfully automates the critical path of patient interaction. By integrating Twilio and SMTP, the system ensures that patients are always informed and have digital access to their prescriptions. This reduces the burden on hospital staff and significantly enhances the patient experience.

---

## 14. BIBLIOGRAPHY
1. Django Documentation: https://docs.djangoproject.com/
2. Twilio API Reference: https://www.twilio.com/docs/whatsapp
3. Python.org: Official Python Language Documentation.
4. Bootstrap 5: GetBootstrap.com.
```