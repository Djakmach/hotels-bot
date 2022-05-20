from create_bot import bot
from Telegram import handlers_bot
from DataBase import db_for_history


handlers_bot.register_handlers(bot)

# db_for_history.connect_data_base()

bot.polling(none_stop=True)
