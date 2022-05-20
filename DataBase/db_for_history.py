import sqlite3
from create_bot import bot
from loguru import logger


class DB:
    data_base = None
    cursor = None

    def connect_data_base(self):
        self.data_base = sqlite3.connect('DataBase/data_base.db', check_same_thread=False)
        self.cursor = self.data_base.cursor()
        if self.data_base:
            logger.info('Соединение с базой данных уставновленно')
        self.data_base.execute('CREATE TABLE IF NOT EXISTS history(id INTEGER PRIMARY KEY AUTOINCREMENT, command TEXT, date_time DATETIME, hotels TEXT)')
        self.data_base.commit()

    def add_note_in_history(self, data_request):
        # self.cursor.execute('INSERT INTO history(command, date_time, hotels) VALUES (?, ?, ?)', tuple(data_request.values()))
        self.cursor.execute('INSERT INTO history VALUES (NULL, ?, ?, ?)', tuple(data_request.values()))
        self.data_base.commit()


    def show_history(self, message):
        try:
            for request in self.cursor.execute('SELECT * FROM history').fetchall():
                bot.send_message(message.from_user.id, f'Комманда: {request[1]}\nДата и время: {request[2]}\nНайденный отели: {request[3]}')
                self.data_base.commit()
        except AttributeError:
            bot.send_message(message.from_user.id, 'История поиска пуста')


db = DB()
