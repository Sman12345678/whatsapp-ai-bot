import os
import logging
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-here")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL")
if not database_url or database_url == "":
    database_url = "sqlite:///whatsapp_bot.db"
app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Store bot start time for uptime calculation
app.config['BOT_START_TIME'] = datetime.now()

with app.app_context():
    # Import models and analytics
    import models
    import analytics
    
    # Create all database tables
    db.create_all()
    logger.info("Database tables created successfully")
    
    # Import bot after database is set up
    try:
        from bot import wa  # Import WhatsApp bot instance
        if wa:
            logger.info("WhatsApp bot imported and ready")
        else:
            logger.info("WhatsApp bot running in demo mode")
    except Exception as e:
        logger.warning(f"Error importing WhatsApp bot: {e}")

# Routes
@app.route('/')
def dashboard():
    """Admin dashboard route"""
    try:
        from analytics import get_dashboard_stats
        stats = get_dashboard_stats()
        return render_template('dashboard.html', stats=stats)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render_template('dashboard.html', stats={
            'total_users': 0,
            'total_messages': 0,
            'uptime': '0:00:00',
            'active_groups': 0,
            'commands_used': 0,
            'ai_requests': 0,
            'files_processed': 0
        })

@app.route('/api/stats')
def api_stats():
    """API endpoint for real-time stats"""
    try:
        from analytics import get_dashboard_stats
        stats = get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"API stats error: {e}")
        return jsonify({'error': 'Failed to fetch stats'}), 500

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    """WhatsApp webhook endpoint - handled by PyWa"""
    return '', 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
