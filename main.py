from create_bot import bot
from Telegram import handlers_bot
from DataBase.db_for_history import db
from keyboards import inlinekeyboards


# подключение обработчика команд
handlers_bot.register_handlers()

# подключение обработчика клавиатуры
inlinekeyboards.register_callback_query_handler()

# подключение к базе данных
db.connect_data_base()

bot.polling(none_stop=True)
