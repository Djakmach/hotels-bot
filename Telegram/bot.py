import json

import telebot
from telebot import types

from API.Hotels_requests import RequestHandler


bot = telebot.TeleBot('5263982663:AAH8yAgYnKUVz5_XP70AQxAAru8K7SSSrDU')


param_low_price = {
        'city': 'london',
        "checkIn": '2020-01-08',
        "checkOut": "2020-01-15",
        'amount_hotels': '4',
        'photo_hotels': True,
        'amount_photo': 3
    }


@bot.message_handler(commands=['help'])
def start(message):
    mess = 'Я бот предназначенный для поиска отелей\n\nВы можете управлять мной,\
    отправив следующие команды:\n\n/help\n/lowprice'
    bot.send_message(message.chat.id, mess)


@bot.message_handler(commands=['lowprice'])
def lowprice(message):
    bot.send_message(message.from_user.id, 'Введите город')
    bot.register_next_step_handler(message, getting_city)


def getting_city(message):
    global param_low_price
    city = message.text.lower()
    param_low_price.update({'city': city})
    bot.send_message(message.from_user.id, 'Введите дату заезда')
    bot.register_next_step_handler(message, getting_check_in)


def getting_check_in(message):
    global param_low_price
    check_in = message.text
    param_low_price.update({'checkIn': check_in})
    bot.send_message(message.from_user.id, 'Введите дату выезда')
    bot.register_next_step_handler(message, getting_check_out)

def getting_check_out(message):
    global param_low_price
    check_out = message.text
    param_low_price.update({'checkOut': check_out})
    bot.send_message(message.from_user.id, 'Введите кол-во отелей (не больше 10)')
    bot.register_next_step_handler(message, getting_amount_hotels)

def getting_amount_hotels(message):
    global param_low_price
    amount_hotels = message.text
    try:
        if 1 <= int(amount_hotels) <= 10:
            param_low_price.update({'amount_hotels': amount_hotels})
        else:
            raise ValueError
    except ValueError:
        bot.send_message(message.from_user.id, 'Ошибка ввода, введите число от 1 до 10')
        bot.register_next_step_handler(message, getting_amount_hotels)
    else:
        keyboard = types.InlineKeyboardMarkup()  # наша клавиатура
        key_yes = types.InlineKeyboardButton(text='Да', callback_data='yes')
        keyboard.add(key_yes)  # добавляем кнопку в клавиатуру
        key_no = types.InlineKeyboardButton(text='Нет', callback_data='no')
        keyboard.add(key_no)
        bot.send_message(message.from_user.id, text='Предоставить фото?', reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def callback_worker(call):
    global param_low_price
    if call.data == "yes":
        param_low_price.update({'photo_hotels': True})
        bot.send_message(call.message.chat.id, 'Сколько вывести фотографий?)')
        bot.register_next_step_handler(call.message, getting_amount_photo)
    elif call.data == "no":
        param_low_price.update({'photo_hotels': False})
        get_hotels(call.message)


def getting_amount_photo(message):
    global param_low_price
    amount_photo = int(message.text)
    param_low_price.update({'amount_photo': amount_photo})
    print('получили кол-во фото')
    get_hotels(message)


def get_hotels(message):
    global param_low_price
    print(param_low_price)
    # low_price = RequestHandler()
    # data_hotels = low_price(comand='low_price', **param_low_price)
    #
    # for data_hotel in data_hotels:
    #     result = ''
    #     result += ''.join(('Название отеля: ', data_hotel.get('name_hotel')))
    #     result += ''.join(('\nАдрес отеля: ', data_hotel.get('adress')))
    #     result += ''.join(('\nРасстояние до центра города: ', data_hotel.get('distance_to_center')))
    #     result += ''.join(('\nОбщая стоимость проживания: ', str(round(data_hotel.get('price'))), 'руб'))
    #     if data_hotel.get('photo_hotel'):
    #         result += ''.join(('\n', data_hotel.get('photo_hotel')[0]))
    #     bot.send_message(message.from_user.id, result)






bot.polling(none_stop=True, )
