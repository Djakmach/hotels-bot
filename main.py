from create_bot import bot
from Telegram import handlers_bot


handlers_bot.register_handlers(bot)

bot.polling(none_stop=True)