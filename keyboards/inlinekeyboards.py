import telebot
from telebot import types
from datetime import datetime, date
from loguru import logger
from dotenv import load_dotenv
import os

load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

EMTPY_FIELD = '-1'

def calendar_years(year: str):
    logger.info('start calendar_years')
    logger.info(f'year = {year}')
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    year = int(year)
    keyboard.add(types.InlineKeyboardButton(text=str(year - 1), callback_data=f'previous_year {str(year - 1)}'))
    keyboard.add(types.InlineKeyboardButton(text=str(year), callback_data=f'current_year {str(year)}'))
    keyboard.add(types.InlineKeyboardButton(text=str(year + 1), callback_data=f'next_year{str(year + 1)}'))

    return keyboard



def calendar_months(year: str):
    logger.info('start calendar_month')
    keyboard = types.InlineKeyboardMarkup(row_width=4)
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    month_button = []
    for i_month, name_month in enumerate(months):
        month_button.append(types.InlineKeyboardButton(text=name_month,
                                                       callback_data=f'month {date(int(year), i_month + 1, 1)}'))

    month_button.append(types.InlineKeyboardButton(text='<', callback_data=f'previous_year {int(year) - 1}'))
    month_button.append(types.InlineKeyboardButton(text=year, callback_data=f'choose_year {year}'))
    month_button.append(types.InlineKeyboardButton(text='>', callback_data=f'next_year {int(year) + 1}'))
    logger.info('list buttons ready')

    keyboard.add(*month_button)
    logger.info('return calendar_month')
    return keyboard


def calendar_days(now_datetime):
    logger.info('start calendar_days')
    keyboard = types.InlineKeyboardMarkup(row_width=7)
    days = []

    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    days.extend(week_days)

    first_day = date(now_datetime.year, now_datetime.month, 1)

    empty_days = [' ' for i in range(first_day.weekday())]
    days.extend(empty_days)
    logger.info(f'Сформировали список empty кнопок: {empty_days}')

    next_month = date(first_day.year, first_day.month + 1, 1) if first_day.month != 12 else date(first_day.year + 1, 1, 1)
    days_in_month = (next_month - first_day).days
    dates = [day for day in range(1, days_in_month + 1)]
    days.extend(dates)
    logger.info(f'Сформировали список дат месяца кнопок: {dates}')


    lost = len(days) % 7
    if lost:
        empty_days = [' ' for i in range(7 - lost)]
        days.extend(empty_days)
    logger.info(f'Сформировали список empty кнопок: {empty_days}')


    button_dates = []
    logger.info(f'Сформировали список ДЛЯ кнопок: {days}')

    for day_button in days:
        callback_data = date(now_datetime.year, now_datetime.month, int(day_button)) if isinstance(day_button,
                                                                                                   int) else day_button
        button_dates.append(types.InlineKeyboardButton(text=day_button,
                                                       callback_data=f'date {callback_data}'))
    logger.info(f'cформировали список кнопок')

    date_previous_month = date(now_datetime.year, now_datetime.month - 1, now_datetime.day) if now_datetime.month != 1 else date(now_datetime.year - 1, 12, now_datetime.day)
    button_dates.append(types.InlineKeyboardButton(text='<',
                                                   callback_data=f'previous_month {date_previous_month}'))
    button_dates.append(types.InlineKeyboardButton(text=now_datetime.strftime('%B %Y'),
                                                   callback_data=f'choose_months {now_datetime.year}'))
    date_next_month = date(now_datetime.year, now_datetime.month + 1, now_datetime.day) if now_datetime.month != 12 else date(now_datetime.year + 1, 1, now_datetime.day)
    button_dates.append(types.InlineKeyboardButton(text='>',
                                                   callback_data=f'next_month {date_next_month}'))

    keyboard.add(*button_dates)
    return keyboard


@bot.message_handler(commands=["start"])
def send_mes(message):
    logger.info(f' start хендлер send_mes')
    now = datetime.now()
    bot.send_message(message.chat.id, "Выберите дату заезда:", reply_markup=calendar_days(now))
    print(message.chat.id)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    logger.info(f' start метода-обработчика callback_worker')
    if call.data.startswith('date'):
        bot.send_message(1105716326, f'Вы выбрали {call.data[-10:]}')
    if call.data.startswith('previous_month'):
        bot.send_message(1105716326, "Выберите дату заезда:",
                         reply_markup=calendar_days(datetime.strptime(call.data[-10:], '%Y-%m-%d')))
    elif call.data.startswith('choose_months'):
        bot.send_message(1105716326, "Выберите месяц:",
                         reply_markup=calendar_months(call.data[-4:]))
    elif call.data.startswith('next_month'):
        bot.send_message(1105716326, "Выберите дату заезда:",
                         reply_markup=calendar_days(datetime.strptime(call.data[-10:], '%Y-%m-%d')))

    elif call.data.startswith('month'):
        bot.send_message(1105716326, "Выберите дату:",
                         reply_markup=calendar_days(datetime.strptime(call.data[-10:], '%Y-%m-%d')))
    elif call.data.startswith('previous_year'):
        bot.send_message(1105716326, "Выберите месяц:",
                         reply_markup=calendar_months(call.data[-4:]))
    elif call.data.startswith('choose_year'):
        bot.send_message(1105716326, "Выберите год:",
                         reply_markup=calendar_years((call.data[-4:])))
    elif call.data.startswith('next_year'):
        bot.send_message(1105716326, "Выберите месяц:",
                         reply_markup=calendar_months(call.data[-4:]))


    elif call.data.startswith('current_year'):
        bot.send_message(1105716326, "Выберите месяц:",
                         reply_markup=calendar_months((call.data[-4:])))


bot.polling(none_stop=True)
logger.info(f'после bot.polling')

# bot.infinity_polling()

# with open('data_search_high_price.json', 'w') as low_price_file:
#     json.dump(hotels_json, low_price_file, indent=4)
