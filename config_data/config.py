import os
from dotenv import load_dotenv, find_dotenv

# проверка на наличие переменных в окружении
if not find_dotenv():
    exit('Переменные окружения не загружены т.к отсутствует файл .env')
else:
    load_dotenv()


# достаем переменные из окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPID_API_KEY = os.getenv('RAPID_API_KEY')
