import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file
import random
import os
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader
import qrcode
import io

# ✅ Initialize Flask app FIRST
app = Flask(__name__, template_folder="templates", static_folder="static")

# ✅ Now define your routes
@app.route('/download-bet-slip')
def download_bet_slip():
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 50, "🧾 UFC 317 Bet Slip – Method of Victory Parlay")

    c.setFont("Helvetica", 12)
    c.drawString(72, height - 90, "Prepared for: Bentley")
    c.drawString(72, height - 110, "Event: UFC 317")
    c.drawString(72, height - 130, "Date: July 28, 2025")
    c.drawString(72, height - 150, "Location: T-Mobile Arena, Las Vegas, NV")
    c.drawString(72, height - 170, "Wager Type: 3-Leg Parlay")
    c.drawString(72, height - 190, "Stake: $100")
    c.drawString(72, height - 210, "Estimated Payout: $1,460")

    c.setFont("Helvetica-Bold", 14)
    c.drawString(72, height - 240, "🎯 Primary Parlay – Method of Victory")

    c.setFont("Helvetica", 11)
    fights = [
        ("Ilia Topuria vs. Charles Oliveira", "Ilia Topuria", "Win by KO/TKO", "-160 (1.63)"),
        ("Alexandre Pantoja vs. Kai Kara-France", "Alexandre Pantoja", "Win by Submission", "+220 (3.20)"),
        ("Brandon Royval vs. Joshua Van", "Brandon Royval", "Win by Submission", "+180 (2.80)")
    ]

    y = height - 265
    for fight, pick, method, odds in fights:
        c.drawString(80, y, f"{fight}")
        c.drawString(100, y - 15, f"Pick: {pick} | Method: {method} | Odds: {odds}")
        y -= 40

    c.drawString(80, y, "Total Parlay Odds: 14.6")
    c.drawString(80, y - 15, "Projected Return: $1,460")

    qr = qrcode.make("https://www.ufc.com/event/ufc-317")
    qr_buffer = io.BytesIO()
    qr.save(qr_buffer)
    qr_buffer.seek(0)
    qr_img = ImageReader(qr_buffer)
    c.drawImage(qr_img, width - 120, 60, width=60, height=60)

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="UFC_317_Bet_Slip.pdf", mimetype='application/pdf')

# Set up database path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_DIR = os.path.join(BASE_DIR, 'ai_prediction')
DB_PATH = os.path.join(DB_DIR, 'fighters.db')

if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/prediction')
def prediction_page():
    return render_template('prediction.html')

@app.route('/upcoming')
def upcoming_page():
    return render_template('upcoming.html')

@app.route('/analysis')
def analysis_page():
    return render_template(
        'analysis.html',
        topuria_is_champ=True,
        oliveira_is_champ=True
    )

@app.route('/fighters')
def fighters_page():
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
    cursor.execute("SELECT name, image_url, record, weight_class FROM fighters")
    fighters = cursor.fetchall()
    conn.close()
    return render_template('fighters.html', fighters=fighters)

@app.route('/predict', methods=['POST'])
def predict():
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

def get_or_create_fighter(name):
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

def get_fighter_stats(fighter_name):
    return {
        "record": f"{random.randint(10, 30)}-{random.randint(0, 5)}-{random.randint(0, 2)}",
        "weight_class": random.choice([
            "Flyweight", "Bantamweight", "Featherweight", "Lightweight",
            "Welterweight", "Middleweight", "Light Heavyweight", "Heavyweight"
        ])
    }

def get_fighter_image(fighter_name):
    formatted_name = fighter_name.lower().replace(" ", "-")
    ufc_url = f"https://www.ufc.com/athlete/{formatted_name}"
    wiki_image_url = f"https://en.wikipedia.org/wiki/Special:FilePath/{fighter_name.replace(' ', '_')}.jpg"

    try:
        response = requests.get(ufc_url, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        image_tag = soup.find('img', class_='hero-profile__image')
        fighter_image = image_tag['src'] if image_tag else None
    except:
        fighter_image = None

    if not fighter_image:
        try:
            wiki_response = requests.get(wiki_image_url, timeout=5)
            if wiki_response.status_code == 200:
                fighter_image = wiki_image_url
        except:
            pass

    return fighter_image or "https://via.placeholder.com/100"

# Run the app
if __name__ == '__main__':
    app.run(port=5000, debug=True)