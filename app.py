from flask import Flask, render_template, request, jsonify, send_from_directory
from get_time import get_show_info
import json
import os
import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from pywebpush import webpush, WebPushException
import threading

app = Flask(__name__)

# Ensure directories exist
os.makedirs('static/icons', exist_ok=True)

# Store subscriptions
SUBSCRIPTION_FILE = 'subscriptions.json'
VAPID_PRIVATE_KEY = os.getenv('VAPID_PRIVATE_KEY')
VAPID_PUBLIC_KEY = os.getenv('VAPID_PUBLIC_KEY')
VAPID_CLAIMS = {
    'sub': os.getenv('VAPID_SUB', 'mailto:your-email@example.com')
}


def load_subscriptions():
    try:
        with open(SUBSCRIPTION_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_subscriptions(subscriptions):
    with open(SUBSCRIPTION_FILE, 'w') as f:
        json.dump(subscriptions, f)


def check_upcoming_episodes():
    subscriptions = load_subscriptions()

    for user_id, data in subscriptions.items():
        subscription_info = data.get('subscription')
        shows = data.get('shows', [])

        for show in shows:
            show_info = get_show_info(show)
            if show_info['next_episode']:
                try:
                    air_time = datetime.datetime.fromisoformat(show_info['next_episode'])
                    now = datetime.datetime.now(datetime.timezone.utc)

                    # Check if episode is within the next hour
                    time_diff = air_time - now
                    if datetime.timedelta(minutes=55) <= time_diff <= datetime.timedelta(minutes=65):
                        send_notification(subscription_info, show, air_time)
                except (ValueError, TypeError):
                    continue


def send_notification(subscription, show_name, air_time):
    try:
        local_time = air_time.strftime("%I:%M %p")
        payload = json.dumps({
            "title": f"{show_name} starts soon!",
            "body": f"Your show begins at {local_time}. Don't miss it!",
            "url": "/"
        })

        webpush(
            subscription_info=subscription,
            data=payload,
            vapid_private_key=VAPID_PRIVATE_KEY,
            vapid_claims=VAPID_CLAIMS
        )
    except WebPushException as e:
        print(f"Push notification failed: {e}")


@app.route('/')
def index():
    shows_to_display = []
    for title in ["Severance", "Invincible","Georgie and Mandy's First Marriage"]:
        shows_to_display.append(get_show_info(title))

    return render_template('index.html', featured_shows=shows_to_display)


@app.route('/manifest.json')
def manifest():
    return send_from_directory('static', 'manifest.json')


@app.route('/sw.js')
def service_worker():
    return app.send_static_file('sw.js')


@app.route('/api/save-subscription', methods=['POST'])
def save_subscription():
    data = request.json
    subscription_info = data.get('subscription')
    shows = data.get('shows', [])

    if not subscription_info:
        return jsonify({'error': 'No subscription information provided'}), 400

    subscriptions = load_subscriptions()
    subscription_id = str(hash(json.dumps(subscription_info)))

    subscriptions[subscription_id] = {
        'subscription': subscription_info,
        'shows': shows
    }

    save_subscriptions(subscriptions)
    return jsonify({'success': True}), 201


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_upcoming_episodes, 'interval', minutes=5)
    scheduler.start()

    # Avoid the scheduler being garbage collected
    return scheduler


@app.route('/test-notification')
def test_notification():
    subscriptions = load_subscriptions()
    now = datetime.datetime.now(datetime.timezone.utc)
    future = now + datetime.timedelta(minutes=60)

    for user_id, data in subscriptions.items():
        send_notification(data['subscription'], "Test Show", future)

    return jsonify({"message": "Test notification sent"})
if __name__ == '__main__':
    # Setup static files
    if not os.path.exists('static/manifest.json'):
        with open('static/manifest.json', 'w') as f:
            json.dump({
                "name": "Horologe - TV Show Tracker",
                "short_name": "Horologe",
                "description": "Track your favorite TV shows and never miss an episode",
                "start_url": "/",
                "display": "standalone",
                "background_color": "#2a303c",
                "theme_color": "#570df8",
                "icons": [
                    {
                        "src": "/static/icons/icon-192x192.png",
                        "sizes": "192x192",
                        "type": "image/png"
                    },
                    {
                        "src": "/static/icons/icon-512x512.png",
                        "sizes": "512x512",
                        "type": "image/png"
                    }
                ]
            }, f)

    if not os.path.exists('static/sw.js'):
        with open('static/sw.js', 'w') as f:
            f.write(open('sw.js', 'r').read())

    scheduler = start_scheduler()
    app.run(debug=True, use_reloader=False)