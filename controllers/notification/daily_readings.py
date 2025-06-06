from flask_apscheduler import APScheduler
from controllers.notification.abnormal_notify.Daily_readings_util import run_daily_meter_check
scheduler = APScheduler()

def init_scheduler(app):
    app.config['SCHEDULER_API_ENABLED'] = True
    scheduler.init_app(app)

    if not scheduler.running:
        scheduler.start()

    @scheduler.task('cron', id='daily_meter_check', hour=10, minute=10)
    def daily_meter_check():
        run_daily_meter_check()
