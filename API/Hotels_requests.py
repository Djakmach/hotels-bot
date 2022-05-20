from abc import ABC
import requests
import json
from typing import List, Optional, Dict
import re

from loguru import logger

from API import settings

logger.add('debug.log', level='DEBUG')               #что такое level?

class BaseRequest(ABC):
    """ Базовый класс всех запросов

    _dict_destination_id (dict): словарь с id городов

    Attributes:
        URL (str): url - адресс запроса
        QUERYSTRING (dict): парметры запроса
        HEADERS (dict): словарь заголовков HTTP для отправки
    """
    URL = ''
    QUERYSTRING = {}
    HEADERS = settings.HEADERS

    def get_response(self, url, querystring):
        """
        Метод для получения запроса

        :return: response
        """

        try:
            response = requests.request("GET", url=url, headers=self.HEADERS, params=querystring, timeout=10)
            if response.status_code == requests.codes.ok:
                return response
        except requests.exceptions.ReadTimeout:
            logger.debug('время ожидания запроса истекло')


class LocationRequest(BaseRequest):
    """ Клласс для запроса локации

    Attributes:
        URL (str): url - адресс запроса, берется из файла settings.py
        QUERYSTRING (dict): парметры запроса, берется из файла settings.py
        HEADERS (dict): словарь заголовков HTTP для отправки, берется из файла settings.py
    """

    URL = settings.URL_LOCATION
    QUERYSTRING = settings.QUERYSTRING_LOCATION
    _dict_destination_id = {'new york': '1506246', 'london': '549499', 'paris': "504261"}


    def get_location(self, city) -> Optional[str]:
        """
        Метод для получения id города

        :param city: город

        :return: destination_id - id города
        :rtype destination_id: str
        """
        if city in self._dict_destination_id:
            destination_id = self._dict_destination_id.get(city)
        else:
            self.QUERYSTRING.update({"query": city})
            response = self.get_response(self.URL, self.QUERYSTRING)
            pattern_destination = r'(?<="CITY_GROUP",).+?[\]]'
            find = re.search(pattern_destination, response.text)
            if find:
                data = json.loads(f"{{{find[0]}}}")
                destination_id = data["entities"][0]["destinationId"]
                self._dict_destination_id.update({city: destination_id})
            else:
                logger.exception('нет данных')
                return
        logger.info(f'получили id города: {destination_id}')
        return destination_id

    def __call__(self, city):
        return self.get_location(city)


class BaseRequestsHotels(BaseRequest):
    """
    Базовый класс запросов отелей

    Args:
        URL (str): url - адресс запроса, берется из файла settings.py
        QUERYSTRING (dict): парметры запроса, берется из файла settings.py
        HEADERS (dict): словарь заголовков HTTP для отправки, берется из файла settings.py
        hotels_deal (list): будущий список отелей, выводимых по текущему запросу

    """
    def __init__(self):
        self.URL = settings.URL_HOTELS
        self.QUERYSTRING = settings.QUERYSTRING_HOTELS
        self.hotels_deal = []

    @staticmethod
    def location_request(city: str):
        """
        Метод для поиска id города

        :param city: город
        :return: destination_id
        :rtype: str
        """
        search_destination_id = LocationRequest()
        destination_id = search_destination_id(city)
        if destination_id:
            return destination_id

    def photo_requests(self, hotel_id: str, amount_photo: int) -> Optional[List[str]]:
        """
        Метод для получения фотографий отеля

        :param hotel_id: id отеля
        :param amount_photo: кол-во необходимых фотографий данного отеля
        :return: photo_list
        :rtype: list
        """
        photo_list = []
        URL_PHOTO = settings.URL_PHOTO
        querystring = {"id": hotel_id}
        response_photo = self.get_response(URL_PHOTO, querystring)

        pattern_photo = r'(?<=,"hotelImages":).+?(?=,"roomImages)'
        find = re.search(pattern_photo, response_photo.text)
        if find:
            hotel_photos_json = json.loads(f"{find.group(0)}")

            counter = 0
            for data_photo in hotel_photos_json:

                photo_hotel = data_photo["baseUrl"].replace('{size}', 'z')
                photo_list.append(photo_hotel)
                counter += 1
                if counter >= amount_photo:
                    break

            return photo_list
        else:
            logger.info('фотограйий нет')
            return

    @staticmethod
    def _get_address(address_data: dict) -> str:

        """
        Метод для получения адресса отеля, в удобном представлении для пользователя

        :param address_data: словарь с данными об адресе
        :rtype address_data: dict

        :return: address
        :rtype address: str
        """
        address = None
        country_name = address_data.get("countryName")
        if country_name:
            address = country_name
        region = address_data.get("region")
        if region:
            if address:
                address = ', '.join((address, region))
            else:
                address = region
        street_address = address_data.get("streetAddress")
        if street_address:
            if address:
                address = ', '.join((address, street_address))
            else:
                address = street_address
        extended_address = address_data.get("extendedAddress")
        if extended_address:
            if address:
                address = ', '.join((address, extended_address))
            else:
                address = extended_address
        return address

    def update_param(self, **kwargs):
        destination_id = self.location_request(kwargs.get('city'))
        self.QUERYSTRING.update({"destinationId": destination_id,
                                 "checkIn": kwargs.get('checkIn'),
                                 "checkOut": kwargs.get('checkOut')})

    def request_hotels(self):
        response_hotels = self.get_response(self.URL, self.QUERYSTRING)
        pattern_hotels = r'(?<=,"results":).+?(?=,"pagination)'
        find = re.search(pattern_hotels, response_hotels.text)
        if find:
            hotels_json = json.loads(f"{find.group(0)}")
            return hotels_json
        else:
            return None

    def converter_data_hotels(self, hotel: dict, need_photo, amount_photo=1):
        hotel_id = hotel.get("id")
        name_hotel = hotel.get("name")
        address = hotel.get('address')
        if address:
            address = self._get_address(address)
        distance_to_center = hotel["landmarks"][0]["distance"]
        price = hotel.get('ratePlan')["price"]["current"]

        converted_hotel = {
            'hotel_id': hotel_id,
            'name_hotel': name_hotel,
            'adress': address,
            'distance_to_center': distance_to_center,
            'price': price,
        }

        if need_photo:
            photo_hotel = self.photo_requests(hotel_id, amount_photo)
            converted_hotel.update({'photo_hotel': photo_hotel})
            logger.info('фотограйий получены')

        return converted_hotel

    def _get_hotels(self, **kwargs) -> List[dict]:
        """
        Метод для получения отелей удовлетворяющих условию запроса пользователя

        Keyword Args:
            'city' (str): город поиска
            'checkIn' (str): дата заезда
            'checkOut' (str): дата отъезда
            'amount_hotels' (str): кол-во отелей
            'photo_hotels' (bool): надо ли показать фото
            'amount_photo' (int): кол-во фото отеля
        """
        self.update_param(**kwargs)
        self.QUERYSTRING.update({"pageSize": kwargs.get('amount_hotels')})

        hotels_json = self.request_hotels()

        for data_hotel in hotels_json:
            converted_hotel = self.converter_data_hotels(data_hotel, kwargs.get('photo_hotels'),
                                                         kwargs.get('amount_photo'))

            self.hotels_deal.append(converted_hotel)

        logger.info('данные об отелях получены успешно')
        return self.hotels_deal

    def __call__(self, **kwargs):
        return self._get_hotels(**kwargs)


class LowPriceRequest(BaseRequestsHotels):
    """
    Класс реализующий запрос отелей по самой низкой цене. Родитель: BaseRequestsHotels
    """
    def __init__(self):
        super().__init__()
        self.QUERYSTRING.update({"sortOrder": "PRICE"})


class HighPriceRequest(BaseRequestsHotels):
    """
        Класс реализующий запрос отелей по самой высокой цене. Родитель: BaseRequestsHotels
    """
    def __init__(self):
        super().__init__()
        self.QUERYSTRING.update({"sortOrder": "PRICE_HIGHEST_FIRST"})


class BestDealRequest(BaseRequestsHotels):
    """
        Класс реализующий запрос отелей по лучшему предложению. Родитель: BaseRequestsHotels
    """
    def __init__(self):
        super().__init__()
        self.QUERYSTRING.update({"sortOrder": "DISTANCE_FROM_LANDMARK", "landmarkIds": "City center"})

    @staticmethod
    def _check_distance_to_center(max_distance, distance: str) -> bool:
        """ Метод для проверки дистанции, подходит ли отель по параметру "расстояние до центра"

        :param max_distance: максимальное расстояние до центра которое удовлетворяет запросу пользователя
        :return: True если расстояние меньше или равно, False если расстояние больше допустимого
        """
        distance = float(distance.split()[0].replace(',', '.'))
        if distance <= max_distance:
            return True
        else:
            return False

    def _get_hotels(self, **kwargs):
        """
        Переопределенный метод для получения отелей удовлетворяющих условию запроса пользователя

           Keyword Args:
            'city' (str): город поиска
            'priceMin' (float): минимальная цена
            'priceMax' (float): максимальная цена
            'checkIn' (str): дата заезда
            'checkOut' (str): дата отъезда
            'max_distance' (float): максимальная удаленность от центра
            'amount_hotels' (str): кол-во отелей
            'photo_hotels' (bool): надо ли показать фото
            'amount_photo' (int): кол-во фото отеля
        """
        self.update_param(**kwargs)
        self.QUERYSTRING.update({"priceMin": kwargs.get('priceMin'),
                                 "priceMax": kwargs.get('priceMax'),
                                 "pageSize": "25"})
        amount_hotels = int(kwargs.get('amount_hotels'))

        hotels_json = self.request_hotels()
        if hotels_json:
            for data_hotel in hotels_json:

                distance_to_center = data_hotel["landmarks"][0]["distance"]
                if self._check_distance_to_center(kwargs.get('max_distance'), distance_to_center):
                    converted_hotel = self.converter_data_hotels(data_hotel, kwargs.get('photo_hotels'),
                                                                 kwargs.get('amount_photo'))

                    self.hotels_deal.append(converted_hotel)

                    if len(self.hotels_deal) >= amount_hotels:
                        break

            logger.info('данные об отелях получены успешно')
            return self.hotels_deal
        else:
            logger.info('По запросу ничего не найдено')


class RequestHandler:
    _COMMANDS = {
        'low_price': LowPriceRequest,
        'high_price': HighPriceRequest,
        'best_deal': BestDealRequest,
    }

    def __call__(self, command: str = 'low_price', **kwargs):
        object_request = self._COMMANDS.get(command)()
        return object_request(**kwargs)




# if __name__ == '__main__':

    # low_price = RequestHandler()
    # param_low_price = {
    #     'city': 'london',
    #     "checkIn": '2022-04-27',
    #     "checkOut": "2022-04-28",
    #     'amount_hotels': '2',
    #     'photo_hotels': False,
    #     'amount_photo': 3
    # }
    # result = low_price(command='low_price', **param_low_price)
    # with open('low.json', 'w') as file:
    #     file.write(json.dumps(result, indent=4))
    #
    #
    # high_price = RequestHandler()
    # param_high_price = {
    #         'city': 'london',
    #         "checkIn": '2022-04-27',
    #         "checkOut": "2022-04-28",
    #         'amount_hotels': '2',
    #         'photo_hotels': False,
    #         'amount_photo': 3
    #     }
    # result = high_price(command='high_price', **param_high_price)
    # with open('high.json', 'w') as file:
    #     file.write(json.dumps(result, indent=4))
    #
    #
    # best_deal = RequestHandler()
    # param_best_deal = {
    #     'city': 'london', 'priceMin': 500, 'priceMax': 10000, "checkIn": '2020-01-08', "checkOut": "2020-01-15",
    #     'max_distance': 2, 'amount_hotels': '3', 'photo_hotels': True, 'amount_photo': 3
    # }
    # result = best_deal(command='best_deal', **param_best_deal)
    # with open('best_deal.json', 'w') as file:
    #     file.write(json.dumps(result, indent=4))






# {'new york': '1506246'}
# {'london': '549499'}
# {'paris': "504261"}
