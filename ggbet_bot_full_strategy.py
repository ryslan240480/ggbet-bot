import os
import time
import json
import requests
import telebot

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')
API_KEY = os.environ.get('ODDS_API_KEY')

bot = telebot.TeleBot(TELEGRAM_TOKEN)
PREMATCH_FILE = "prematch_signals.json"

def load_prematch_signals():
    if os.path.exists(PREMATCH_FILE):
        with open(PREMATCH_FILE, "r") as f:
            return json.load(f)
    return {}

def save_prematch_signals(data):
    with open(PREMATCH_FILE, "w") as f:
        json.dump(data, f)

def fetch_odds():
    url = 'https://api.the-odds-api.com/v4/sports/basketball/odds'
    params = {
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
        'bookmakers': 'ggbet',
        'apiKey': API_KEY
    }
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Ошибка запроса: {response.status_code}")
            return []
    except Exception as e:
        print(f"Ошибка получения данных: {e}")
        return []

def check_strategy():
    data = fetch_odds()
    tracked = load_prematch_signals()
    updated_tracked = tracked.copy()

    for event in data:
        match_id = event["id"]
        home = event["home_team"]
        away = event["away_team"]
        if not event.get("bookmakers"):
            continue

        for bookmaker in event["bookmakers"]:
            for market in bookmaker["markets"]:
                if market["key"] != "h2h":
                    continue
                outcomes = market["outcomes"]
                if len(outcomes) != 2:
                    continue

                team1, team2 = outcomes
                odds1, odds2 = team1["price"], team2["price"]

                if match_id not in tracked:
                    if 1.6 <= odds1 <= 2.4 and 1.6 <= odds2 <= 2.4:
                        if odds1 > odds2:
                            chosen, wait_for = team1, team2
                        else:
                            chosen, wait_for = team2, team1
                        msg = f"ПРЕДМАТЧ: {home} vs {away}\nСтавка: {chosen['name']} @ {chosen['price']}"
                        bot.send_message(CHAT_ID, msg)
                        updated_tracked[match_id] = {
                            "match": f"{home} vs {away}",
                            "team": chosen["name"],
                            "opponent": wait_for["name"]
                        }
                else:
                    opponent = tracked[match_id]["opponent"]
                    for out in outcomes:
                        if out["name"] == opponent and out["price"] >= 2.4:
                            msg = f"ЛАЙВ-СИГНАЛ: {home} vs {away}\nСтавка на: {opponent} @ {out['price']}"
                            bot.send_message(CHAT_ID, msg)
                            break

    save_prematch_signals(updated_tracked)

if __name__ == "__main__":
    print("Бот запущен и работает...")
    while True:
        try:
            check_strategy()
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
        time.sleep(60)
