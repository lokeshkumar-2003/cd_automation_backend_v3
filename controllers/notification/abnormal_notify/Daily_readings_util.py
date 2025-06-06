from datetime import datetime, date
from dbconfig import get_db_connection
from controllers.notification.util.Email_handler import send_email
from controllers.notification.Notification_handler import send_app_notification
import os
from dotenv import load_dotenv

load_dotenv()

def run_daily_meter_check():
    print(f"[{datetime.now()}] 🔄 Running daily meter check...")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 1: Fetch all meters
        cursor.execute("SELECT MeterName FROM Meters")
        all_meters = {row[0] for row in cursor.fetchall()}
        total_meters = len(all_meters)

        # Step 2: Fetch meters with readings today
        today = date.today()
        cursor.execute("SELECT DISTINCT MeterName FROM MeterReadings WHERE ReadingDate = %s", (today,))
        meters_with_readings = {row[0] for row in cursor.fetchall()}

        # Step 3: Calculate missing meters
        missing_meters = all_meters - meters_with_readings
        missing_count = len(missing_meters)

        # Step 4: Fetch admin users
        cursor.execute("SELECT Username, EmailId, emailPassword, fcm_token FROM admin_users")
        admins = cursor.fetchall()

        now = datetime.now()
        current_date = now.strftime("%d-%m-%Y")
        sender = None  # Could be system account or script trigger

        if missing_meters:
            meter_list_str = "\n".join(f"- {m}" for m in sorted(missing_meters))
            title = f"⚠️ Missed Meter Reading Alert – {current_date}"
            message = (
                f"The following meter readings were not received on {current_date}:\n\n"
                f"{meter_list_str}\n\nPlease follow up to ensure data integrity."
            )
            db_message = f"{missing_count} meter(s) have missing readings on {current_date}."

            # Step 5: Insert into Notifications table
            cursor.execute("""
                INSERT INTO Notifications (Title, Message, CreatedBy, CreatedAt, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, db_message, "AutoScript", now, "Warning"))
            conn.commit()

            notification_id = cursor.lastrowid

            # Notify all admins
            for username, email, password, fcm_token in admins:
                # Insert unread status
                cursor.execute("""
                    INSERT INTO NotificationReadStatus (NotificationID, AdminUsername, IsRead)
                    VALUES (%s, %s, %s)
                """, (notification_id, username, 0))

                # Send Email
                if email and password:
                    try:
                        send_email(
                            sender_email=email,  # Assuming each admin uses their own mail — otherwise use common sender
                            sender_password=password,
                            recipient_email=email,
                            subject=title,
                            body=message
                        )
                    except Exception as e:
                        print(f"📧 Failed to send email to {email}: {e}")

                # Send App Notification
                if fcm_token:
                    try:
                        send_app_notification(
                            device_token=fcm_token,
                            title=title,
                            message=db_message
                        )
                    except Exception as e:
                        print(f"📲 Failed to send app notification to {username}: {e}")

            conn.commit()
            print(f"❌ {missing_count} meter(s) missing. Notifications sent.")

        else:
            title = f"✅ All Meter Readings Submitted – {current_date}"
            db_message = f"All {total_meters} meters submitted readings on {current_date}."
            message = (
                f"All meter readings have been successfully submitted on {current_date}.\n"
                f"Total meters: {total_meters}"
            )

            # Insert success notification
            cursor.execute("""
                INSERT INTO Notifications (Title, Message, CreatedBy, CreatedAt, Status)
                VALUES (%s, %s, %s, %s, %s)
            """, (title, db_message, "AutoScript", now, "Success"))
            conn.commit()

            notification_id = cursor.lastrowid

            for username, email, password, fcm_token in admins:
                cursor.execute("""
                    INSERT INTO NotificationReadStatus (NotificationID, AdminUsername, IsRead)
                    VALUES (%s, %s, %s)
                """, (notification_id, username, 0))

                # Send Email
                if email and password:
                    try:
                        send_email(
                            sender_email=email,
                            sender_password=password,
                            recipient_email=email,
                            subject=title,
                            body=message
                        )
                    except Exception as e:
                        print(f"📧 Failed to send email to {email}: {e}")

                if fcm_token:
                    try:
                        send_app_notification(
                            device_token=fcm_token,
                            title=title,
                            message=db_message
                        )
                    except Exception as e:
                        print(f"📲 Failed to send app notification to {username}: {e}")

            conn.commit()
            print(f"✅ All meter readings submitted. Success notification sent.")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Exception occurred during meter check: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
        print(f"[{datetime.now()}] 🔚 Daily meter check process completed.")
