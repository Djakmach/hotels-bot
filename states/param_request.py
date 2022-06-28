from telebot.handler_backends import State, StatesGroup


class UserParamRequestState(StatesGroup):
    command = State()
    city = State()
    check_in = State()
    check_out = State()

    price_min = State()
    price_max = State()
    distance_for_centre = State()

    amount_hotels = State()
    is_photo_needed = State()
    amount_photo = State()