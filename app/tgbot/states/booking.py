from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    MAIN_MENU = State()
    ENTER_NAME = State()
    SELECT_DATE = State()
    SELECT_START_TIME = State()
    SELECT_END_TIME = State()
    ENTER_PHONE = State()
    CANCEL_BOOKING_DATE = State()
    CANCEL_BOOKING_TIME = State()
    CANCEL_BOOKING_NAME = State()
