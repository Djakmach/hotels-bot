from datetime import datetime, date

from telebot.types import InputMediaPhoto, Message
from loguru import logger


from create_bot import bot
from states.param_request import UserParamRequestState
from keyboards.inlinekeyboards import calendar_days
from API.Hotels_requests import RequestHandler
from DataBase.db_for_history import db


class BaseHandler:

    command = None

    param_request = {
        'city': 'london',
        "checkIn": '2020-01-08',
        "checkOut": "2020-01-15",
        'amount_hotels': '4',
        'is_photo_needed': True,
        'amount_photo': 3
    }

    def __call__(self, message: Message) -> None:
        bot.send_message(message.chat.id, 'Введите город')
        bot.register_next_step_handler(message, self.getting_city)

    def getting_city(self, message):
        city = message.text.lower()
        self.param_request.update({'city': city})
        cur_date = date.today()
        bot.send_message(message.from_user.id, 'Выбирете дату заезда', reply_markup=calendar_days(cur_date))
        # TODO register_next_step_handler жидает от МЕНЯ ввода сообщения, а моя клавиатура выводит сама сообщение из-за
        #  этого пока я в ручную не ввиду он не будет дальше идти, как это сделать?
        bot.register_next_step_handler(message, self.getting_check_in)

    def getting_check_in(self, message):
        check_in = message.text
        self.param_request.update({'checkIn': check_in})
        cur_date = date.today()
        bot.send_message(message.from_user.id, 'Выбирете дату выезда', reply_markup=calendar_days(cur_date))
        bot.register_next_step_handler(message, self.getting_check_out)

    def getting_check_out(self, message):
        check_out = message.text
        self.param_request.update({'checkOut': check_out})
        bot.send_message(message.from_user.id, 'Введите кол-во отелей (не больше 10)')
        bot.register_next_step_handler(message, self.getting_amount_hotels)

    def getting_amount_hotels(self, message):
        amount_hotels = message.text
        try:
            if 1 <= int(amount_hotels) <= 10:
                self.param_request.update({'amount_hotels': amount_hotels})
                bot.send_message(message.from_user.id, 'Предоставить фото?')
                bot.register_next_step_handler(message, self.getting_photo_hotels)
            else:
                raise ValueError
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода, введите число от 1 до 10')
            bot.register_next_step_handler(message, self.getting_amount_hotels)

    def getting_photo_hotels(self, message):
        answer = message.text
        try:
            if answer == 'да':
                self.param_request.update({'photo_hotels': True})
                bot.send_message(message.from_user.id, 'Сколько вывести фотографий?')
                bot.register_next_step_handler(message, self.getting_amount_photo)
            elif answer == 'нет':
                self.param_request.update({'photo_hotels': False})
                self.get_hotels(message)
            else:
                raise ValueError
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода, введите "да" или "нет"')
            bot.register_next_step_handler(message, self.getting_photo_hotels)

    def getting_amount_photo(self, message):
        try:
            amount_photo = int(message.text)
            self.param_request.update({'amount_photo': amount_photo})
            self.get_hotels(message)
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода, повторите ввод')
            bot.register_next_step_handler(message, self.getting_amount_photo)

    def get_data(self):
        logger.info(f'Параметры запроса пользователя: {self.param_request}')
        object_request = RequestHandler()
        data_hotels = object_request(command=self.command, **self.param_request)

        return data_hotels

    def history(self, data_hotels):
        dt = datetime.now()
        data_request = {'command': self.command,
                        'data_time': dt.strftime("%x %X"),
                        'hotels': ', '.join([name.get('name_hotel') for name in data_hotels])}
        db.add_note_in_history(data_request)

    def get_hotels(self, message):
        data_hotels = self.get_data()
        if data_hotels:
            for data_hotel in data_hotels:
                result = ''
                result += ''.join(('Название отеля: ', data_hotel.get('name_hotel')))
                result += ''.join(('\nАдрес отеля: ', data_hotel.get('adress')))
                result += ''.join(('\nРасстояние до центра города: ', data_hotel.get('distance_to_center')))
                result += ''.join(('\nОбщая стоимость проживания: ', data_hotel.get('price')))
                bot.send_message(message.from_user.id, result)
                photo = data_hotel.get('photo_hotel')
                if photo:
                    media = []
                    for reference in photo:
                        media.append(InputMediaPhoto(reference))
                    bot.send_media_group(message.chat.id, media)
            self.history(data_hotels)
        else:
            bot.send_message(message.from_user.id, 'По вашему запросу ничего не найдено')


class Help:
    def __call__(self, message: Message):
        mess = 'Я бот предназначенный для поиска отелей\n\nВы можете управлять мной, ' \
               'отправив следующие команды:\n\n/help\n/lowprice\n/highprice\n/bestdeal\n/history'
        bot.send_message(message.chat.id, mess)


class LowPrice(BaseHandler):
    command = 'low_price'



class HighPrice(BaseHandler):
    command = 'high_price'


class BestDeal(BaseHandler):
    param_request = {
        'city': 'london',
        'priceMin': 500,
        'priceMax': 10000,
        "checkIn": '2020-01-08',
        "checkOut": "2020-01-15",
        'max_distance': 2,
        'amount_hotels': '3',
        'is_photo_needed': True,
        'amount_photo': 3
    }
    command = 'best_deal'

    def getting_check_out(self, message: Message):
        check_out = message.text
        self.param_request.update({'checkOut': check_out})
        bot.send_message(message.from_user.id, 'Введите минимальную цену (руб)')
        bot.register_next_step_handler(message, self.getting_price_min)

    def getting_price_min(self, message: Message):
        try:
            price_min = int(message.text)
            self.param_request.update({'priceMin': price_min})
            bot.send_message(message.from_user.id, 'Введите максимальную цену (руб)')
            bot.register_next_step_handler(message, self.getting_price_max)
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода, повторите ввод')
            bot.register_next_step_handler(message, self.getting_price_min)

    def getting_price_max(self, message: Message):
        try:
            price_max = int(message.text)
            if price_max < self.param_request.get('priceMin'):
                bot.send_message(message.from_user.id, 'Максимальная цена не должна быть меньше минимальной')
                raise ValueError
            self.param_request.update({'priceMax': price_max})
            bot.send_message(message.from_user.id, 'Введите максимальное расстояние от центра города (км)')
            bot.register_next_step_handler(message, self.getting_distance_for_centre)
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода, повторите ввод')
            bot.register_next_step_handler(message, self.getting_price_max)

    def getting_distance_for_centre(self, message: Message):
        try:
            max_distance = int(message.text)
            if max_distance < 0:
                raise ValueError
            self.param_request.update({'max_distance': max_distance})
            bot.send_message(message.from_user.id, 'Введите кол-во отелей (не больше 10)')
            bot.register_next_step_handler(message, self.getting_amount_hotels)
        except ValueError:
            bot.send_message(message.from_user.id, 'Ошибка ввода, повторите ввод')
            bot.register_next_step_handler(message, self.getting_distance_for_centre)


class History:
    def __call__(self, message: Message):
        db.show_history(message)


def register_handlers():
    bot.register_message_handler(Help(), commands=['help', 'start'])
    bot.register_message_handler(LowPrice(), commands=['lowprice'])
    bot.register_message_handler(HighPrice(), commands=['highprice'])
    bot.register_message_handler(BestDeal(), commands=['bestdeal'])
    bot.register_message_handler(History(), commands=['history'])
