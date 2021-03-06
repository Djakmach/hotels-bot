import sqlite3
from create_bot import bot
from loguru import logger


class DB:
    data_base = None
    cursor = None

    def connect_data_base(self) -> None:
        """ Метод для соединения с базой данных(если ее нет-создается новая) """
        self.data_base = sqlite3.connect('DataBase/data_base.db', check_same_thread=False)
        self.cursor = self.data_base.cursor()
        if self.data_base:
            logger.info('Соединение с базой данных уставновленно')
        self.data_base.execute('CREATE TABLE IF NOT EXISTS history(user_id INTEGER, command TEXT,'
                               ' date_time DATETIME, hotels TEXT)')
        self.data_base.commit()

    def add_note_in_history(self, data_request) -> None:
        """ Метод для записи данных в базу данных """
        self.cursor.execute('INSERT INTO history VALUES (?, ?, ?, ?)', tuple(data_request.values()))
        self.data_base.commit()

    def show_history(self, user_id) -> None:
        """ Метод для получения данных из базы данных """
        try:
            data = self.cursor.execute('SELECT * FROM history WHERE user_id= {}'. format(user_id)).fetchall()
            if data:
                for request in data:
                    bot.send_message(user_id, f'Комманда: {request[1]}\nДата и время: {request[2]}\n'
                                                           f'Найденные отели: {request[3]}')
                    self.data_base.commit()
            else:
                bot.send_message(user_id, 'История поиска пуста')
        except AttributeError:
            logger.info('База данных с историей запросов отсутсвует')


db = DB()
