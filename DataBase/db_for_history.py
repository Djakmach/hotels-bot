import sqlite3
from create_bot import bot


def connect_data_base():
    global data_base, cursor
    data_base = sqlite3.connect('DataBase/data_base.db')
    cursor = data_base.cursor()
    if data_base:
        print('Соединение с базой данных уставновленно')
    data_base.execute('CREATE TABLE IF NOT EXISTS history(id INTEGER, command TEXT, date_time DATETIME, hotels TEXT)')
    data_base.commit()


def add_note_in_history(data_request):
    data_base = sqlite3.connect('DataBase/data_base.db')
    cursor = data_base.cursor()
    if data_base:
        print('Соединение с базой данных уставновленно')
    data_base.execute('CREATE TABLE IF NOT EXISTS history(id INTEGER, command TEXT, date_time DATETIME, hotels TEXT)')
    cursor.execute('INSERT INTO history(command, date_time, hotels) VALUES (?, ?, ?)', tuple(data_request.values()))
    data_base.commit()


def show_history(message):
    data_base = sqlite3.connect('DataBase/data_base.db')
    cursor = data_base.cursor()
    if data_base:
        print('Соединение с базой данных уставновленно')
    try:
        for request in cursor.execute('SELECT * FROM history').fetchall():
            bot.send_message(message.from_user.id, f'Комманда: {request[1]}\nДата и время: {request[2]}\nНайденный отели: {request[3]}')
    except:
        bot.send_message(message.from_user.id, 'История поиска пуста')
    data_base.commit()