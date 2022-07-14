from create_bot import bot
from Telegram import handlers, callback_query
from DataBase.db_for_history import db

from telebot.custom_filters import StateFilter


if __name__ == '__main__':
    bot.add_custom_filter(StateFilter(bot))

    # подключение обработчика команд
    handlers.register_handlers()

    # подключение обработчика клавиатуры
    callback_query.register_callback_query_handler()

    # подключение к базе данных
    db.connect_data_base()

    bot.polling(none_stop=True)
