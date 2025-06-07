import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, request, jsonify
import random

app = Flask(__name__, template_folder="templates")

@app.route('/')
def home():
    try:
        return render_template('prediction.html')  # Load fight prediction page
    except Exception as e:
        return f"Error loading page: {str(e)}"

# Function to Fetch Fighter Images Dynamically from UFC or Wikipedia
def get_fighter_image(fighter_name):
    formatted_name = fighter_name.lower().replace(" ", "-")  # UFC URL format
    ufc_url = f"https://www.ufc.com/athlete/{formatted_name}"
    wiki_image_url = f"https://en.wikipedia.org/wiki/Special:FilePath/{fighter_name.replace(' ', '_')}.jpg"

    response = requests.get(ufc_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Try fetching UFC image
    image_tag = soup.find('img', class_='hero-profile__image')
    fighter_image = image_tag['src'] if image_tag else None

    # If UFC image not found, try Wikipedia
    if not fighter_image:
        wiki_response = requests.get(wiki_image_url)
        if wiki_response.status_code == 200:
            fighter_image = wiki_image_url

    return fighter_image or "https://via.placeholder.com/100"  # Fallback image

# Function to Fetch Fighter Stats from Sherdog
def get_fighter_stats(fighter_name):
    search_url = f"https://www.sherdog.com/search?search={fighter_name.replace(' ', '+')}"
    response = requests.get(search_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    fighter_link = soup.find('a', class_='search_tiger_item')
    if not fighter_link:
        return {"record": "Unknown", "weight_class": "Unknown"}

    profile_url = "https://www.sherdog.com" + fighter_link['href']
    fighter_response = requests.get(profile_url)
    fighter_soup = BeautifulSoup(fighter_response.text, 'html.parser')

    record = fighter_soup.find('span', class_='record').text if fighter_soup.find('span', class_='record') else "Unknown"
    weight_class = fighter_soup.find('h6', class_='title').text if fighter_soup.find('h6', class_='title') else "Unknown"

    return {"record": record, "weight_class": weight_class}

@app.route('/prediction')
def prediction_page():
    return render_template('prediction.html')


@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    fighter1 = data.get("fighter1")
    fighter2 = data.get("fighter2")

    prediction = {
        fighter1: round(random.uniform(40, 60), 2),
        fighter2: round(100 - random.uniform(40, 60), 2)
    }

    fighter1_data = get_fighter_stats(fighter1)
    fighter2_data = get_fighter_stats(fighter2)

    fighter1_image = get_fighter_image(fighter1)
    fighter2_image = get_fighter_image(fighter2)

    return jsonify({
        fighter1: {
            "win_rate": prediction[fighter1],
            "image": fighter1_image,
            "record": fighter1_data["record"],
            "weight_class": fighter1_data["weight_class"]
        },
        fighter2: {
            "win_rate": prediction[fighter2],
            "image": fighter2_image,
            "record": fighter2_data["record"],
            "weight_class": fighter2_data["weight_class"]
        }
    })
if __name__ == "__main__":
    app.run(debug=True)
    