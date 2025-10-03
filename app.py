import os
import random
import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__, template_folder="templates", static_folder="static")

# Database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'fighters.db')

# Hero Headliner for AI Showcase
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

# White House Card: TBD
upcoming_ufc_fights = [
    {
        "fighter_a": "???",
        "fighter_b": "???",
        "record_a": "TBD",
        "record_b": "TBD",
        "weight_class": "TBD",
        "title_fight": False,
        "event_name": "White House Card: TBD",
        "event_date": datetime(2025, 11, 11, 20, 0, 0),
        "location": "Undisclosed Location, Washington D.C.",
        "image_a": "images/placeholder.jpg",
        "image_b": "images/placeholder.jpg",
        "note": "Presidential Fight Night Preview"
    }
]

# Seed fighter database
def seed_fighters():
    sample_fighters = [
        ("Tom Aspinall", "images/TOM_ASPINALL.jpg", "14-3", "Heavyweight"),
        ("Ciryl Gane", "images/CIRYL_GANE.jpg", "12-2", "Heavyweight"),
        ("Jan Blachowicz", "images/JAN_BLACHOWICZ.jpg", "29-10-1", "Light Heavyweight"),
        ("Nikita Krylov", "images/NIKITA_KRYLOV.jpg", "30-9", "Light Heavyweight"),
        ("Sergei Spivak", "images/SERGEI_SPIVAK.jpg", "17-4", "Heavyweight"),
        ("Tai Tuivasa", "images/TAI_TUIVASA.jpg", "15-6", "Heavyweight"),
        ("Curtis Blaydes", "images/CURTIS_BLAYDES.jpg", "18-4 (1 NC)", "Heavyweight"),
        ("Jailton Almeida", "images/JAILTON_ALMEIDA.jpg", "21-3", "Heavyweight"),
        ("Derrick Lewis", "images/DERRICK_LEWIS.jpg", "28-12-0 (1 NC)", "Heavyweight")
    ]

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fighters (
            name TEXT PRIMARY KEY,
            image_url TEXT,
            record TEXT,
            weight_class TEXT
        )
    ''')

    for fighter in sample_fighters:
        cursor.execute("INSERT OR IGNORE INTO fighters VALUES (?, ?, ?, ?)", fighter)

    conn.commit()
    conn.close()

# Routes
@app.route('/')
def index():
    return render_template('index.html', hero_fighters=hero_fighters)

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

        fighter1_data = get_or_create_fighter(fighter1)
        fighter2_data = get_or_create_fighter(fighter2)

        return jsonify({
            fighter1: {
                "win_rate": prediction[fighter1],
                "image": fighter1_data["image"],
                "record": fighter1_data["record"],
                "weight_class": fighter1_data["weight_class"]
            },
            fighter2: {
                "win_rate": prediction[fighter2],
                "image": fighter2_data["image"],
                "record": fighter2_data["record"],
                "weight_class": fighter2_data["weight_class"]
            }
        })

    return render_template('prediction.html', hero_fighters=hero_fighters)

@app.route('/upcoming')
def upcoming_page():
    fight = upcoming_ufc_fights[0]
    return render_template(
        'upcoming.html',
        event_name=fight["event_name"],
        event_date=fight["event_date"].strftime("%B %d, %Y"),
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

# Fighter data helpers
def get_or_create_fighter(name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM fighters WHERE name = ?", (name,))
    row = cursor.fetchone()

    if row:
        fighter = {
            "name": row[0],
            "image": row[1],
            "record": row[2],
            "weight_class": row[3]
        }
    else:
        stats = get_fighter_stats(name)
        image = get_fighter_image(name)
        cursor.execute("INSERT INTO fighters VALUES (?, ?, ?, ?)", (
            name, image, stats["record"], stats["weight_class"]
        ))
        conn.commit()
        fighter = {
            "name": name,
            "image": image,
            "record": stats["record"],
            "weight_class": stats["weight_class"]
        }

    conn.close()
    return fighter

def get_fighter_stats(name):
    return {
        "record": f"{random.randint(10, 30)}-{random.randint(0, 5)}-{random.randint(0, 2)}",
        "weight_class": random.choice([
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ])
    }

def get_fighter_image(name):
    formatted_name = name.lower().replace(" ", "-")
    ufc_url = f"https://www.ufc.com/athlete/{formatted_name}"

    try:
        response = requests.get(ufc_url, timeout=3)
        soup = BeautifulSoup(response.text, 'html.parser')
        image_tag = soup.find('img', class_='hero-profile__image')
        if image_tag and image_tag.get('src'):
            return image_tag['src']
    except requests.exceptions.RequestException:
        pass

    return "images/placeholder.jpg"

# Run the app
if __name__ == "__main__":
    seed_fighters()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
