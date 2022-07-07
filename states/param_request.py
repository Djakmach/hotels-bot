from telebot.handler_backends import State, StatesGroup


class UserParamRequestState(StatesGroup):
    """ Класс опрелделяющий состояния машины в процессе ввода пользователем параметров запроса"""
    command = State()
    city = State()

    price_min = State()
    price_max = State()
    distance_for_centre = State()

    amount_hotels = State()
    is_photo_needed = State()
    amount_photo = State()
