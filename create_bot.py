from telebot import TeleBot, StateMemoryStorage
from config_data import config


state_storage = StateMemoryStorage()
# создаем экземпляр бота
bot = TeleBot(token=config.BOT_TOKEN, state_storage=state_storage)
