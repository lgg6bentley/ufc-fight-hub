import os
import random
import sqlite3
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify, redirect, url_for
from datetime import datetime, timedelta

# Optional: for future PDF or QR code features (keeping for now)
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import ImageReader
import qrcode
import io

app = Flask(__name__, template_folder="templates", static_folder="static")

# Database setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'fighters.db')

# 🥊 Define Upcoming UFC Fight Card (UFC 319 - Actual Card based on user input)
# Ensure dates are in the future relative to when you run this
upcoming_ufc_fights = [
    {
        "fighter_a": "Dricus Du Plessis",
        "fighter_b": "Khamzat Chimaev",
        "record_a": "23-2-0",
        "record_b": "14-0-0",
        "weight_class": "Middleweight",
        "title_fight": True, # Assuming this is a title fight based on the poster
        "event_name": "UFC 319: Du Plessis vs. Chimaev",
        "event_date": datetime(2025, 8, 16, 22, 0, 0), # August 16, 2025, 10 PM EST
        "location": "T-Mobile Arena, Las Vegas, NV", # Common UFC venue
        "image_a": "/static/images/DU_PLESSIS_DRICUS.jpg",
        "image_b": "/static/images/KHAMZAT_CHIMAEV.jpg",
        "note": "Middleweight Championship Bout"
    },
    {
        "fighter_a": "Geoff Neal",
        "fighter_b": "Carlos Prates",
        "record_a": "16-6-0",
        "record_b": "21-7-0",
        "weight_class": "Welterweight",
        "title_fight": False,
        "event_name": "UFC 319: Du Plessis vs. Chimaev",
        "event_date": datetime(2025, 8, 16, 21, 30, 0),
        "location": "T-Mobile Arena, Las Vegas, NV",
        "image_a": "/static/images/GEOFF_NEAL.jpg",
        "image_b": "/static/images/CARLOS_PRATES.jpg",
        "note": "Co-main Event"
    },
    {
        "fighter_a": "Jared Cannonier",
        "fighter_b": "Michael Page",
        "record_a": "18-8-0",
        "record_b": "23-3-0",
        "weight_class": "Middleweight",
        "title_fight": False,
        "event_name": "UFC 319: Du Plessis vs. Chimaev",
        "event_date": datetime(2025, 8, 16, 21, 0, 0),
        "location": "T-Mobile Arena, Las Vegas, NV",
        "image_a": "/static/images/JARED_CANNONIER.jpg",
        "image_b": "/static/images/MICHAEL_PAGE.jpg",
        "note": "Middleweight Clash"
    }
]

# 🧠 Generate multiple parlay types (remains the same)
def generate_parlay_variants(fights, stake=100):
    parlays = {"safe": [], "risky": [], "wildcard": []}
    total_odds = {"safe": 1.0, "risky": 1.0, "wildcard": 1.0}

    for fight in fights:
        f1 = fight['fighter_a']
        f2 = fight['fighter_b']

        odds1 = random.randint(-250, 200)
        odds2 = random.randint(-250, 200)

        if odds1 < 0 and odds2 < 0:
            if abs(odds1) > abs(odds2): odds2 = random.randint(100, 200)
            else: odds1 = random.randint(100, 200)
        elif odds1 > 0 and odds2 > 0:
            if odds1 > odds2: odds1 = random.randint(-250, -110)
            else: odds2 = random.randint(-250, -110)

        winner = f1 if random.random() < 0.5 else f2
        winner_odds = odds1 if winner == f1 else odds2

        decimal_winner_odds = (winner_odds / 100) + 1 if winner_odds > 0 else (100 / abs(winner_odds)) + 1

        parlays["safe"].append({
            "fight": f"{f1} vs {f2}",
            "pick": winner,
            "type": "Winner Only",
            "odds": winner_odds
        })
        total_odds["safe"] *= decimal_winner_odds

        method = random.choice(["KO/TKO", "Submission", "Decision"])
        risky_odds = winner_odds * random.uniform(1.2, 1.8)
        parlays["risky"].append({
            "fight": f"{f1} vs {f2}",
            "pick": f"{winner} by {method}",
            "type": "Method of Victory",
            "odds": round(risky_odds, 0)
        })
        total_odds["risky"] *= (round(risky_odds, 0) / 100) + 1 if risky_odds > 0 else (100 / abs(round(risky_odds, 0))) + 1

        num_rounds = 5 if fight["title_fight"] else 3
        round_win = random.choice([f"Round {i}" for i in range(1, num_rounds + 1)])
        method_wc = random.choice(["KO/TKO", "Submission", "Decision"])
        wildcard_odds = winner_odds * random.uniform(2.0, 3.0)

        parlays["wildcard"].append({
            "fight": f"{f1} vs {f2}",
            "pick": f"{winner} in {round_win} by {method_wc}",
            "type": "Round + Method",
            "odds": round(wildcard_odds, 0)
        })
        total_odds["wildcard"] *= (round(wildcard_odds, 0) / 100) + 1 if wildcard_odds > 0 else (100 / abs(round(wildcard_odds, 0))) + 1

    return parlays, total_odds, stake

def seed_fighters():
    # Expanded list of sample fighters
    sample_fighters = [
        ("Jon Jones", "/static/images/JON_JONES.jpg", "28-1 (1 NC)", "Heavyweight"),
        ("Stipe Miocic", "/static/images/STIPE_MIOCIC.jpg", "20-5", "Heavyweight"),
        ("Ilia Topuria", "/static/images/ILIA_TOPURIA.jpg", "17-0", "Featherweight"),
        ("Charles Oliveira", "/static/images/CHARLES_OLIVEIRA.jpg", "35-11 (1 NC)", "Lightweight"),
        ("Islam Makhachev", "/static/images/ISLAM_MAKHACHEV.jpg", "27-1", "Lightweight"),
        ("Alexander Volkanovski", "/static/images/ALEXANDER_VOLKANOVSKI.jpg", "27-4", "Featherweight"),
        ("Dustin Poirier", "/static/images/POIRIER_DUSTIN.jpg", "30-9", "Lightweight"),
        ("Max Holloway", "/static/images/HOLLOWAY_MAX.jpg", "26-7", "Featherweight"),
        ("Sean O'Malley", "/static/images/OMALLEY_SEAN.jpg", "18-1", "Bantamweight"),
        ("Merab Dvalishvili", "/static/images/DVALISHVILI_MERAB.jpg", "17-4", "Bantamweight"),
        ("Bo Nickal", "/static/images/NICKAL_BO.jpg", "6-0", "Middleweight"),
        ("André Muniz", "/static/images/MUNIZ_ANDRE.jpg", "23-6", "Middleweight"),
        ("Kevin Holland", "/static/images/HOLLAND_KEVIN.jpg", "25-10", "Welterweight"),
        ("Michel Pereira", "/static/images/PEREIRA_MICHEL.jpg", "30-11", "Welterweight"),
        ("Maycee Barber", "/static/images/BARBER_MAYCEE.jpg", "14-2", "Women’s Flyweight"),
        ("Erin Blanchfield", "/static/images/BLANCHFIELD_ERIN.jpg", "12-1", "Women’s Flyweight"),
        ("Sean Strickland", "/static/images/STRICKLAND_SEAN.jpg", "29-7", "Middleweight"),
        ("Dricus Du Plessis", "/static/images/DU_PLESSIS_DRICUS.jpg", "22-2", "Middleweight"),
        ("Manon Fiorot", "/static/images/FIOROT_MANON.jpg", "12-1", "Women's Flyweight"),
        ("Jiri Prochazka", "/static/images/JIRI_PROCHAZKA.jpg", "30-5", "Light Heavyweight"),
        ("Alex Pereira", "/static/images/ALEX_PEREIRA.jpg", "13-3", "Light Heavyweight"),
        ("Arman Tsarukyan", "/static/images/ARMAN_TSARUKYAN.jpg", "22-3", "Lightweight"),
        ("Israel Adesanya", "/static/images/ISRAEL_ADESANYA.jpg", "24-3", "Middleweight"),
        ("Jamahal Hill", "/static/images/JAMAHAL_HILL.jpg", "12-2", "Light Heavyweight"),
        ("Ciryl Gane", "/static/images/CIRYL_GANE.jpg", "12-2", "Heavyweight"),
        ("Tom Aspinall", "/static/images/TOM_ASPINALL.jpg", "15-3", "Heavyweight"),
        ("Khamzat Chimaev", "/static/images/KHAMZAT_CHIMAEV.jpg", "14-0", "Middleweight"),
        ("Geoff Neal", "/static/images/GEOFF_NEAL.jpg", "16-6", "Welterweight"),
        ("Carlos Prates", "/static/images/CARLOS_PRATES.jpg", "21-7", "Welterweight"),
        ("Jared Cannonier", "/static/images/JARED_CANNONIER.jpg", "18-8", "Middleweight"),
        ("Michael Page", "/static/images/MICHAEL_PAGE.jpg", "23-3", "Welterweight"),
        # Adding more fighters
        ("Colby Covington", "/static/images/COLBY_COVINGTON.jpg", "17-4", "Welterweight"),
        ("Leon Edwards", "/static/images/LEON_EDWARDS.jpg", "22-3", "Welterweight"),
        ("Justin Gaethje", "/static/images/JUSTIN_GAETHJE.jpg", "25-5", "Lightweight"),
        ("Brandon Moreno", "/static/images/BRANDON_MORENO.jpg", "21-8-2", "Flyweight"),
        ("Deiveson Figueiredo", "/static/images/DEIVESON_FIGUEIREDO.jpg", "23-4-1", "Bantamweight"),
        ("Aljamain Sterling", "/static/images/ALJAMAIN_STERLING.jpg", "24-4", "Featherweight"),
        ("Paddy Pimblett", "/static/images/PADDY_PIMBLETT.jpg", "22-3", "Lightweight"),
        ("Shavkat Rakhmonov", "/static/images/SHAVKAT_RAKHMONOV.jpg", "18-0", "Welterweight"),
        ("Belal Muhammad", "/static/images/BELAL_MUHAMMAD.jpg", "23-3 (1 NC)", "Welterweight"),
        ("Robert Whittaker", "/static/images/ROBERT_WHITTAKER.jpg", "26-7", "Middleweight"),
        ("Paulo Costa", "/static/images/PAULO_COSTA.jpg", "14-4", "Middleweight"),
        ("Sergei Pavlovich", "/static/images/SERGEI_PAVLOVICH.jpg", "18-2", "Heavyweight"),
        ("Caio Borralho", "/static/images/CAIO_BORRALHO.jpg", "16-1 (1 NC)", "Middleweight"),
        ("Brendan Allen", "/static/images/BRENDAN_ALLEN.jpg", "24-5", "Middleweight"),
        ("Jessica Andrade", "/static/images/JESSICA_ANDRADE.jpg", "26-12", "Women's Strawweight"),
        ("Zhang Weili", "/static/images/ZHANG_WEILI.jpg", "25-3", "Women's Strawweight"),
        ("Amanda Lemos", "/static/images/AMANDA_LEMOS.jpg", "14-3-1", "Women's Strawweight"),
        ("Rose Namajunas", "/static/images/ROSE_NAMAJUNAS.jpg", "13-6", "Women's Flyweight"),
        ("Tatiana Suarez", "/static/images/TATIANA_SUAREZ.jpg", "11-0", "Women's Strawweight"),
        ("Mayra Bueno Silva", "/static/images/MAYRA_BUENO_SILVA.jpg", "11-3-1 (1 NC)", "Women's Bantamweight"),
        ("Julianna Pena", "/static/images/JULIANNA_PENA.jpg", "12-5", "Women's Bantamweight"),
        ("Raul Rosas Jr.", "/static/images/RAUL_ROSAS_JR.jpg", "9-2", "Bantamweight"),
        ("Muhammad Mokaev", "/static/images/MUHAMMAD_MOKAEV.jpg", "12-0 (1 NC)", "Flyweight"),
        ("Manel Kape", "/static/images/MANEL_KAPE.jpg", "19-6", "Flyweight"),
        ("Brandon Royval", "/static/images/BRANDON_ROYVAL.jpg", "16-8", "Flyweight"),
        ("Kai Kara-France", "/static/images/KAI_KARA_FRANCE.jpg", "24-11 (1 NC)", "Flyweight"),
        ("Alexandre Pantoja", "/static/images/ALEXANDRE_PANTOJA.jpg", "29-5", "Flyweight"),
        ("Sean Brady", "/static/images/SEAN_BRADY.jpg", "16-1", "Welterweight"),
        ("Jack Della Maddalena", "/static/images/JACK_DELLA_MADDALENA.jpg", "17-2", "Welterweight"),
        ("Max Griffin", "/static/images/MAX_GRIFFIN.jpg", "20-12", "Welterweight"),
        ("Stephen Thompson", "/static/images/STEPHEN_THOMPSON.jpg", "17-7-1", "Welterweight"),
        ("Kevin Lee", "/static/images/KEVIN_LEE.jpg", "19-8", "Welterweight"),
        ("Renato Moicano", "/static/images/RENATO_MOICANO.jpg", "19-5-1", "Lightweight"),
        ("Beneil Dariush", "/static/images/BENEIL_DARIUSH.jpg", "22-6-1", "Lightweight"),
        ("Mateusz Gamrot", "/static/images/MATEUSZ_GAMROT.jpg", "24-2 (1 NC)", "Lightweight"),
        ("Charles Jourdain", "/static/images/CHARLES_JOURDAIN.jpg", "15-7-1", "Featherweight"),
        ("Movsar Evloev", "/static/images/MOVSAR_EVLOEV.jpg", "18-0", "Featherweight"),
        ("Arnold Allen", "/static/images/ARNOLD_ALLEN.jpg", "19-3", "Featherweight"),
        ("Brian Ortega", "/static/images/BRIAN_ORTEGA.jpg", "16-3-1", "Featherweight"),
        ("Yair Rodriguez", "/static/images/YAIR_RODRIGUEZ.jpg", "16-5 (1 NC)", "Featherweight"),
        ("Magomed Ankalaev", "/static/images/MAGOMED_ANKALAEV.jpg", "19-1-1", "Light Heavyweight"),
        ("Jan Blachowicz", "/static/images/JAN_BLACHOWICZ.jpg", "29-10-1", "Light Heavyweight"),
        ("Nikita Krylov", "/static/images/NIKITA_KRYLOV.jpg", "30-9", "Light Heavyweight"),
        ("Sergei Spivak", "/static/images/SERGEI_SPIVAK.jpg", "17-4", "Heavyweight"),
        ("Tai Tuivasa", "/static/images/TAI_TUIVASA.jpg", "15-6", "Heavyweight"),
        ("Curtis Blaydes", "/static/images/CURTIS_BLAYDES.jpg", "18-4 (1 NC)", "Heavyweight"),
        ("Jailton Almeida", "/static/images/JAILTON_ALMEIDA.jpg", "21-3", "Heavyweight"),
        # Corrected / Added Derrick Lewis
        ("Derrick Lewis", "/static/images/DERRICK_LEWIS.jpg", "28-12-0 (1 NC)", "Heavyweight"),
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
        try:
            # Use INSERT OR REPLACE to update existing records if needed, or just INSERT OR IGNORE
            cursor.execute("INSERT OR IGNORE INTO fighters VALUES (?, ?, ?, ?)", fighter)
        except Exception as e:
            print(f"Error inserting {fighter[0]}: {e}")

    conn.commit()
    conn.close()

# Routes (all routes remain the same as the previous update)
@app.route('/')
def index():
    return redirect(url_for('upcoming_page'))

@app.route('/prediction')
def prediction_page():
    return render_template('prediction.html')

@app.route('/upcoming')
def upcoming_page():
    return render_template(
        'upcoming.html',
        event_name=upcoming_ufc_fights[0]["event_name"],
        event_date=upcoming_ufc_fights[0]["event_date"].strftime("%B %d, %Y"),
        event_location=upcoming_ufc_fights[0]["location"],
        main_card_fights=upcoming_ufc_fights
    )

@app.route('/seed-fighters')
def seed_fighters_route():
    seed_fighters()
    return redirect(url_for('fighters_page'))

@app.route('/analysis')
def analysis_page():
    main_event_fight = upcoming_ufc_fights[0]

    fighter_a_data = get_or_create_fighter(main_event_fight['fighter_a'])
    fighter_b_data = get_or_create_fighter(main_event_fight['fighter_b'])

    fighter_a_koto_wins = random.randint(5, 15)
    fighter_b_koto_wins = random.randint(5, 15)
    fighter_a_sub_wins = random.randint(1, 8)
    fighter_b_sub_wins = random.randint(1, 8)
    fighter_a_reach = random.randint(65, 75)
    fighter_b_reach = random.randint(65, 75)
    fighter_a_height_ft = 5
    fighter_a_height_in = random.randint(5, 11)
    fighter_b_height_ft = 5
    fighter_b_height_in = random.randint(5, 11)
    fighter_a_stance = random.choice(['Orthodox', 'Southpaw', 'Switch'])
    fighter_b_stance = random.choice(['Orthodox', 'Southpaw', 'Switch'])
    
    fighter_a_win_chance = round(random.uniform(40, 60), 0)
    fighter_b_win_chance = 100 - fighter_a_win_chance


    return render_template(
        'analysis.html',
        event=main_event_fight["event_name"],
        date=main_event_fight["event_date"].strftime("%B %d, %Y"),
        location=main_event_fight["location"],
        fighter_a_name=main_event_fight['fighter_a'],
        fighter_b_name=main_event_fight['fighter_b'],
        fighter_a_image=fighter_a_data['image'],
        fighter_b_image=fighter_b_data['image'],
        fighter_a_record=fighter_a_data['record'],
        fighter_b_record=fighter_b_data['record'],
        fighter_a_weight_class=fighter_a_data['weight_class'],
        fighter_b_weight_class=fighter_b_data['weight_class'],
        fighter_a_is_champ=main_event_fight['title_fight'],
        fighter_b_is_challenger=not main_event_fight['title_fight'],

        fighter_a_koto_wins=fighter_a_koto_wins,
        fighter_b_koto_wins=fighter_b_koto_wins,
        fighter_a_sub_wins=fighter_a_sub_wins,
        fighter_b_sub_wins=fighter_b_sub_wins,
        fighter_a_reach=fighter_a_reach,
        fighter_b_reach=fighter_b_reach,
        fighter_a_height_ft=fighter_a_height_ft,
        fighter_a_height_in=fighter_a_height_in,
        fighter_b_height_ft=fighter_b_height_ft,
        fighter_b_height_in=fighter_b_height_in,
        fighter_a_stance=fighter_a_stance,
        fighter_b_stance=fighter_b_stance,
        fighter_a_win_chance=fighter_a_win_chance,
        fighter_b_win_chance=fighter_b_win_chance
    )

@app.route('/parlay')
def parlay_predictor():
    parlays, total_odds, stake = generate_parlay_variants(upcoming_ufc_fights)
    payouts = {k: round(stake * total_odds[k], 2) for k in total_odds}

    return render_template(
        "parlay.html",
        parlays=parlays,
        total_odds=total_odds,
        payouts=payouts,
        stake=stake,
        upcoming_fights=upcoming_ufc_fights
    )

@app.route('/past-events')
def past_events():
    past_cards = [
        {
            "event": "UFC 320",
            "date": "August 17, 2025",
            "location": "TD Garden, Boston, MA",
            "main_event": "Islam Makhachev vs. Arman Tsarukyan",
            "result": "Makhachev wins by Decision",
            "pdf_link": url_for('parlay_predictor')
        },
        {
            "event": "UFC 318",
            "date": "July 19, 2025",
            "location": "Smoothie King Center, New Orleans, LA",
            "main_event": "Max Holloway vs. Dustin Poirier",
            "result": "Holloway wins by KO/TKO",
            "pdf_link": url_for('parlay_predictor')
        }
    ]
    return render_template('past_events.html', cards=past_cards)

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

# Fighter data helpers
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
    
    # Attempt to fetch from UFC.com first
    try:
        response = requests.get(ufc_url, timeout=3)
        soup = BeautifulSoup(response.text, 'html.parser')
        image_tag = soup.find('img', class_='hero-profile__image')
        if image_tag and image_tag.get('src'):
            return image_tag['src']
    except requests.exceptions.RequestException:
        pass # Fallback to placeholder

    # Fallback to a generic placeholder if UFC.com fails
    return "https://via.placeholder.com/100"

# Run the app
if __name__ == "__main__":
    seed_fighters() # Seed fighters when the app starts
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
