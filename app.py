import os
import random
import sqlite3
from flask import Flask, render_template, request, jsonify

app = Flask(__name__, template_folder="templates", static_folder="static")

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'fighters.db')

# Hero fighters for homepage
hero_fighters = [
    {
        "name": "Tom Aspinall",
        "image": "images/TOM_ASPINALL.jpg",
        "record": "14-3",
        "weight_class": "Heavyweight"
    },
    {
        "name": "Ciryl Gane",
        "image": "images/CIRYL_GANE.jpg",
        "record": "12-2",
        "weight_class": "Heavyweight"
    }
]

# Upcoming fight card
upcoming_ufc_fights = [
    {
        "fighter_a": "???",
        "fighter_b": "???",
        "record_a": "TBD",
        "record_b": "TBD",
        "weight_class": "TBD",
        "title_fight": False,
        "event_name": "White House Card: TBD",
        "event_date": "November 11, 2025",
        "location": "Undisclosed Location, Washington D.C.",
        "image_a": "images/placeholder.jpg",
        "image_b": "images/placeholder.jpg",
        "note": "Presidential Fight Night Preview"
    }
]

# Routes
@app.route('/')
def index():
    return render_template('index.html', hero_fighters=hero_fighters)

@app.route('/whitehouse-arena')
def whitehouse_arena():
    return render_template('whitehouse_arena.html')

@app.route('/predict', methods=['GET', 'POST'])
def prediction_page():
    if request.method == 'POST':
        data = request.get_json()
        fighter1 = data.get("fighter1")
        fighter2 = data.get("fighter2")

        prediction = {
            fighter1: round(random.uniform(40, 60), 2),
            fighter2: round(100 - random.uniform(40, 60), 2)
        }

        fighter1_data = get_fighter_data(fighter1)
        fighter2_data = get_fighter_data(fighter2)

        return jsonify({
            fighter1: fighter1_data | {"win_rate": prediction[fighter1]},
            fighter2: fighter2_data | {"win_rate": prediction[fighter2]}
        })

    return render_template('prediction.html', hero_fighters=hero_fighters)

@app.route('/upcoming')
def upcoming_page():
    fight = upcoming_ufc_fights[0]
    return render_template(
        'upcoming.html',
        event_name=fight["event_name"],
        event_date=fight["event_date"],
        event_location=fight["location"],
        main_card_fights=upcoming_ufc_fights
    )

@app.route('/fighters')
def fighters_page():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, image_url, record, weight_class FROM fighters")
    fighters = cursor.fetchall()
    conn.close()
    return render_template('fighters.html', fighters=fighters)

# Helper function to simulate fighter data
def get_fighter_data(name):
    return {
        "name": name,
        "image": "images/placeholder.jpg",
        "record": f"{random.randint(10, 30)}-{random.randint(0, 5)}-{random.randint(0, 2)}",
        "weight_class": random.choice([
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ])
    }

# Run the app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
