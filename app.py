from flask import Flask
from controllers.authentication.auth import auth_routes
from controllers.ocr.ocr import ocr_routes
from controllers.users.add_users import add_user_routes
from controllers.users.get_users import get_users_routes
from controllers.users.edit_users import edit_users_routes
from controllers.users.delete_users import delete_users_routes
from controllers.meters.meters_details import meter_details_routes
from controllers.meters.meters_readings import meter_readings_routes
from controllers.qrgenerator.qr_code import qr_generator_routes
from controllers.meterreports.watermeterreports import water_meter_readings_report_routes
from controllers.notification.user_notification import user_notification_routes
from controllers.notification.meter_notification import meter_notification_routes
from controllers.notification.util.fcm_token import fcm_token_routes
from controllers.notification.daily_readings import init_scheduler
from controllers.notification.app_notification.notification_reading import app_notification

def create_app():
    app = Flask(__name__)
    
    # Register all blueprints
    app.register_blueprint(auth_routes)
    app.register_blueprint(add_user_routes)
    app.register_blueprint(get_users_routes)
    app.register_blueprint(edit_users_routes)
    app.register_blueprint(delete_users_routes)
    app.register_blueprint(meter_details_routes)
    app.register_blueprint(meter_readings_routes)
    app.register_blueprint(ocr_routes)
    app.register_blueprint(qr_generator_routes)
    app.register_blueprint(water_meter_readings_report_routes)
    app.register_blueprint(user_notification_routes)
    app.register_blueprint(meter_notification_routes)
    app.register_blueprint(fcm_token_routes)
    app.register_blueprint(app_notification)
  
    init_scheduler(app)
    
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=True)
