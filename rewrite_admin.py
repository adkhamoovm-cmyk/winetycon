import re

# 1. UPDATE STATES.PY
with open('bot/states.py', 'a') as f:
    f.write('''
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
''')

# 2. UPDATE KEYBOARDS.PY
with open('bot/keyboards.py', 'a') as f:
    f.write('''
def admin_main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Foydalanuvchini boshqarish")],
            [KeyboardButton(text="📊 Statistika"), KeyboardButton(text="📢 Xabar yuborish")],
            [KeyboardButton(text="⚙️ Tizim sozlamalari")],
            [KeyboardButton(text="⬅️ Asosiy menyu")]
        ], resize_keyboard=True
    )

def admin_cancel_kb():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔙 Admin menyu")]], resize_keyboard=True)

def admin_user_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💰 Balansni o'zgartirish"), KeyboardButton(text="🎁 Ombor balansni o'zgartirish")],
            [KeyboardButton(text="💳 Kartani o'zgartirish"), KeyboardButton(text="📜 Tarixini ko'rish")],
            [KeyboardButton(text="🚫 Ban / Unban")],
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
''')

# 3. UPDATE ADMIN.PY
admin_code = '''from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from bot.database import async_session, User, Transaction, Settings, PromoCode
from bot.config import ADMIN_IDS
from bot.states import Admin
from bot.keyboards import admin_main_kb, admin_cancel_kb, admin_user_kb, admin_settings_kb, main_menu_kb
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_, func
import asyncio

router = Router()

@router.message(Command("admin"))
async def admin_panel(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await state.clear()
    await message.answer("🛡 BOSH BOSHQARUV PANELI", reply_markup=admin_main_kb())

@router.message(F.text == "🔙 Admin menyu")
async def back_to_admin(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await state.clear()
    await message.answer("🛡 BOSH BOSHQARUV PANELI", reply_markup=admin_main_kb())

# --- SETTINGS ---
@router.message(F.text == "⚙️ Tizim sozlamalari")
async def admin_settings_menu(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        text = f"⚙️ TIZIM SOZLAMALARI\\n\\n💳 Karta: {settings.admin_card_number if settings else 'Kiritilmagan'}\\n" \\
               f"👤 Karta egasi: {settings.admin_card_name if settings else 'Kiritilmagan'}\\n" \\
               f"🚧 Texnik xizmat: {'YOQILGAN (On)' if settings and settings.is_maintenance else 'O`CHIRILGAN (Off)'}"
    await message.answer(text, reply_markup=admin_settings_kb())

@router.message(F.text == "🚧 Texnik xizmat holatini o'zgartirish")
async def toggle_maintenance(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        settings.is_maintenance = not settings.is_maintenance
        status = "YOQILDI" if settings.is_maintenance else "O'CHIRILDI"
        await session.commit()
    await message.answer(f"✅ Texnik xizmat holati {status}.", reply_markup=admin_settings_kb())

@router.message(F.text == "💳 Admin kartasini o'zgartirish")
async def change_admin_card_btn(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Yangi karta raqamini kiriting (16 ta raqam):", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_admin_card)

@router.message(Admin.waiting_for_admin_card)
async def save_admin_card(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        settings.admin_card_number = message.text
        await session.commit()
    await message.answer("✅ Karta raqami yangilandi.", reply_markup=admin_settings_kb())
    await state.clear()
    
@router.message(F.text == "👤 Admin ismini o'zgartirish")
async def change_admin_name_btn(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Yangi karta egasining ism va familiyasini kiriting:", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_admin_name)

@router.message(Admin.waiting_for_admin_name)
async def save_admin_name(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        settings.admin_card_name = message.text
        await session.commit()
    await message.answer("✅ Karta egasining ismi yangilandi.", reply_markup=admin_settings_kb())
    await state.clear()

# --- STATISTICS ---
@router.message(F.text == "📊 Statistika")
async def show_statistics(message: Message):
    if message.from_user.id not in ADMIN_IDS: return
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        deposits = await session.scalar(select(func.sum(Transaction.amount)).where(and_(Transaction.type == 'deposit', Transaction.status == 'completed')))
        withdraws = await session.scalar(select(func.sum(Transaction.amount)).where(and_(Transaction.type == 'withdraw', Transaction.status == 'completed')))
        
    deposits = deposits or 0
    withdraws = withdraws or 0
    
    text = f"📊 UMUMIY STATISTIKA\\n\\n👥 Jami foydalanuvchilar: {users_count} ta\\n" \\
           f"📥 Jami kiritilgan depozit: {deposits:,.0f} UZS\\n" \\
           f"📤 Jami yechilgan mablag': {abs(withdraws):,.0f} UZS\\n"
    await message.answer(text, reply_markup=admin_main_kb())

# --- BROADCAST ---
@router.message(F.text == "📢 Xabar yuborish")
async def broadcast_btn(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Barcha foydalanuvchilarga yuboriladigan xabarni kiriting (yoki rasm/video bilan yuboring):", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.broadcast)

@router.message(Admin.broadcast)
async def process_broadcast(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    if message.from_user.id not in ADMIN_IDS: return
    
    async with async_session() as session:
        users = (await session.execute(select(User.id))).scalars().all()
        
    await message.answer(f"{len(users)} ta foydalanuvchiga xabar yuborilmoqda...", reply_markup=admin_main_kb())
    await state.clear()
    
    success = 0
    for uid in users:
        try:
            await message.copy_to(uid)
            success += 1
        except:
            pass
        await asyncio.sleep(0.05)
        
    await message.answer(f"Xabar yuborish yakunlandi. {success} ta foydalanuvchiga muvaffaqiyatli yetib bordi.")

# --- USER MANAGEMENT ---
@router.message(F.text == "👥 Foydalanuvchini boshqarish")
async def manage_user_btn(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS: return
    await message.answer("Qidirilayotgan foydalanuvchining ID raqamini kiriting:", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_user_id)

@router.message(Admin.waiting_for_user_id)
async def search_user(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
        
    if not message.text.isdigit():
        await message.answer("Faqat ID raqamini kiriting:")
        return
        
    target_id = int(message.text)
    async with async_session() as session:
        user = await session.get(User, target_id)
        if not user:
            await message.answer("Bunday ID dagi foydalanuvchi topilmadi. Qaytadan kiriting:")
            return
            
        await state.update_data(target_user_id=target_id)
        
        banned_str = "🚫 HA" if user.is_banned else "✅ YO'Q"
        text = f"👤 Foydalanuvchi ma'lumotlari:\\n\\n" \\
               f"ID: {user.id}\\n" \\
               f"Ism: {user.fullname}\\n" \\
               f"Username: @{user.username}\\n" \\
               f"Telefon: {user.phone}\\n" \\
               f"Balans: {user.balance:,.0f} UZS\\n" \\
               f"Ombor balans: {user.ombor_balance:,.0f} UZS\\n" \\
               f"Kiritgan depoziti: {user.deposit_total:,.0f} UZS\\n" \\
               f"Yechgan puli: {user.withdraw_total:,.0f} UZS\\n" \\
               f"Karta turi: {user.card_type}\\n" \\
               f"Karta raqami: {user.card_number}\\n" \\
               f"Karta egasi: {user.card_name}\\n" \\
               f"Ban qilinganmi: {banned_str}\\n\\n" \\
               f"Harakatni tanlang:"
               
        await message.answer(text, reply_markup=admin_user_kb())
        await state.set_state(Admin.user_menu)

@router.message(Admin.user_menu, F.text == "🚫 Ban / Unban")
async def ban_unban_user(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_user_id")
    async with async_session() as session:
        user = await session.get(User, target_id)
        user.is_banned = not user.is_banned
        status = "Bloklandi" if user.is_banned else "Blokdan chiqarildi"
        await session.commit()
    await message.answer(f"✅ Foydalanuvchi {status}!", reply_markup=admin_user_kb())

@router.message(Admin.user_menu, F.text == "💰 Balansni o'zgartirish")
async def edit_balance_btn(message: Message, state: FSMContext):
    await message.answer("Yangi asosiy balans miqdorini kiriting (raqamlarda):", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_balance)

@router.message(Admin.waiting_for_balance)
async def save_balance(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    if not message.text.replace(".", "").isdigit():
        await message.answer("Raqam kiriting:")
        return
    data = await state.get_data()
    async with async_session() as session:
        user = await session.get(User, data.get("target_user_id"))
        user.balance = float(message.text)
        await session.commit()
    await message.answer("✅ Balans yangilandi.", reply_markup=admin_user_kb())
    await state.set_state(Admin.user_menu)

@router.message(Admin.user_menu, F.text == "🎁 Ombor balansni o'zgartirish")
async def edit_ombor_btn(message: Message, state: FSMContext):
    await message.answer("Yangi ombor balansi miqdorini kiriting:", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_ombor)

@router.message(Admin.waiting_for_ombor)
async def save_ombor(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    if not message.text.replace(".", "").isdigit():
        await message.answer("Raqam kiriting:")
        return
    data = await state.get_data()
    async with async_session() as session:
        user = await session.get(User, data.get("target_user_id"))
        user.ombor_balance = float(message.text)
        await session.commit()
    await message.answer("✅ Ombor balansi yangilandi.", reply_markup=admin_user_kb())
    await state.set_state(Admin.user_menu)

@router.message(Admin.user_menu, F.text == "💳 Kartani o'zgartirish")
async def edit_card_btn(message: Message, state: FSMContext):
    await message.answer("Foydalanuvchining yangi 16 xonali karta raqamini kiriting:", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_card_number)
    
@router.message(Admin.waiting_for_card_number)
async def save_user_card_num(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    if not message.text.isdigit() or len(message.text) != 16:
        await message.answer("Noto'g'ri format! 16 ta raqam kiriting:")
        return
    data = await state.get_data()
    async with async_session() as session:
        user = await session.get(User, data.get("target_user_id"))
        user.card_number = message.text
        await session.commit()
    await message.answer("✅ Karta raqami yangilandi. Endi karta egasining ismini kiriting:", reply_markup=admin_cancel_kb())
    await state.set_state(Admin.waiting_for_card_name)

@router.message(Admin.waiting_for_card_name)
async def save_user_card_name(message: Message, state: FSMContext):
    if message.text == "🔙 Admin menyu":
        await back_to_admin(message, state)
        return
    data = await state.get_data()
    async with async_session() as session:
        user = await session.get(User, data.get("target_user_id"))
        user.card_name = message.text
        await session.commit()
    await message.answer("✅ Karta egasi ismi yangilandi.", reply_markup=admin_user_kb())
    await state.set_state(Admin.user_menu)

@router.message(Admin.user_menu, F.text == "📜 Tarixini ko'rish")
async def user_history_btn(message: Message, state: FSMContext):
    data = await state.get_data()
    target_id = data.get("target_user_id")
    async with async_session() as session:
        result = await session.execute(select(Transaction).where(Transaction.user_id == target_id).order_by(Transaction.created_at.desc()).limit(15))
        trans = result.scalars().all()
        
        if not trans:
            await message.answer("Tarix bo'sh.", reply_markup=admin_user_kb())
            return
            
        text = "📜 Oxirgi 15 ta tranzaksiya:\\n\\n"
        for t in trans:
            sign = "+" if t.amount > 0 else ""
            text += f"🔹 {t.type} | {sign}{t.amount:,.0f} | {t.status}\\n"
            
    await message.answer(text, reply_markup=admin_user_kb())


# Keeping original transaction approval handlers from inline buttons:
@router.callback_query(F.data.startswith("dep_app_"))
async def approve_dep(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    trans_id = int(call.data.split("_")[2])
    
    async with async_session() as session:
        trans = await session.get(Transaction, trans_id)
        if trans and trans.status == "pending":
            trans.status = "completed"
            user = await session.get(User, trans.user_id)
            user.balance += trans.amount
            user.deposit_total += trans.amount
            await session.commit()
            
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.reply("✅ Depozit tasdiqlandi.")
            try:
                await call.bot.send_message(user.id, f"✅ Tabriklaymiz! Sizning {trans.amount:,.0f} UZS depozitingiz tasdiqlandi va hisobingizga tushdi.")
            except:
                pass

@router.callback_query(F.data.startswith("dep_rej_"))
async def reject_dep(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    trans_id = int(call.data.split("_")[2])
    
    async with async_session() as session:
        trans = await session.get(Transaction, trans_id)
        if trans and trans.status == "pending":
            trans.status = "rejected"
            await session.commit()
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.reply("❌ Depozit rad etildi.")
            try:
                await call.bot.send_message(trans.user_id, "❌ Sizning depozit arizangiz rad etildi. Iltimos, admin bilan bog'laning.")
            except:
                pass

@router.callback_query(F.data.startswith("with_app_"))
async def approve_with(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    trans_id = int(call.data.split("_")[2])
    
    async with async_session() as session:
        trans = await session.get(Transaction, trans_id)
        if trans and trans.status == "pending":
            trans.status = "completed"
            user = await session.get(User, trans.user_id)
            user.withdraw_total += abs(trans.amount)
            await session.commit()
            
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.reply("✅ Pul yechish tasdiqlandi.")
            try:
                await call.bot.send_message(user.id, f"🎉 Muvaffaqiyatli to'lov!\\nSizning pul yechish arizangiz muvaffaqiyatli bajarildi!")
            except:
                pass

@router.callback_query(F.data.startswith("with_rej_"))
async def reject_with(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS: return
    trans_id = int(call.data.split("_")[2])
    
    async with async_session() as session:
        trans = await session.get(Transaction, trans_id)
        if trans and trans.status == "pending":
            trans.status = "rejected"
            user = await session.get(User, trans.user_id)
            user.balance += abs(trans.amount)
            await session.commit()
            
            await call.message.edit_reply_markup(reply_markup=None)
            await call.message.reply("❌ Pul yechish rad etildi, summa qaytarildi.")
            try:
                await call.bot.send_message(user.id, "❌ Sizning pul yechish arizangiz rad etildi va mablag' balansingizga qaytarildi.")
            except:
                pass
'''

with open('bot/handlers/admin.py', 'w') as f:
    f.write(admin_code)

