from datetime import datetime, date

from loguru import logger
from states.param_request import UserParamRequestState
from telebot.types import Message, InputMediaPhoto
from create_bot import bot
from keyboards.inlinekeyboards import calendar_days
from API.Hotels_requests import RequestHandler
from DataBase.db_for_history import db


def help_handler(message: Message) -> None:
    """ стандартный хендлер, реагирующий на команды help и start """
    logger.info(f"Пользователь с id {message.from_user.id} ввел комманду: ('/help/start')")

    mess = 'Я бот предназначенный для поиска отелей\n\nВы можете управлять мной, ' \
           'отправив следующие команды:\n\n/help - помощь по командам бота\n' \
           '/lowprice - вывод самых дешёвых отелей в городе\n' \
           '/highprice - вывод самых дорогих отелей в городе\n' \
           '/bestdeal - вывод отелей, наиболее подходящих по цене и расположению от центра\n' \
           '/history -  вывод истории поиска отелей'
    bot.send_message(message.chat.id, mess)


def lowprice(message: Message) -> None:
    """ Начало сценария lowprice"""
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.city, chat_id=message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['command'] = 'lowprice'
    logger.info(f"Пользователь с id {message.from_user.id} ввел комманду: ('/lowprice')")


def highprice(message: Message) -> None:
    """ Начало сценария highprice"""
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.city, chat_id=message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['command'] = 'highprice'
    logger.info(f"Пользователь с id {message.from_user.id} ввел комманду: ('/highprice')")


def bestdeal(message: Message) -> None:
    """ Начало сценария bestdeal"""
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.city, chat_id=message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['command'] = 'bestdeal'
    logger.info(f"Пользователь с id {message.from_user.id} ввел комманду: ('/bestdeal')")



@bot.message_handler(state="*", commands=['cancel'])
def exist_state(message: Message):
    """ Cancel state """
    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)
    logger.debug(f"Пользователь с id {message.from_user.id} отменил ввод параметров: ('/cancel')")



@bot.message_handler(state=UserParamRequestState.city)
def get_city(message: Message) -> None:
    """ получаем город"""

    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['city'] = message.text
    logger.info(f"Пользователь с id {message.from_user.id} ввел информацию о городе: ('{message.text}')")
    cur_date = date.today()
    bot.send_message(message.from_user.id, 'Ввыберите дату заезда', reply_markup=calendar_days(cur_date))



def get_check_out(user_id, chat_id) -> None:
    """
    получаем дату выезда, и далее в зависимости от сценария просим ввести минимальную цену либо сразу переходим на
    ввод количества отелей
    """

    with bot.retrieve_data(user_id=user_id, chat_id=chat_id) as data:

        if data.get('command') == 'bestdeal':
            bot.send_message(chat_id, 'Введите минимальную цену за ночь (руб)')
            bot.set_state(user_id=user_id, state=UserParamRequestState.price_min,
                          chat_id=chat_id)

        else:
            bot.send_message(chat_id, 'Введите кол-во отелей (не больше 10)')
            bot.set_state(user_id=user_id, state=UserParamRequestState.amount_hotels,
                          chat_id=chat_id)


@bot.message_handler(state=UserParamRequestState.price_min)
def get_price_min(message: Message) -> None:
    """ получаем минимальную цену """
    try:
        price_min = int(message.text)
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['price_min'] = price_min
            logger.info(f"Пользователь с id {message.from_user.id} ввел информацию минимальной цене: ('{price_min}')")

        bot.send_message(message.from_user.id, 'Введите максимальную цену за ночь (руб)')
        bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.price_max, chat_id=message.chat.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода, введите пожалуйста цифрами')
        logger.info(f"Пользователь с id {message.from_user.id} допустил ошибку при вводе минимальной цены")


@bot.message_handler(state=UserParamRequestState.price_max)
def get_price_max(message: Message) -> None:
    """ получаем максимальную цену """
    try:
        price_max = int(message.text)
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            if data['price_min'] > price_max:
                raise ValueError
            else:
                data['price_max'] = price_max
                logger.info(f"Пользователь с id {message.from_user.id} ввел информацию максимальной цене: ('{price_max}')")

                bot.send_message(message.from_user.id, 'Введите максимальное расстояние от центра города (км)')
                bot.set_state(user_id=message.from_user.id,
                              state=UserParamRequestState.distance_for_centre,
                              chat_id=message.chat.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода, введите пожалуйста цифрами и значение не'
                                               ' должно быть меньше минимальной цены')
        logger.info(f"Пользователь с id {message.from_user.id} допустил ошибку при вводе максимальной цены")


@bot.message_handler(state=UserParamRequestState.distance_for_centre)
def getting_distance_for_centre(message: Message):
    """ получаем максимальное расстояние от центра города """
    try:
        max_distance = int(message.text)
        if max_distance < 0:
            raise ValueError
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['max_distance'] = max_distance
            logger.info(f"Пользователь с id {message.from_user.id} ввел информацию о "
                        f"максимальном расстоянии: ('{max_distance}')")

        bot.send_message(message.from_user.id, 'Введите кол-во отелей (не больше 10)')
        bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.amount_hotels,
                      chat_id=message.chat.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода, введите значение цифрами (значение должно быть больше 0)')
        logger.info(f"Пользователь с id {message.from_user.id} допустил ошибку при вводе макс расстояния до центра")


@bot.message_handler(state=UserParamRequestState.amount_hotels)
def get_amount_hotels(message: Message) -> None:
    """ получаем количество отелей которое нужно вывести """
    try:
        amount_hotels = int(message.text)
        if 1 <= amount_hotels <= 10:
            with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
                data['amount_hotels'] = amount_hotels
                logger.info(f"Пользователь с id {message.from_user.id} ввел информацию о кол-ве отелей: ('{amount_hotels}')")

            bot.send_message(message.from_user.id, 'Предоставить фото?')
            bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.is_photo_needed,
                          chat_id=message.chat.id)
        else:
            bot.send_message(message.from_user.id, 'Ошибка ввода')
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода, введите значение от 1 до 10')
        logger.info(f"Пользователь с id {message.from_user.id} допустил ошибку при вводе кол-ва отелей")



@bot.message_handler(state=UserParamRequestState.is_photo_needed)
def get_is_photo_needed(message: Message) -> None:
    """ спрашиваем нужно ли вывести фото """
    user_answer = message.text.lower()
    if user_answer == 'да' or user_answer == 'yes':
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['is_photo_needed'] = True
            logger.info(f"Пользователь с id {message.from_user.id} ввел информацию о необходимости вывода фото: ('{True}')")
            bot.send_message(message.from_user.id, 'Сколько вывести фотографий?')
            bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.amount_photo,
                          chat_id=message.chat.id)
    elif user_answer == 'нет' or user_answer == 'no':
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['is_photo_needed'] = False
            logger.info(f"Пользователь с id {message.from_user.id} ввел информацию о необходимости вывода фото: ('{False}')")
            processing_request(data, message)
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        bot.send_message(message.from_user.id, "Ошибка ввода, введите 'да' или 'нет'")
        logger.info(f"Пользователь с id {message.from_user.id} допустил ошибку при выборе вывода фотографий")



@bot.message_handler(state=UserParamRequestState.amount_photo)
def get_amount_photo(message: Message) -> None:
    """ если попросили вывести фото, тогда спрашиваем сколько? """
    chat_id = message.chat.id
    try:
        amount_photo = int(message.text)
        if amount_photo > 5:
            amount_photo = 5
        elif amount_photo < 0:
            amount_photo = 0

        with bot.retrieve_data(user_id=message.from_user.id, chat_id=chat_id) as data:
            data['amount_photo'] = amount_photo
            logger.info(f"Пользователь с id {message.from_user.id} ввел информацию о кол-ве фото: ('{amount_photo}')")

            processing_request(data, message)

        bot.delete_state(message.from_user.id, message.chat.id)

    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода, введите число цифрами')
        logger.info(f"Пользователь с id {message.from_user.id} допустил ошибку при выборе кол-ва фотографий")



def processing_request(request_parameters, message):
    """ начинаем процесс обработки запроса """

    logger.info(f'Параметры запроса для пользователя c id {message.from_user.id}: {request_parameters}')
    hotel_information = get_information(request_parameters)
    logger.info(f'Результат поиска для пользователя c id {message.from_user.id}: {hotel_information}')
    if hotel_information:
        output_information(message.chat.id, hotel_information)
        hotels = ', '.join([name.get('name_hotel') for name in hotel_information])
        write_in_history(message.from_user.id, request_parameters.get('command'), hotels)
    else:
        bot.send_message(message.chat.id, 'По вашему запросу ничего не найдено')


def get_information(data):
    """ получаем данные об оттелях """

    object_request = RequestHandler()
    hotel_information = object_request(**data)
    return hotel_information


def output_information(chat_id, hotel_information):
    """ выводим информацию об отелях в чат пользователю """

    for data_hotel in hotel_information:
        result = ''
        link = ''.join(('https://www.hotels.com/ho', str(data_hotel.get('hotel_id'))))
        name_hotel = data_hotel.get('name_hotel')
        result += ''.join(('Название отеля: ', f'<a class="link" href="{link}">{name_hotel}</a>'))
        result += ''.join(('\nАдрес отеля: ', data_hotel.get('adress')))
        result += ''.join(('\nРасстояние до центра города: ', data_hotel.get('distance_to_center')))
        result += ''.join(('\nСтоимость за сутки проживания (без НДС): ', data_hotel.get('price')))
        result += ''.join(('\nОбщая стоимость проживания с учетом все сборов: ', data_hotel.get('full_price')))

        bot.send_message(chat_id, result, parse_mode='html', disable_web_page_preview=True,)
        photo = data_hotel.get('photo_hotel')
        if photo:
            media = []
            for reference in photo:
                media.append(InputMediaPhoto(reference))
            bot.send_media_group(chat_id, media)


def write_in_history(user_id, command, hotels):
    """ записываем запрос в исотрию """

    dt = datetime.now()
    data_request = {'user_id': user_id,
                    'command': command,
                    'data_time': dt.strftime("%x %X"),
                    'hotels': hotels}
    db.add_note_in_history(data_request)


def history(message: Message) -> None:
    """ хендлер для вывода истории запросов в чат пользователя """

    logger.info(f"Пользователь с id {message.from_user.id} ввел комманду: ('/history')")
    db.show_history(message.from_user.id)


def invalid_command(message):
    bot.reply_to(message, 'Такой команды нет, воспользуйтесь командой /help для получения свединий о боте')
    bot.send_message(message.chat.id, 'wfwfwfw<a class="link" href="modules.html">Modules</a>', parse_mode='html')


def register_handlers():
    """ Регистратор всех хендлеров """
    bot.register_message_handler(help_handler, commands=['help', 'start'])
    bot.register_message_handler(lowprice, commands=['lowprice'])
    bot.register_message_handler(highprice, commands=['highprice'])
    bot.register_message_handler(bestdeal, commands=['bestdeal'])
    bot.register_message_handler(history, commands=['history'])
    bot.register_message_handler(invalid_command, func=lambda m: True)
