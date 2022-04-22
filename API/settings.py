# параметры по умолчанию для поиска локации
URL_LOCATION = "https://hotels4.p.rapidapi.com/locations/v2/search"
QUERYSTRING_LOCATION = {"query": "new york", "locale": "ru_RU", "currency": "RUB"}



# параметры по умолчанию для поиска отелей
URL_HOTELS = "https://hotels4.p.rapidapi.com/properties/list"
QUERYSTRING_HOTELS = {
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

URL_PHOTO = "https://hotels4.p.rapidapi.com/properties/get-hotel-photos"


# общий параметр по умолчанию
HEADERS = {
    "X-RapidAPI-Host": "hotels4.p.rapidapi.com",
    # "X-RapidAPI-Key": "4235d6cca2msh50d282e49713c06p14ad2fjsn4b1f3e7e7710"
    "X-RapidAPI-Key": "abd06b8ce9msh4271b526a3040d9p1e143djsnd9e7c5b8acd3"
}