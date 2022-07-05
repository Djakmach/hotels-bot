from datetime import datetime, date

from loguru import logger
from telebot.types import CallbackQuery
from create_bot import bot
from keyboards.inlinekeyboards import calendar_days, calendar_months, calendar_years
from Telegram.handlers import get_check_out


def callback_date(call: CallbackQuery) -> None:
    """ Обработчик, которыйвыводит выбранную дату """
    logger.info(f'start метода-обработчика callback_date')

    user_id = call.from_user.id
    chat_id = call.message.chat.id

    user_choice = datetime.strptime(call.data[-10:], '%Y-%m-%d').date()
    current_date = date.today()
    if user_choice < current_date:
        bot.answer_callback_query(callback_query_id=call.id, text='Нельзя выбрать предыдущую дату', show_alert=True)
        return

    with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as data:

        if not data.get('check_in'):
            data['check_in'] = call.data[-10:]
            logger.info(f'данные после выбор даты заезда{data}')
            cur_date = date.today()
            bot.edit_message_text(text=f'Вы выбрали {call.data[-10:]}', chat_id=chat_id,
                                  message_id=call.message.id)
            bot.answer_callback_query(call.id)
            bot.send_message(chat_id, 'Ввыберите дату выезда', reply_markup=calendar_days(cur_date))
            return
        else:
            check_in = datetime.strptime(data.get('check_in'), '%Y-%m-%d').date()
            check_out = datetime.strptime(call.data[-10:], '%Y-%m-%d').date()
            if check_in < check_out:
                data['check_out'] = call.data[-10:]
                logger.info(f'данные после выбор даты выезда{data}')
                bot.edit_message_text(text=f'Вы выбрали {call.data[-10:]}', chat_id=chat_id, message_id=call.message.id)
            else:
                bot.answer_callback_query(callback_query_id=call.id,
                                          text='Дата выезда не должна быть больше даты заезда', show_alert=True)
                return
    get_check_out(user_id, chat_id)


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
    """ Регистратор всех обработчиков"""
    bot.register_callback_query_handler(callback_date, func=lambda call: call.data.startswith('selected_date'))
    bot.register_callback_query_handler(callback_dates_month, func=lambda call: call.data.startswith('dates'))
    bot.register_callback_query_handler(callback_months, func=lambda call: call.data.startswith('months'))
    bot.register_callback_query_handler(callback_years, func=lambda call: call.data.startswith('years'))
