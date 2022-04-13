from abc import ABC
import requests
import json
from typing import List

import settings


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
    _dict_destination_id = {}

    def _get_response(self):
        """
        Метод для получения запроса

        :return: response
        """
        response = requests.request("GET", self.URL, headers=self.HEADERS, params=self.QUERYSTRING)
        return response


class LocationRequest(BaseRequest):
    """ Клласс для запроса локации

    Attributes:
        URL (str): url - адресс запроса, берется из файла settings.py
        QUERYSTRING (dict): парметры запроса, берется из файла settings.py
        HEADERS (dict): словарь заголовков HTTP для отправки, берется из файла settings.py
    """

    URL = settings.URL_LOCATION
    QUERYSTRING = settings.QUERYSTRING_LOCATION

    def get_location(self, city) -> str:
        """
        Метод для получения id города

        :param city: город

        :return: destination_id - id города
        :rtype destination_id: str
        """
        if city in self._dict_destination_id:
            return self._dict_destination_id.get(city)
        else:
            with open('destination_id.txt', 'r') as file_id:
                destinations_id = json.load(file_id)
                self._dict_destination_id.update(destinations_id)
                for name_city, id in destinations_id.items():
                    if name_city == city:
                        destination_id = id
                        self._dict_destination_id.update({city: id})
                        break
                else:
                    self.QUERYSTRING.update({"query": city})
                    response = self._get_response()
                    data = json.loads(response.text)
                    destination_id = data["suggestions"][0]["entities"][0]["destinationId"]
                    self._dict_destination_id.update({city: destination_id})

            with open('destination_id.txt', 'w') as file_id:
                json.dump(self._dict_destination_id, file_id)

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
    def location_request(city):
        """
        Метод для поиска id города

        :param city: город
        :return: destination_id
        :rtype: str
        """
        search_destination_id = LocationRequest()
        destination_id = search_destination_id(city)
        return destination_id

    def photo_requests(self, hotel_id: str, amount_photo: int) -> List[str]:
        """
        Метод для получения фотографий отеля

        :param hotel_id: id отеля
        :param amount_photo: кол-во необходимых фотографий данного отеля
        :return: photo_list
        :rtype: list
        """
        photo_list = []
        url_photo = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"
        querystring = {"id": hotel_id}
        response_photo = requests.request("GET", url_photo, headers=self.HEADERS, params=querystring)
        hotel_photos_json = json.loads(response_photo.text)

        counter = 0
        for data_photo in hotel_photos_json["hotelImages"]:
            photo_hotel = data_photo["baseUrl"].replace('{size}', 'z')
            photo_list.append(photo_hotel)
            counter += 1
            if counter >= amount_photo:
                break
        return photo_list

    @staticmethod
    def _get_address(address_data: dict) -> str:   # нужен self или нет

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
        destination_id = self.location_request(kwargs.get('city'))
        self.QUERYSTRING.update({"destinationId": destination_id, "pageSize": kwargs.get('amount_hotels'),
                                 "checkIn": kwargs.get('checkIn'), "checkOut": kwargs.get('checkOut')})

        response = self._get_response()

        hotels_json = json.loads(response.text)

        for hotel in hotels_json["data"]["body"]["searchResults"]["results"]:
            hotel_id = hotel.get("id")
            name_hotel = hotel.get("name")
            address = hotel.get('address')
            if address:
                address = self._get_address(address)
            distance_to_center = hotel["landmarks"][0]["distance"]
            price = hotel.get('ratePlan')["price"]["exactCurrent"]

            hotel = {
                'hotel_id': hotel_id,
                'name_hotel': name_hotel,
                'adress': address,
                'distance_to_center': distance_to_center,
                'price': price,
            }

            if kwargs.get('photo_hotels'):
                photo_hotel = self.photo_requests(hotel_id, kwargs.get('amount_photo'))
                hotel.update({'photo_hotel': photo_hotel})

            self.hotels_deal.append(hotel)
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
        distance = float(distance.split()[0])
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
        destination_id = self.location_request(kwargs.get('city'))
        self.QUERYSTRING.update({"destinationId": destination_id,
                                 "priceMin": kwargs.get('priceMin'),
                                 "priceMax": kwargs.get('priceMax'),
                                 "checkIn": kwargs.get('checkIn'),
                                 "checkOut": kwargs.get('checkOut'),
                                 "pageSize": "25"}
                                )
        amount_hotels = int(kwargs.get('amount_hotels'))
        response = self._get_response()

        hotels_json = json.loads(response.text)
        with open('data_search_best_deal.json', 'w') as best_deal_file:
            json.dump(hotels_json, best_deal_file, indent=4)

        for hotel in hotels_json["data"]["body"]["searchResults"]["results"]:
            distance_to_center = hotel["landmarks"][0]["distance"]
            price = hotel.get('ratePlan')["price"]["exactCurrent"]
            if self._check_distance_to_center(kwargs.get('max_distance'), distance_to_center):
                hotel_id = hotel.get("id")
                name_hotel = hotel.get("name")
                address = hotel.get('address')
                if address:
                    address = self._get_address(address)

                hotel = {
                    'hotel_id': hotel_id,
                    'name_hotel': name_hotel,
                    'adress': address,
                    'distance_to_center': distance_to_center,
                    'price': price,
                }
                if kwargs.get('photo_hotels'):
                    photo_hotel = self.photo_requests(hotel_id, kwargs.get('amount_photo'))
                    hotel.update({'photo_hotel': photo_hotel})

                self.hotels_deal.append(hotel)
                if len(self.hotels_deal) >= amount_hotels:
                    break
        return self.hotels_deal


class RequestHandler:
    _COMMANDS = {
        'low_price': LowPriceRequest,
        'high_price': HighPriceRequest,
        'best_deal': BestDealRequest,
    }

    @classmethod
    def __call__(cls, command: str = 'low_price', **kwargs):
        object = cls._COMMANDS.get(command)()
        return object(**kwargs)


# av = LocationRequest()
# print(av('paris'))


# low_price = RequestHandler()
# param_low_price = {
#     'city': 'london', "checkIn": '2020-01-08', "checkOut": "2020-01-15", 'amount_hotels': '4', 'photo_hotels': True,
#     'amount_photo': 3
# }
# result = low_price(comand='low_price', **param_low_price)
# with open('low.json', 'w') as file:
#     file.write(json.dumps(result, indent=4))
#
#
# high_price = RequestHandler()
# param_high_price = {
#     'city': 'london', "checkIn": '2020-01-08', "checkOut": "2020-01-15", 'amount_hotels': '3', 'photo_hotels': False,
#     'amount_photo': 3
# }
# result = high_price(comand='high_price', **param_high_price)
# with open('high.json', 'w') as file:
#     file.write(json.dumps(result, indent=4))


best_deal = RequestHandler()
param_best_deal = {
    'city': 'london', 'priceMin': 500, 'priceMax': 10000, "checkIn": '2020-01-08', "checkOut": "2020-01-15",
    'max_distance': 0.7, 'amount_hotels': '3', 'photo_hotels': True, 'amount_photo': 3
}
result = best_deal(command='best_deal', **param_best_deal)
with open('best_deal.json', 'w') as file:
    file.write(json.dumps(result, indent=4))






# {'new york': '1506246'}
# {'london': '549499'}
# {'paris': "504261"}
