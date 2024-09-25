import os
import requests
import re
import json
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

TELEGRAM_TOKEN = 

CITIES = {
    'Астана': 'astana.php',
    'Алматы': 'almaty.php',
    'Шымкент': 'shymkent.php',
    'Караганда': 'karaganda.php',
    'Актау': 'aktau.php',
    'Актобе': 'aktobe.php',
    'Атырау': 'atyrau.php',
    'Атбасар': 'atbasar.php',
    'Павлодар': 'pavlodar.php',
    'Петропавл': 'petropavlovsk.php',
    'Тараз': 'taraz.php',
    'Темиртау': 'temirtau.php',
    'Орал': 'uralsk.php',
    'Оскемен': 'oskemen.php',
    'Бишкек': 'bishkek.php',
    'Ош': 'osh.php'
}


def get_keyboard():
    buttons = [[KeyboardButton(city) for city in list(CITIES.keys())[i:i + 3]] for i in range(0, len(CITIES), 3)]
    return ReplyKeyboardMarkup(buttons, one_time_keyboard=True)


def get_sensors_data():
    url = "https://airkaz.org/"
    response = requests.get(url)

    if response.status_code == 200:
        match = re.search(r'var sensors_data = (.*?);', response.text, re.DOTALL)

        if match:
            sensors_data_json = match.group(1).strip()
            try:
                sensors_data = json.loads(sensors_data_json)
            except json.JSONDecodeError:
                last_bracket_pos = sensors_data_json.rfind('}]')
                cleaned_json = sensors_data_json[:last_bracket_pos + 2]
                sensors_data = json.loads(cleaned_json)

            return sensors_data
    return None


def get_data(city):
    sensors_data = get_sensors_data()
    if sensors_data is None:
        return None, "Не удалось получить данные сенсоров."

    latest_data = {}
    current_time = datetime.now()

    for sensor in sensors_data:
        if sensor['city'] == city:
            sensor_time = datetime.strptime(sensor['date'], '%Y-%m-%d %H:%M:%S')
            if current_time - sensor_time <= timedelta(hours=3):
                sensor['status'] = 'OK'
                latest_data[(sensor['city'], sensor['name'])] = sensor

    return latest_data if latest_data else None, "Данные неактуальны."

def take_screenshot(city):
    url = f'https://airkaz.org/{CITIES[city]}'
    options = Options()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--headless')
    options.add_argument('--start-maximized')

    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        time.sleep(2)

        # Устанавливаем средний размер окна
        driver.set_window_size(1600, 900)

        driver.save_screenshot('screenshot.png')
    except Exception as e:
        print(f"Ошибка при создании скриншота: {e}")
    finally:
        driver.quit()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Выберите город из списка:', reply_markup=get_keyboard())


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    if city in CITIES:
        await update.message.reply_text(f'Сбор данных для города {city}...')
        latest_data, message = get_data(city)

        if latest_data:
            take_screenshot(city)  # Делаем скриншот
            await update.message.reply_photo(photo=open('screenshot.png', 'rb'))  # Отправляем скриншот
            await update.message.reply_text(
                'Индекс качества воздуха указан на картинке.\nДанные получены с сайта https://airkaz.org')
        else:
            await update.message.reply_text(message)  # Отправляем сообщение о неактуальных данных
    else:
        await update.message.reply_text('Пожалуйста, выберите город из списка.')


def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()


if __name__ == '__main__':
    main()
