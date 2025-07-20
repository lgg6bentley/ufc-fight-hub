# preload_fighters.py
from app import get_or_create_fighter, DB_PATH

print(f"Using database at: {DB_PATH}")

fighters = [
    "Jon Jones", "Stipe Miocic", "Ilia Topuria", "Charles Oliveira",
    "Islam Makhachev", "Alexander Volkanovski", "Sean O'Malley", "Aljamain Sterling",
    "Leon Edwards", "Kamaru Usman", "Israel Adesanya", "Robert Whittaker",
    "Conor McGregor", "Dustin Poirier", "Justin Gaethje", "Max Holloway",
    "Alex Pereira", "Jiri Prochazka", "Brandon Moreno", "Deiveson Figueiredo",
    "Tom Aspinall", "Sergei Pavlovich", "Petr Yan", "Merab Dvalishvili",
    "Khamzat Chimaev", "Bo Nickal", "Shavkat Rakhmonov", "Tai Tuivasa",
    "Ciryl Gane", "Paulo Costa"
]

for name in fighters:
    print(f"Fetching and storing: {name}")
    try:
        fighter = get_or_create_fighter(name)
        print(f"✅ {fighter['name']} added with record {fighter['record']}")
    except Exception as e:
        print(f"❌ Failed to add {name}: {e}")