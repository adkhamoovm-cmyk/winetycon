from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 BUYURTMALAR / VAZIFALAR"), KeyboardButton(text="🏬 Do'konlar")],
            [KeyboardButton(text="🌐 Hamkorlik"), KeyboardButton(text="👤 Shaxsiy Kabinet")],
            [KeyboardButton(text="🏢 Biz haqimizda"), KeyboardButton(text="🧧 Qizil xalta")],
            [KeyboardButton(text="ℹ️ Yordam / FAQ")]
        ], resize_keyboard=True
    )

def contact_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Telefon raqamni yuborish", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )

def tos_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Qoidalarga roziman")]],
        resize_keyboard=True, one_time_keyboard=True
    )

def sub_kb(link: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤝 Guruhga o'tish", url=link)],
        [InlineKeyboardButton(text="➕ Guruhga a'zo bo'ldim (Tasdiqlash)", callback_data="check_sub")]
    ])

def cabinet_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📥 Hisobni to'ldirish"), KeyboardButton(text="📤 Pul yechish")],
            [KeyboardButton(text="💳 Hamyonni sozlash"), KeyboardButton(text="📜 Tarix")],
            [KeyboardButton(text="⬅️ Asosiy menyu")]
        ], resize_keyboard=True
    )

def shops_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎁 Boshlang'ich Ombor (Bepul)")],
            [KeyboardButton(text="🛒 eBay Global (110,000 UZS)")],
            [KeyboardButton(text="🛒 Walmart Direct (210,000 UZS)")],
            [KeyboardButton(text="🛒 Amazon Prime (350,000 UZS)")],
            [KeyboardButton(text="⬅️ Asosiy menyu")]
        ], resize_keyboard=True
    )

def back_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⬅️ Asosiy menyu")]], resize_keyboard=True)

def task_packing_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="📦 Qadoqlash")]], resize_keyboard=True)

def task_shipping_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🚚 Kuryerga topshirish")]], resize_keyboard=True)

def task_next_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📦 Yana buyurtma olish")],
        [KeyboardButton(text="⬅️ Asosiy menyu")]
    ], resize_keyboard=True)

def task_review_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="⭐"), KeyboardButton(text="⭐⭐"), KeyboardButton(text="⭐⭐⭐")],
        [KeyboardButton(text="⭐⭐⭐⭐"), KeyboardButton(text="⭐⭐⭐⭐⭐")]
    ], resize_keyboard=True)
    
def card_type_kb():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="🟢 Uzcard"), KeyboardButton(text="🟠 Humo")],
        [KeyboardButton(text="⬅️ Asosiy menyu")]
    ], resize_keyboard=True)

def admin_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Foydalanuvchini boshqarish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="🎁 Promokod yaratish")],
            [KeyboardButton(text="⚙️ Tizim sozlamalari")],
            [KeyboardButton(text="⬅️ Asosiy menyu")]
        ], resize_keyboard=True
    )

def admin_cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Admin menyu")]], resize_keyboard=True)

def admin_user_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Balansni o'zgartirish"), KeyboardButton(text="🤝 Taklif qilganlar / Referallari")],
            [KeyboardButton(text="💳 Kartani o'zgartirish"), KeyboardButton(text="📜 Tarixini ko'rish")],
            [KeyboardButton(text="🚫 Ban / Unban")],
            [KeyboardButton(text="🔙 Admin menyu")]
        ], resize_keyboard=True
    )

def admin_promo_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Yangi yaratish"), KeyboardButton(text="📋 Promokodlar ro'yxati")],
            [KeyboardButton(text="🔙 Admin menyu")]
        ], resize_keyboard=True
    )

def admin_settings_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💳 Admin kartasini o'zgartirish"), KeyboardButton(text="👤 Admin ismini o'zgartirish")],
            [KeyboardButton(text="🚧 Texnik xizmat holatini o'zgartirish")],
            [KeyboardButton(text="🔙 Admin menyu")]
        ], resize_keyboard=True
    )
