@echo off
cd /d D:\Msc_project\Hospital_Managment
call D:\Msc_project\msc\Scripts\activate
echo [%DATE% %TIME%] Starting automated WhatsApp reminders... >> cron_log.txt
python manage.py send_reminders >> cron_log.txt 2>&1
echo --------------------------------------------------------- >> cron_log.txt
