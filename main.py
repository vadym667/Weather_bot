import os
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = "945919920"

LATITUDE = 48.485
LONGITUDE = 34.250


def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    requests.post(url, json=data)


def get_weather_statistic():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        "&current=temperature_2m,relative_humidity_2m"
        "&hourly=precipitation_probability"
        "&timezone=Europe%2FKyiv"
    )

    response = requests.get(url)
    weather_data = response.json()
    rain_probabilities = weather_data["hourly"]["precipitation_probability"]
    times = weather_data["hourly"]["time"]
    current_hour = datetime.now().strftime("%Y-%m-%dT%H:00")

    current_index = times.index(current_hour)

    rain_time = times[current_index]
    rain_probability = rain_probabilities[current_index]


    temperature = weather_data["current"]["temperature_2m"]
    humidity = weather_data["current"]["relative_humidity_2m"]
    return temperature, humidity, rain_probability

kyiv_time = datetime.now(ZoneInfo("Europe/Kyiv"))

date_now = kyiv_time.strftime("%d/%m/%Y")
time_now = kyiv_time.strftime("%H:%M")

temperature, humidity, rain_probability = get_weather_statistic()
def get_temperature_comment(temperature):
    if temperature > 25:
        weather_comment ="🔥 На улице жарко!"
    elif temperature < 10:
        weather_comment = "🥶 На улице холодно!"
    else:
        weather_comment = "😎 Нормальная температура."
    return weather_comment

weather_comment = get_temperature_comment(temperature)

def get_humidity_comment(humidity):
    if humidity > 80:
        weather_comment1 = "💧 Очень влажно!"
    elif humidity < 50:
        weather_comment1 = "🏜 Сухо!"
    else:
        weather_comment1 = "🌤 Нормальная влажность"
    return weather_comment1

def get_rain_comment(rain_probability):
    if rain_probability > 70:
        return "☔ Высокая вероятность дождя!"
    elif rain_probability < 30:
        return "☀ Дождь маловероятен."
    else:
        return "🌥 Возможен дождь"
rain_comment = get_rain_comment(rain_probability)

weather_comment1 = get_humidity_comment(humidity)


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

    params = {
        "timeout": 30,
        "offset": offset
    }

    response = requests.get(url, params=params)
    return response.json()

already_sent = False
last_update_id = None

while True:

    updates = get_updates(last_update_id)

    for update in updates["result"]:
        last_update_id = update["update_id"] + 1

        if "message" not in update:
            continue

        message = update["message"]
        chat_id = message["chat"]["id"]

        if "text" not in message:
            continue

        text = message["text"]

        if text == "/forecast":
            temperature, humidity, rain_probability = get_weather_statistic()

            weather_comment = get_temperature_comment(temperature)
            weather_comment1 = get_humidity_comment(humidity)
            rain_comment = get_rain_comment(rain_probability)

            date_now = datetime.now().strftime("%d/%m/%Y")
            time_now = datetime.now().strftime("%H:%M")

            send_message(
                chat_id,
                f"🌤 Погода в Верховцеве\n"
                f"Температура: {temperature}°C\n"
                f"{weather_comment}\n"
                f"Влажность: {humidity}%\n"
                f"{weather_comment1}\n"
                f"Вероятность дождя: {rain_probability}%\n"
                f"{rain_comment}\n"
                f"Дата запуска: {date_now}\n"
                f"Время запуска: {time_now}"
            )