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

    mess = 'Я бот предназначенный для поиска отелей\n\nВы можете управлять мной, ' \
           'отправив следующие команды:\n\n/help\n/lowprice\n/highprice\n/bestdeal\n/history'
    bot.send_message(message.chat.id, mess)


def lowprice(message: Message) -> None:
    """ Начало сценария lowprice"""
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.city, chat_id=message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['command'] = 'lowprice'


def highprice(message: Message) -> None:
    """ Начало сценария highprice"""
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.city, chat_id=message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['command'] = 'highprice'


def bestdeal(message: Message) -> None:
    """ Начало сценария bestdeal"""
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.city, chat_id=message.chat.id)
    bot.send_message(message.from_user.id, 'Введите город')
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['command'] = 'bestdeal'


@bot.message_handler(state="*", commands=['cancel'])
def exist_state(message: Message):
    """ Cancel state """
    bot.send_message(message.chat.id, "Your state was cancelled.")
    bot.delete_state(message.from_user.id, message.chat.id)


@bot.message_handler(state=UserParamRequestState.city)
def get_city(message: Message) -> None:
    """ получаем город"""
    cur_date = date.today()
    bot.send_message(message.from_user.id, 'Ввыберите дату заезда', reply_markup=calendar_days(cur_date))
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.check_in, chat_id=message.chat.id)

    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['city'] = message.text


@bot.message_handler(state=UserParamRequestState.check_in)
def get_check_in(message: Message) -> None:
    """ получаем дату заезда """
    cur_date = date.today()
    bot.send_message(message.from_user.id, 'Ввыберите дату выезда', reply_markup=calendar_days(cur_date))
    bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.check_out, chat_id=message.chat.id)

    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['check_in'] = message.text


@bot.message_handler(state=UserParamRequestState.check_out)
def get_check_out(message: Message) -> None:
    """
    получаем дату выезда, и далее в зависимости от сценария просим ввести минимальную цену либо сразу переходим на
    ввод количества отелей
    """
    with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
        data['check_out'] = message.text
        if data.get('command') == 'bestdeal':
            bot.send_message(message.from_user.id, 'Введите минимальную цену (руб)')
            bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.price_min,
                          chat_id=message.chat.id)
        else:
            bot.send_message(message.from_user.id, 'Введите кол-во отелей (не больше 10)')
            bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.amount_hotels,
                          chat_id=message.chat.id)


@bot.message_handler(state=UserParamRequestState.price_min)
def get_price_min(message: Message) -> None:
    """ получаем минимальную цену """
    try:
        price_min = int(message.text)
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['price_min'] = price_min
        bot.send_message(message.from_user.id, 'Введите максимальную цену (руб)')
        bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.price_max,
                     chat_id=message.chat.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода')


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
                bot.send_message(message.from_user.id, 'Введите максимальное расстояние от центра города (км)')
                bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.distance_for_centre,
                             chat_id=message.chat.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода')


@bot.message_handler(state=UserParamRequestState.distance_for_centre)
def getting_distance_for_centre(message: Message):
    """ получаем максимальное расстояние от центра города """
    try:
        max_distance = int(message.text)
        if max_distance < 0:
            raise ValueError
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['max_distance'] = max_distance
        bot.send_message(message.from_user.id, 'Введите кол-во отелей (не больше 10)')
        bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.amount_hotels,
                      chat_id=message.chat.id)
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода')


@bot.message_handler(state=UserParamRequestState.amount_hotels)
def get_amount_hotels(message: Message) -> None:
    """ получаем количество отелей которое нужно вывести """
    try:
        amount_hotels = int(message.text)
        if 1 <= amount_hotels <= 10:
            with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
                data['amount_hotels'] = amount_hotels
                logger.info(f'amount_hotels = {amount_hotels}')
            bot.send_message(message.from_user.id, 'Предоставить фото?')
            bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.is_photo_needed,
                          chat_id=message.chat.id)
        else:
            bot.send_message(message.from_user.id, 'Ошибка ввода')
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода')


@bot.message_handler(state=UserParamRequestState.is_photo_needed)
def get_is_photo_needed(message: Message) -> None:
    """ спрашиваем нужно ли вывести фото """
    chat_id = message.chat.id
    if message.text == 'да' or message.text == 'yes':
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['is_photo_needed'] = True
            logger.info('is_photo_needed = True')
            bot.send_message(message.from_user.id, 'Сколько вывести фотографий?')
            bot.set_state(user_id=message.from_user.id, state=UserParamRequestState.amount_photo,
                          chat_id=message.chat.id)
    elif message.text == 'нет' or message.text == 'no':
        with bot.retrieve_data(user_id=message.from_user.id, chat_id=message.chat.id) as data:
            data['is_photo_needed'] = False
            logger.info('is_photo_needed = False')
            processing_request(data, chat_id)
        bot.delete_state(message.from_user.id, message.chat.id)
    else:
        logger.info('is_photo_needed - ошибка ввода')
        bot.send_message(message.from_user.id, 'Ошибка ввода')


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
            logger.info(f'amount_photo = {amount_photo}')


            processing_request(data, chat_id)


        bot.delete_state(message.from_user.id, message.chat.id)

    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода')
        logger.info(f'amount_photo - ошибка ввода')


def processing_request(request_parameters, chat_id):
    """ начинаем процесс обработки запроса """

    hotel_information = get_information(request_parameters)
    output_information(chat_id, hotel_information)
    hotels = ', '.join([name.get('name_hotel') for name in hotel_information])
    write_in_history(request_parameters.get('command'), hotels)

def get_information(data):
    """ получаем данные об оттелях """

    logger.info(f'Параметры запроса пользователя: {data}')
    object_request = RequestHandler()
    hotel_information = object_request(**data)
    return hotel_information


def output_information(chat_id, hotel_information):
    """ выводим информацию об отелях в чат пользователю """

    if hotel_information:
        for data_hotel in hotel_information:
            result = ''
            result += ''.join(('Название отеля: ', data_hotel.get('name_hotel')))
            result += ''.join(('\nАдрес отеля: ', data_hotel.get('adress')))
            result += ''.join(('\nРасстояние до центра города: ', data_hotel.get('distance_to_center')))
            result += ''.join(('\nОбщая стоимость проживания: ', data_hotel.get('price')))
            bot.send_message(chat_id, result)
            # bot.send_message(message.from_user.id, result)
            photo = data_hotel.get('photo_hotel')
            if photo:
                media = []
                for reference in photo:
                    media.append(InputMediaPhoto(reference))
                bot.send_media_group(chat_id, media)
    else:
        bot.send_message(chat_id, 'По вашему запросу ничего не найдено')
        # bot.send_message(message.from_user.id, 'По вашему запросу ничего не найдено')


def write_in_history(command, hotels):
    """ записываем запрос в исотрию """

    dt = datetime.now()
    data_request = {'command': command,
                    'data_time': dt.strftime("%x %X"),
                    'hotels': hotels}
    db.add_note_in_history(data_request)


def history(message: Message) -> None:
    """ хендлер для вывода истории запросов в чат пользователя """

    db.show_history(message)


def register_handlers():
    bot.register_message_handler(help_handler, commands=['help'])
    bot.register_message_handler(lowprice, commands=['lowprice'])
    bot.register_message_handler(highprice, commands=['highprice'])
    bot.register_message_handler(bestdeal, commands=['bestdeal'])
    bot.register_message_handler(history, commands=['history'])

