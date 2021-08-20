# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import os

from collections import defaultdict
import sqlite3
import telebot

import redis

conn = sqlite3.connect('db', check_same_thread=False)
cursor = conn.cursor()
token = 'TOKEN'
bot = telebot.TeleBot(token)

BEGIN, START, NAME, LOCATION, CONFIRM = range(5)
USER_STATE = defaultdict(lambda: BEGIN)

data_list = []


def db_add_val(user_id: int, name: str, lat: float, lon: float):
    cursor.execute('INSERT OR IGNORE INTO data (user_id, name, lat, lon) VALUES (?, ?, ?, ?)',
                   (user_id, name, lat, lon))
    conn.commit()


def db_delete_val(user_id: int):
    cursor.execute('DELETE FROM data WHERE user_id = ?',
                   (user_id,))
    conn.commit()


def db_get_values(user_id: int):
    cursor.execute('SELECT * FROM data WHERE user_id = ?',
                   (user_id,))
    records = cursor.fetchmany(10)
    return records


def get_state(message):
    return USER_STATE[message.chat.id]


def update_state(message, state):
    USER_STATE[message.chat.id] = state


@bot.message_handler(func=lambda message: get_state(message) == BEGIN, content_types=['text'])
def get_text_messages(message):
    bot.send_message(message.from_user.id, 'Хочешь добавить место на карте? Выбери команду /add, отправь название, '
                                           'а затем прикрепи локацию и отправь следующим сообщением! Хочешь '
                                           'просмотреть список своих локаций - набери /list. Для сброса данных '
                                           'существует команда /reset.')
    update_state(message, START)


@bot.message_handler(func=lambda message: get_state(message) == START, commands=['add'])
def handle_title(message):
    bot.send_message(message.chat.id, 'Напиши название :)')
    update_state(message, NAME)


@bot.message_handler(func=lambda message: get_state(message) == NAME)
def handle_title(message):
    data_list.append(message.text)
    bot.send_message(message.chat.id, 'А местоположение?')
    update_state(message, LOCATION)


@bot.message_handler(func=lambda message: get_state(message) == LOCATION, content_types=['location'])
def handle_confirm(message):
    bot.send_message(message.chat.id, 'Сохраняю? (да/нет)')
    update_state(message, CONFIRM)
    data_list.append(message.location)


@bot.message_handler(func=lambda message: get_state(message) == LOCATION, content_types=['text'])
def handle_confirm(message):
    bot.send_message(message.chat.id, 'Не так!')


@bot.message_handler(func=lambda message: get_state(message) == CONFIRM)
def handle_finish(message):
    loc = data_list.pop()
    name = data_list.pop()
    if 'да' in message.text.lower():
        db_add_val(message.from_user.id, name, loc.latitude, loc.longitude)
        bot.send_message(message.chat.id, 'Сделано!')
    if 'нет' in message.text.lower():
        bot.send_message(message.chat.id, 'Ну ладно, как хочешь.')
    update_state(message, START)


@bot.message_handler(commands=['list'])
def handle_list(message):
    records = db_get_values(message.from_user.id)
    if not records:
        bot.send_message(message.chat.id, 'Еще ничего здесь нет :\'(')
    for row in records:
        bot.send_message(message.chat.id, row[1])
        bot.send_location(message.chat.id, row[2], row[3])


@bot.message_handler(commands=['reset'])
def handle_confirmation(message):
    db_delete_val(message.from_user.id)
    bot.send_message(message.chat.id, 'Все удалено :(')


bot.polling()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
