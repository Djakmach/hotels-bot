from create_bot import bot
from Telegram import handlers
from DataBase.db_for_history import db
from keyboards import inlinekeyboards
from telebot.custom_filters import StateFilter

bot.add_custom_filter(StateFilter(bot))

# подключение обработчика команд
handlers.register_handlers()

# подключение обработчика клавиатуры
inlinekeyboards.register_callback_query_handler()

# подключение к базе данных
db.connect_data_base()

bot.polling(none_stop=True)
