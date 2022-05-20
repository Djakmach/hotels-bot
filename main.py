from create_bot import bot
from Telegram import handlers_bot
from DataBase.db_for_history import db


handlers_bot.register_handlers(bot)

db.connect_data_base()

bot.polling(none_stop=True)
