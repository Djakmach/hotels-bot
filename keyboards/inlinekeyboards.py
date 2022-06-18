from create_bot import bot

from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from datetime import datetime, date
from loguru import logger

EMTPY_FIELD = '-1'


def calendar_years(year: str) -> InlineKeyboardMarkup:
    """
       Клавиатура для выбора года

       :param year: год от которого отталкивается выбор
       :rtype year: str
    """

    logger.info('start calendar_years')
    logger.info(f'year = {year}')
    keyboard = InlineKeyboardMarkup(row_width=3)
    year = int(year)
    keyboard.add(InlineKeyboardButton(text=str(year - 1), callback_data=f'months_selected_year {str(year - 1)}'))
    keyboard.add(InlineKeyboardButton(text=str(year), callback_data=f'months_selected_year {str(year)}'))
    keyboard.add(InlineKeyboardButton(text=str(year + 1), callback_data=f'months_selected_year{str(year + 1)}'))
    return keyboard


def calendar_months(year: str) -> InlineKeyboardMarkup:
    """
       Клавиатура для выбора месяца

       :param year: год от которого отталкивается выбор
       :rtype year: str
    """
    logger.info('start calendar_month')
    keyboard = InlineKeyboardMarkup(row_width=4)
    months = ['янв', 'фев', 'мар', 'апр', 'май', 'июн', 'июл', 'авг', 'сен', 'окт', 'ноя', 'дек']
    month_button = []
    for i_month, name_month in enumerate(months):
        month_button.append(InlineKeyboardButton(text=name_month,
                                                       callback_data=f'dates_selected_month {date(int(year), i_month + 1, 1)}'))

    month_button.append(InlineKeyboardButton(text='<', callback_data=f'months_previous_year {int(year) - 1}'))
    month_button.append(InlineKeyboardButton(text=year, callback_data=f'years {year}'))
    month_button.append(InlineKeyboardButton(text='>', callback_data=f'months_next_year {int(year) + 1}'))
    logger.info('list buttons ready')

    keyboard.add(*month_button)
    logger.info('return calendar_month')
    return keyboard


def calendar_days(now_date: date) -> InlineKeyboardMarkup:
    """
       Клавиатура для выбора даты

       :param now_date: год от которого отталкивается выбор
       :rtype now_date: str
    """
    logger.info('start calendar_days')
    keyboard = InlineKeyboardMarkup(row_width=7)
    days = []

    week_days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    days.extend(week_days)

    first_day = date(now_date.year, now_date.month, 1)

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
        callback_data = date(now_date.year, now_date.month, int(day_button)) if isinstance(day_button, int) else day_button
        button_dates.append(InlineKeyboardButton(text=day_button,
                                                       callback_data=f'selected_date {callback_data}'))
    logger.info(f'cформировали список кнопок')

    date_previous_month = date(now_date.year, now_date.month - 1, 1) if now_date.month != 1 else date(now_date.year - 1, 12, 1)
    button_dates.append(InlineKeyboardButton(text='<',
                                                   callback_data=f'dates_previous_month {date_previous_month}'))
    button_dates.append(InlineKeyboardButton(text=now_date.strftime('%B %Y'),
                                                   callback_data=f'months_selected_year {now_date.year}'))
    date_next_month = date(now_date.year, now_date.month + 1, 1) if now_date.month != 12 else date(now_date.year + 1, 1, 1)
    button_dates.append(InlineKeyboardButton(text='>',
                                                   callback_data=f'dates_next_month {date_next_month}'))

    keyboard.add(*button_dates)
    return keyboard


def callback_date(call: CallbackQuery) -> date | None:
    """ Обработчик, которыйвыводит выбранную дату"""
    logger.info(f'start метода-обработчика callback_date')

    user_choice = datetime.strptime(call.data[-10:], '%Y-%m-%d').date()
    current_date = date.today()
    if user_choice < current_date:
        bot.answer_callback_query(callback_query_id=call.id, text='Нельзя выбрать предыдущую дату', show_alert=True)
    else:
        bot.edit_message_text(text=f'Вы выбрали {call.data[-10:]}', chat_id=call.message.chat.id,
                              message_id=call.message.id)
        bot.answer_callback_query(call.id)
        return user_choice                         # TODO вот после этого места нужно как то перейти к вводу следующего параметра


def callback_dates_month(call: CallbackQuery) -> None:
    """ Обработчик, который заменяет текущую клавиатуру на клавиатру с выбором дат месяца """
    logger.info(f'start метода-обработчика callback_dates_month')
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id,
                                  reply_markup=calendar_days(datetime.strptime(call.data[-10:], '%Y-%m-%d')))
    bot.answer_callback_query(call.id)


def callback_months(call: CallbackQuery) -> None:
    """ Обработчик, который заменяет текущую клавиатуру на клавиатру с выбором месяцев """
    logger.info(f'start метода-обработчика callback_months')
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id,
                                  reply_markup=calendar_months(call.data[-4:]))
    bot.answer_callback_query(call.id)


def callback_years(call: CallbackQuery) -> None:
    """ Обработчик, который заменяет текущую клавиатуру на клавиатру с выбором годов """
    logger.info(f'start метода-обработчика callback_years')
    bot.edit_message_reply_markup(chat_id=call.message.chat.id, message_id=call.message.id,
                                  reply_markup=calendar_years((call.data[-4:])))


def register_callback_query_handler():
    bot.register_callback_query_handler(callback_date, func=lambda call: call.data.startswith('selected_date'))
    bot.register_callback_query_handler(callback_dates_month, func=lambda call: call.data.startswith('dates'))
    bot.register_callback_query_handler(callback_months, func=lambda call: call.data.startswith('months'))
    bot.register_callback_query_handler(callback_years, func=lambda call: call.data.startswith('years'))
