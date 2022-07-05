from abc import ABC
import requests
import json
from typing import List, Optional
import re

from loguru import logger

from config_data import config

logger.add('debug.log', level='DEBUG')


class BaseRequest(ABC):
    """ Базовый класс всех запросов

    Attributes:
        url (str): url - адресс запроса
        querystring (dict): парметры запроса
        headers (dict): словарь заголовков HTTP для отправки
    """
    url = ''
    querystring = {}
    headers = {"X-RapidAPI-Host": "hotels4.p.rapidapi.com", "X-RapidAPI-Key": config.RAPID_API_KEY}

    def get_response(self, url, querystring):
        """
        Метод для получения запроса

        :return: response
        """

        try:
            response = requests.request("GET", url=url, headers=self.headers, params=querystring, timeout=10)
            if response.status_code == requests.codes.ok:
                return response
            else:
                logger.debug('по запросу ничего не найдено')
        except requests.exceptions.ReadTimeout:
            logger.debug('время ожидания запроса истекло')


class LocationRequest(BaseRequest):
    """ Клласс для запроса локации, унаследован от BaseRequest

    Attributes:
        url (str): url - адресс запроса, берется из файла settings.py
        querystring (dict): парметры запроса, берется из файла settings.py
        headers (dict): словарь заголовков HTTP для отправки, берется из файла settings.py
    """

    url = "https://hotels4.p.rapidapi.com/locations/v2/search"
    querystring = {"query": "new york", "locale": "ru_RU", "currency": "RUB"}

    def get_location(self, city) -> Optional[str]:
        """
        Метод для получения id города

        :param city: город по которому ищем id локации

        :return: destination_id - id города
        :rtype destination_id: str
        """
        self.querystring.update({"query": city})
        response = self.get_response(self.url, self.querystring)
        pattern_destination = r'(?<="CITY_GROUP",).+?[\]]'
        find = re.search(pattern_destination, response.text)
        if find:
            data = json.loads(f"{{{find[0]}}}")
            if not data["entities"]:
                logger.exception('нет данных по локации')
                return None
            destination_id = data["entities"][0]["destinationId"]
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
        url (str): url - адресс запроса, берется из файла settings.py
        querystring (dict): парметры запроса, берется из файла settings.py
        headers (dict): словарь заголовков HTTP для отправки, берется из файла settings.py
        hotels_deal (list): будущий список отелей, выводимых по текущему запросу

    """
    def __init__(self):
        self.url = "https://hotels4.p.rapidapi.com/properties/list"
        self.querystring = {
            "destinationId": "1506246",
            "pageNumber": "1",
            "pageSize": "25",
            "checkIn": "2020-01-08",
            "checkOut": "2020-01-15",
            "adults1": "1",
            "priceMin": '500',
            "priceMax": '10000',
            "sortOrder": "PRICE",
            "locale": "ru_RU",
            "currency": "RUB"
        }

        self.hotels_deal = []

    @staticmethod
    def location_request(city: str) -> Optional[str]:
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
        else:
            return

    def photo_requests(self, hotel_id: str, amount_photo: int) -> Optional[List[str]]:
        """
        Метод для получения фотографий отеля

        :param hotel_id: id отеля
        :param amount_photo: кол-во необходимых фотографий данного отеля
        :return: photos
        :rtype: list
        """
        photos = []
        url_photo = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {"id": hotel_id}
        response_photo = self.get_response(url_photo, querystring)

        pattern_photo = r'(?<=,"hotelImages":).+?(?=,"roomImages)'
        find = re.search(pattern_photo, response_photo.text)
        if find:
            hotel_photos_json = json.loads(f"{find.group(0)}")

            counter = 0
            for data_photo in hotel_photos_json:

                photo_hotel = data_photo["baseUrl"].replace('{size}', 'z')
                photos.append(photo_hotel)
                counter += 1
                if counter >= amount_photo:
                    break

            return photos
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
        """ Вводим параметры запроса пользователя для дальнейшего поиска отелей,
         причем, если по запросу локации города не найдено ничего, тогда метод возвращет False """

        destination_id = self.location_request(kwargs.get('city'))
        if destination_id:
            self.querystring.update({"destinationId": destination_id,
                                     "checkIn": kwargs.get('checkIn'),
                                     "checkOut": kwargs.get('checkOut')})
            return True
        else:
            return False

    def request_hotels(self):
        """ Метод для получения json формата данных об отелях"""
        response_hotels = self.get_response(self.url, self.querystring)
        pattern_hotels = r'(?<=,"results":).+?(?=,"pagination)'
        find = re.search(pattern_hotels, response_hotels.text)
        if find:
            hotels_json = json.loads(f"{find.group(0)}")
            return hotels_json
        else:
            return None

    def converter_data_hotels(self, hotel: dict, need_photo: bool, amount_photo: int):
        """ Метод вытягивания необходимых для нас данных об отеле"""
        hotel_id = hotel.get("id")
        name_hotel = hotel.get("name")
        address = hotel.get('address')
        if address:
            address = self._get_address(address)
        distance_to_center = hotel["landmarks"][0]["distance"]
        logger.info(f'hotel - {hotel}')

        price = hotel['ratePlan']["price"]["current"]
        logger.info(f'price - {price}')

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

    def _get_hotels(self, **kwargs) -> Optional[List[dict]]:
        """
        Метод для получения отелей удовлетворяющих условию запроса пользователя

        Keyword Args:
            'city' (str): город поиска
            'checkIn' (str): дата заезда
            'checkOut' (str): дата отъезда
            'amount_hotels' (int): кол-во отелей
            'is_photo_needed' (bool): надо ли показать фото
            'amount_photo' (int): кол-во фото отеля
        """
        if not self.update_param(**kwargs):
            return None
        self.querystring.update({"pageSize": str(kwargs.get('amount_hotels'))})

        hotels_json = self.request_hotels()

        for data_hotel in hotels_json:
            converted_hotel = self.converter_data_hotels(data_hotel, kwargs.get('is_photo_needed'),
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
        self.querystring.update({"sortOrder": "PRICE"})


class HighPriceRequest(BaseRequestsHotels):
    """
        Класс реализующий запрос отелей по самой высокой цене. Родитель: BaseRequestsHotels
    """
    def __init__(self):
        super().__init__()
        self.querystring.update({"sortOrder": "PRICE_HIGHEST_FIRST"})


class BestDealRequest(BaseRequestsHotels):
    """
        Класс реализующий запрос отелей по лучшему предложению. Родитель: BaseRequestsHotels
    """
    def __init__(self):
        super().__init__()
        self.querystring.update({"sortOrder": "DISTANCE_FROM_LANDMARK", "landmarkIds": "City center"})

    @staticmethod
    def _check_distance_to_center(max_distance: float, distance: str) -> bool:
        """ Метод для проверки дистанции, подходит ли отель по параметру "расстояние до центра"

        :param max_distance: максимальное расстояние до центра которое удовлетворяет запросу пользователя
        :return: True если расстояние меньше или равно, False если расстояние больше допустимого
        """
        distance = float(distance.split()[0].replace(',', '.'))
        if distance <= max_distance:
            return True
        else:
            return False

    def _get_hotels(self, **kwargs) -> Optional[List[dict]]:

        """
        Переопределенный метод для получения отелей удовлетворяющих условию запроса пользователя

           Keyword Args:
            'city' (str): город поиска
            'check_in' (str): дата заезда
            'check_out' (str): дата отъезда
            'price_min' (float): минимальная цена
            'price_max' (float): максимальная цена
            'max_distance' (float): максимальная удаленность от центра
            'amount_hotels' (int): кол-во отелей
            'is_photo_needed' (bool): надо ли показать фото
            'amount_photo' (int): кол-во фото отеля
        """
        if not self.update_param(**kwargs):
            return None
        self.querystring.update({"priceMin": str(kwargs.get('price_min')),
                                 "priceMax": str(kwargs.get('price_max')),
                                 "pageSize": "25"})
        amount_hotels = kwargs.get('amount_hotels')

        hotels_json = self.request_hotels()
        if hotels_json:
            for data_hotel in hotels_json:

                distance_to_center = data_hotel["landmarks"][0]["distance"]
                if self._check_distance_to_center(kwargs.get('max_distance'), distance_to_center):
                    converted_hotel = self.converter_data_hotels(data_hotel, kwargs.get('is_photo_needed'),
                                                                 kwargs.get('amount_photo'))

                    self.hotels_deal.append(converted_hotel)

                    if len(self.hotels_deal) >= amount_hotels:
                        break

            logger.info('данные об отелях получены успешно')
            return self.hotels_deal
        else:
            logger.info('По запросу ничего не найдено')


class RequestHandler:
    """ Главный класс-обработчик запроса, он напрвляет параметры введенные пользователем к нужному классу """

    _COMMANDS = {
        'lowprice': LowPriceRequest,
        'highprice': HighPriceRequest,
        'bestdeal': BestDealRequest,
    }

    @classmethod
    def __call__(cls, command: str, **kwargs):
        object_request = cls._COMMANDS.get(command)()
        return object_request(**kwargs)
