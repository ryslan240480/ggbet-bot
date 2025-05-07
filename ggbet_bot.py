import os
import time
import telebot
import requests

TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
API_KEY = os.environ.get('API_KEY')
CHAT_ID = os.environ.get('CHAT_ID')

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def fetch_odds():
    url = 'https://api.the-odds-api.com/v4/sports/basketball_nba/odds'
    params = {
        'regions': 'eu',
        'markets': 'h2h',
        'oddsFormat': 'decimal',
        'apiKey': API_KEY
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        matches = []
        for event in data:
            if not event.get('bookmakers'):
                continue
            for bookmaker in event['bookmakers']:
                for market in bookmaker['markets']:
                    if market['key'] == 'h2h':
                        outcomes = market['outcomes']
                        if len(outcomes) == 2:
                            team1, team2 = outcomes
                            if 1.6 <= team1['price'] <= 2.4 and 1.6 <= team2['price'] <= 2.4:
                                matches.append(f"{event['home_team']} vs {event['away_team']} - {team1['price']} / {team2['price']}")
        return matches
    else:
        return [f"Ошибка при запросе коэффициентов: {response.status_code}"]

def send_telegram_message(message):
    try:
        bot.send_message(CHAT_ID, message)
    except Exception as e:
        print(f"Ошибка отправки сообщения: {e}")

if __name__ == "__main__":
    print("Бот запущен и работает...")
    while True:
        try:
            matches = fetch_odds()
            if matches:
                for match in matches:
                    print(f"Найден матч: {match}")
                    send_telegram_message(f"Найден матч: {match}")
            else:
                print("Подходящих матчей не найдено.")
        except Exception as e:
            print(f"Ошибка в основном цикле: {e}")
        time.sleep(60)
