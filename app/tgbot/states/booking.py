from aiogram.fsm.state import State, StatesGroup

class BookingStates(StatesGroup):
    waiting_for_action = State()
    waiting_for_name = State()
    waiting_for_date = State()
    waiting_for_table_preference = State()
    waiting_for_start_time = State()
    waiting_for_end_time = State()
    waiting_for_phone = State()
    confirm_booking = State()
    
    # Для отмены брони
    select_booking_to_cancel = State()
    confirm_cancellation = State()
    waiting_for_block_day = State()
    admin_manage_bookings = State()
    admin_waiting_for_client_name = State()
    admin_waiting_for_client_phone = State() 