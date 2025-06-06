from datetime import date, timedelta, datetime
from dbconfig import get_db_connection
from controllers.notification.util.Email_handler import send_email
from controllers.notification.Notification_handler import send_app_notification
import os

def detect_abnormal_variation():
    print(f"[{datetime.now()}] 📊 Checking for abnormal water consumption variation...")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Configuration
        VARIATION_THRESHOLD = 5  # percentage
        DAYS_BACK = 6
        MIN_REQUIRED_READINGS = 4

        # Step 1: Get meter list
        cursor.execute("SELECT DISTINCT MeterName FROM WaterMeterReadings")
        meters = [row[0] for row in cursor.fetchall()]

        # Step 2: Get admin details
        cursor.execute("SELECT Username, EmailId, fcm_token FROM admin_users")
        admins = cursor.fetchall()

        sender_email = os.getenv("SENDER_EMAIL")
        sender_password = os.getenv("SENDER_PASSWORD")

        today = date.today()
        start_date = today - timedelta(days=DAYS_BACK)

        # Step 3: Process each meter
        for meter in meters:
            cursor.execute("""
                SELECT ReadingDate, Consumption 
                FROM MeterReadings 
                WHERE MeterName = %s AND ReadingDate >= %s 
                ORDER BY ReadingDate ASC
            """, (meter, start_date))
            
            readings = cursor.fetchall()
            if len(readings) < MIN_REQUIRED_READINGS:
                print(f"[{datetime.now()}] ℹ️ Skipped meter '{meter}': not enough data.")
                continue

            consumptions = [row[1] for row in readings]
            variations = []

            for i in range(1, len(consumptions)):
                prev = consumptions[i - 1]
                curr = consumptions[i]
                if prev == 0:
                    continue  # avoid division by zero
                change = abs((curr - prev) / prev) * 100
                variations.append(change)

            # Step 4: Check if last 3 changes are above threshold
            if len(variations) >= 3 and all(v > VARIATION_THRESHOLD for v in variations[-3:]):
                subject = f"⚠️ Alert: Abnormal Water Usage – {meter}"
                email_body = (
                    f"Meter '{meter}' has shown over {VARIATION_THRESHOLD}% change in water consumption "
                    f"for the past 3 days.\n\n"
                    "Please inspect the site for leaks or misuse."
                )
                app_message = f"⚠️ Abnormal variation in meter '{meter}' – check site."

                for username, admin_email, fcm_token in admins:
                    try:
                        send_email(sender_email, sender_password, admin_email, subject, email_body)
                    except Exception as e:
                        print(f"❌ Failed to email {admin_email}: {e}")

                    if fcm_token:
                        try:
                            send_app_notification(fcm_token, subject, app_message)
                        except Exception as e:
                            print(f"❌ Failed app notification to {username}: {e}")

                print(f"[{datetime.now()}] ⚠️ Notification sent for meter: {meter}")

        print(f"[{datetime.now()}] ✅ Abnormal variation check complete.")

    except Exception as e:
        print(f"[{datetime.now()}] ❌ Error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
