import os
import time
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

LATITUDE = 48.485
LONGITUDE = 34.250

MY_CHAT_ID = 945919920
SUBSCRIBERS_FILE = "subscribers.json"


def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if reply_markup is not None:
        data["reply_markup"] = reply_markup

    requests.post(url, json=data)

def answer_callback(callback_query_id):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"

    data = {
        "callback_query_id": callback_query_id
    }

    requests.post(url, json=data)

def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"

    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text
    }

    if reply_markup is not None:
        data["reply_markup"] = reply_markup

    requests.post(url, json=data)

def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE, "r") as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()


def save_subscribers(subscribers):
    with open(SUBSCRIBERS_FILE, "w") as file:
        json.dump(list(subscribers), file)

def get_weather_statistic():
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={LATITUDE}"
        f"&longitude={LONGITUDE}"
        "&current=temperature_2m,relative_humidity_2m,precipitation,rain"
        "&hourly=precipitation_probability"
        "&timezone=Europe%2FKyiv"
    )

    response = requests.get(url)
    weather_data = response.json()
    rain_probabilities = weather_data["hourly"]["precipitation_probability"]
    times = weather_data["hourly"]["time"]
    current_hour = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%dT%H:00")
    current_index = times.index(current_hour)
    rain_probability = rain_probabilities[current_index]

    precipitation = weather_data["current"]["precipitation"]
    rain = weather_data["current"]["rain"]


    temperature = weather_data["current"]["temperature_2m"]
    humidity = weather_data["current"]["relative_humidity_2m"]
    return temperature, humidity, rain_probability, precipitation, rain

def get_rain_forecast():
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={LATITUDE}"
            f"&longitude={LONGITUDE}"
            "&hourly=precipitation_probability"
            "&timezone=Europe%2FKyiv"
        )

        response = requests.get(url)
        weather_data = response.json()

        times = weather_data["hourly"]["time"]
        rain_probabilities = weather_data["hourly"]["precipitation_probability"]

        current_hour = datetime.now(ZoneInfo("Europe/Kyiv")).strftime("%Y-%m-%dT%H:00")
        current_index = times.index(current_hour)

        forecast_text = "📅 Прогноз дождя на ближайшие 6 часов\n\n"

        for i in range(6):
            index = current_index + i

            time_text = times[index][11:16]
            rain_probability = rain_probabilities[index]

            forecast_text += f"{time_text} — {rain_probability}%\n"

        return forecast_text

def get_temperature_comment(temperature):
    if temperature > 25:
        weather_comment ="🔥 На улице жарко!"
    elif temperature < 10:
        weather_comment = "🥶 На улице холодно!"
    else:
        weather_comment = "😎 Нормальная температура."
    return weather_comment

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


def get_updates(offset=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

    params = {
        "timeout": 30,
        "offset": offset
    }

    response = requests.get(url, params=params)
    return response.json()

main_keyboard = {
    "keyboard": [
        ["🌤 Погода", "☔ Дождь"],
        ["ℹ️ Помощь"]
    ],
    "resize_keyboard": True
}

inline_keyboard = {
    "inline_keyboard": [
        [
            {"text": "🌤 Погода", "callback_data": "weather"},
            {"text": "☔ Дождь", "callback_data": "rain"}
        ],
        [
            {"text": "📅 Прогноз", "callback_data": "forecast"},
            {"text": "ℹ️ Помощь", "callback_data": "help"}
        ],
        [
            {"text": "🔔 Подписаться", "callback_data": "subscribe"},
            {"text": "🔕 Отписаться", "callback_data": "unsubscribe"}
        ]
    ]
}

already_sent = False
last_update_id = None

last_rain_check = 0

subscribers = load_subscribers()

while True:

    updates = get_updates(last_update_id)

    if "result" not in updates:
        print("Ошибка Telegram:", updates)
        time.sleep(5)
        continue

    for update in updates["result"]:
        last_update_id = update["update_id"] + 1
        if "callback_query" in update:
            callback = update["callback_query"]
            answer_callback(callback["id"])

            chat_id = callback["message"]["chat"]["id"]
            message_id = callback["message"]["message_id"]
            text = callback["data"]
            is_callback = True

            if text == "weather":
                text = "/weather"

            if text == "rain":
                text = "/rain"

            if text == "help":
                text = "/help"

            if text == "forecast":
                text = "/forecast"

            if text == "subscribe":
                text = "/subscribe"

            if text == "unsubscribe":
                text = "/unsubscribe"

        else:
            if "message" not in update:
                continue

            message = update["message"]
            chat_id = message["chat"]["id"]

            if "text" not in message:
                continue

            text = message["text"]
            is_callback = False

        def reply(text_to_send):
            if is_callback:
                edit_message(chat_id, message_id, text_to_send, inline_keyboard)
            else:
                send_message(chat_id, text_to_send)

        if text == "/start":
            send_message(
                chat_id,
                "👋 Ку!\n"
                "Я погодный бот для Верховцева.\n\n"
                "Выбери действие кнопками ниже 👇",
                 inline_keyboard
             )

        elif text == "/rain" or text == "☔ Дождь":
            temperature, humidity, rain_probability, precipitation, rain = get_weather_statistic()

            rain_comment = get_rain_comment(rain_probability)

            reply(
                f"☔ Дождь в Верховцево\n"
                f"Вероятность дождя: {rain_probability}%\n"
                f"🌊 Осадки сейчас: {precipitation} мм\n"
                f"🧊 Дождь сейчас: {rain} мм\n"
                f"{rain_comment}"
            )

        elif text == "/weather" or text == "🌤 Погода":
            temperature, humidity, rain_probability, precipitation, rain = get_weather_statistic()

            weather_comment = get_temperature_comment(temperature)
            weather_comment1 = get_humidity_comment(humidity)
            rain_comment = get_rain_comment(rain_probability)

            kyiv_time = datetime.now(ZoneInfo("Europe/Kyiv"))

            date_now = kyiv_time.strftime("%d/%m/%Y")
            time_now = kyiv_time.strftime("%H:%M")

            reply(
                f"🌤 Погода в Верховцеве\n"
                f"Температура: {temperature}°C\n"
                f"{weather_comment}\n"
                f"Влажность: {humidity}%\n"
                f"{weather_comment1}\n"
                f"Вероятность дождя: {rain_probability}%\n"
                f"🌊 Осадки сейчас: {precipitation} мм\n"
                f"🧊 Дождь сейчас: {rain} мм\n"
                f"{rain_comment}\n"
                f"Дата запуска: {date_now}\n"
                f"Время запуска: {time_now}"
            )
        elif text == "/forecast":
            forecast_text = get_rain_forecast()

            reply(
                forecast_text
            )

        elif text == "/help" or text == "ℹ️ Помощь":
            reply(
                "ℹ️ Помощь\n\n"
                "🌤 /weather — текущая погода\n"
                "☔ /rain — вероятность дождя\n"
                "📖 /help — список команд\n"
                "📅 /forecast — прогноз дождя на 6 часов\n"
                "👋 /start — главное меню"
            )


        elif text == "/subscribe":

            if chat_id in subscribers:

                reply("✅ Ты уже подписан на уведомления.")

            else:

                subscribers.add(chat_id)

                save_subscribers(subscribers)

                reply("🔔 Ты подписался на уведомления о дожде.")



        elif text == "/unsubscribe":

            if chat_id not in subscribers:

                reply("❌ Ты и так не подписан, loh.")

            else:

                subscribers.discard(chat_id)

                save_subscribers(subscribers)

                reply("🔕 Ты отписался от уведомлений.")

        elif text == "/stats":

            if chat_id == MY_CHAT_ID:
                reply(
                    f"📊 Статистика бота\n\n"
                    f"👥 Подписчиков: {len(subscribers)}\n"
                    f"🤖 Бот работает нормально"
                )

        else:
            send_message(
                chat_id,
                "❓ Неизвестная команда.\nНажми /help для списка команд."
            )
    current_time = time.time()

    if current_time - last_rain_check >= 1800:
        temperature, humidity, rain_probability, precipitation, rain = get_weather_statistic()
        rain_comment = get_rain_comment(rain_probability)

        if rain_probability >= 70 and not already_sent:
            for subscriber_id in subscribers:
                send_message(
                    subscriber_id,
                    f"⚠️ Возможен дождь в Верховцево!\n"
                    f"Вероятность дождя: {rain_probability}%\n"
                    f"🌊 Осадки сейчас: {precipitation} мм\n"
                    f"🧊 Дождь сейчас: {rain} мм\n"
                    f"{rain_comment}"
                )


            already_sent = True

        elif rain_probability < 70:
            already_sent = False

        last_rain_check = current_time

    time.sleep(1)