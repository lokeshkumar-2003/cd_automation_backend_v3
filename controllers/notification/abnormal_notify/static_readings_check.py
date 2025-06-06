from datetime import date, timedelta, datetime
from dbconfig import get_db_connection
from controllers.notification.util.Email_handler import send_email
from controllers.notification.Notification_handler import send_app_notification
import os

def detect_static_readings():
    print(f"[{datetime.now()}] 🛑 Checking for continuous static water meter readings...")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Constants
        STATIC_DAYS = 3
        LOOKBACK_DAYS = 4
        STATUS = "Warning"
        CREATED_BY = "System"

        # Get data
        cursor.execute("SELECT DISTINCT MeterName FROM MeterReadings")
        meters = [row[0] for row in cursor.fetchall()]

        cursor.execute("SELECT Username, EmailId, fcm_token FROM admin_users")
        admins = cursor.fetchall()

        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")

        today = date.today()
        start_date = today - timedelta(days=LOOKBACK_DAYS)

        for meter in meters:
            cursor.execute("""
                SELECT ReadingDate, Consumption 
                FROM MeterReadings 
                WHERE MeterName = %s AND ReadingDate >= %s 
                ORDER BY ReadingDate DESC
            """, (meter, start_date))

            readings = cursor.fetchall()

            if len(readings) < STATIC_DAYS:
                print(f"[{datetime.now()}] ℹ️ Skipped meter '{meter}': not enough recent data.")
                continue

            last_consumptions = [row[1] for row in readings[:STATIC_DAYS]]

            if all(c == last_consumptions[0] for c in last_consumptions):
                concise_title = "Static Reading Alert"
                full_title = f"🛑 Static Reading Alert – {meter}"
                full_message = (
                    f"The water consumption for meter '{meter}' has remained unchanged for "
                    f"the last {STATIC_DAYS} days.\n\n"
                    "This may indicate a faulty meter, a connection issue, or genuinely zero usage. "
                    "Please inspect the device at the earliest."
                )
                app_message = f"Meter '{meter}' has static readings. Please check."

                # Insert into Notifications
                cursor.execute("""
                    INSERT INTO Notifications (Title, Message, AppMessage, CreatedBy, Status)
                    VALUES (%s, %s, %s, %s, %s)
                """, (concise_title, full_message, app_message, CREATED_BY, STATUS))
                conn.commit()

                notification_id = cursor.lastrowid

                # Insert read status for all admins
                for username, _, _ in admins:
                    cursor.execute("""
                        INSERT INTO NotificationReadStatus (NotificationID, AdminUsername, IsRead)
                        VALUES (%s, %s, 0)
                    """, (notification_id, username))
                conn.commit()

                # Send notifications
                for username, admin_email, fcm_token in admins:
                    try:
                        send_email(sender_email, sender_password, admin_email, full_title, full_message)
                    except Exception as e:
                        print(f"❌ Failed to send email to {admin_email}: {e}")

                    if fcm_token:
                        try:
                            send_app_notification(fcm_token, concise_title, app_message)
                        except Exception as e:
                            print(f"❌ Failed to send app notification to {username}: {e}")

                print(f"[{datetime.now()}] ⚠️ Static reading alert sent for meter: {meter}")

        print(f"[{datetime.now()}] ✅ Static reading check completed.")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error in static reading detection: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
