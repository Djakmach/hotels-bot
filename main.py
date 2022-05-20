import os

from create_bot import bot
from Telegram import handlers_bot
from DataBase.db_for_history import db


# os.remove('debug.log')

handlers_bot.register_handlers(bot)

db.connect_data_base()

bot.polling(none_stop=True)
