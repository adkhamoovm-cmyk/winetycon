from aiogram.fsm.state import State, StatesGroup

class Onboarding(StatesGroup):
    waiting_for_contact = State()
    waiting_for_sub = State()

class Cabinet(StatesGroup):
    waiting_card_name = State()
    waiting_card_type = State()
    waiting_card_number = State()
    waiting_deposit_amount = State()
    waiting_deposit_receipt = State()
    waiting_withdraw_amount = State()
    
class Promo(StatesGroup):
    waiting_code = State()

class Task(StatesGroup):
    processing = State()
    packing = State()
    shipping = State()
    review = State()

class Broadcast(StatesGroup):
    waiting_for_message = State()

class Admin(StatesGroup):
    waiting_for_user_id = State()
    user_menu = State()
    waiting_for_balance = State()
    waiting_for_ombor = State()
    waiting_for_card_name = State()
    waiting_for_card_number = State()
    settings_menu = State()
    waiting_for_admin_card = State()
    waiting_for_admin_name = State()
    broadcast = State()
    
    promo_menu = State()
    waiting_for_promo_code = State()
    waiting_for_promo_amount = State()
    waiting_for_promo_limit = State()
