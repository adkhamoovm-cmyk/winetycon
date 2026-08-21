from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import async_session, User, Shop, Transaction, Settings
from bot.keyboards import cabinet_kb, card_type_kb, main_menu_kb, back_kb
from bot.states import Cabinet
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_
from datetime import datetime

router = Router()

@router.message(F.text == "👤 Shaxsiy Kabinet")
async def cabinet_menu(message: Message):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user:
            return
            
        result = await session.execute(select(Shop).where(and_(Shop.user_id == user.id, Shop.is_active == True)))
        shops = result.scalars().all()
        
        shop_text = "🏬 FAOL DO'KONLARINGIZ\n"
        if not shops:
            shop_text += "Sizda faol do'konlar yo'q.\n"
        else:
            for idx, shop in enumerate(shops, 1):
                rem_days = (shop.end_date - shop.start_date).days
                shop_name = {0: "Boshlang'ich Ombor", 1: "eBay Global", 2: "Walmart Direct", 3: "Amazon Prime"}.get(shop.tier, "Do'kon")
                shop_text += f"{idx}. {shop_name} — Qolgan muddat: {rem_days} kun\n"
                
        username_text = f"💬 Username: @{user.username}\n" if user.username else ""
        
        total_balance = user.balance
        
        ref_text = "Hamkorsiz"
        if user.referrer_id:
            ref_user = await session.get(User, user.referrer_id)
            if ref_user:
                ref_name = f"@{ref_user.username}" if ref_user.username else ref_user.fullname
                ref_id_str = str(ref_user.id)[-4:]
                ref_text = f"{ref_name} (***{ref_id_str})"
        
        card_text = ""
        if user.card_number:
            card_text = f"💳 <b>ULANGAN KARTA MA'LUMOTLARI</b>\nKarta turi: {user.card_type}\nRaqami: <code>{user.card_number[:4]} **** **** {user.card_number[-4:]}</code>\nEgasi: {user.card_name}\n\n"
        else:
            card_text = f"💳 <b>ULANGAN KARTA MA'LUMOTLARI</b>\n❌ Karta ulanmagan. Iltimos, pul yechishdan oldin hamyonni sozlang.\n\n"

        text = f"👤 <b>FOYDALANUVCHI MA'LUMOTLARI</b>\n🆔 ID raqam: {user.id}\n👤 F.I.Sh: {user.fullname}\n📞 Telefon: {user.phone}\n🤝 Taklif qilgan: {ref_text}\n{username_text}\n" \
               f"💰 <b>BALANS VA STATISTIKA</b>\n💵 Asosiy balans: {total_balance:,.0f} UZS\n📥 Jami kiritilgan depozit: {user.deposit_total:,.0f} UZS\n📤 Jami yechib olingan: {user.withdraw_total:,.0f} UZS\n\n" \
               f"{card_text}" \
               f"{shop_text}"
               
    await message.answer(text, reply_markup=cabinet_kb())

@router.message(F.text == "📜 Tarix")
async def history_menu(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Transaction).where(Transaction.user_id == message.from_user.id).order_by(Transaction.created_at.desc()).limit(20))
        trans = result.scalars().all()
        
        if not trans:
            await message.answer("Tarix bo'sh.")
            return
            
        text = "📜 Oxirgi 20 ta amaliyot:\n\n"
        for t in trans:
            sign = "+" if t.amount > 0 else ""
            text += f"🔹 {t.type} | {sign}{t.amount:,.0f} UZS | {t.status}\n"
            
    await message.answer(text)

@router.message(F.text == "💳 Hamyonni sozlash")
async def setup_wallet(message: Message, state: FSMContext):
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user.card_number:
            await message.answer(f"Sizning kartangiz allaqachon ulangan:\n{user.card_name}\n{user.card_type}\n{user.card_number}\n\nO'zgartirish uchun admin bilan bog'laning.")
            return
            
    await message.answer("Iltimos, kartadagi Ism va Familiyangizni kiriting:", reply_markup=back_kb())
    await state.set_state(Cabinet.waiting_card_name)

@router.message(StateFilter(Cabinet.waiting_card_name))
async def card_name(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return
        
    if len(message.text) > 60:
        await message.answer("Ism juda uzun, qisqaroq kiriting:")
        return
    await state.update_data(card_name=message.text)
    await message.answer("Karta turini tanlang:", reply_markup=card_type_kb())
    await state.set_state(Cabinet.waiting_card_type)

@router.message(StateFilter(Cabinet.waiting_card_type))
async def card_type(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return
        
    await state.update_data(card_type=message.text.replace("🟢 ", "").replace("🟠 ", ""))
    await message.answer("16 xonali karta raqamingizni kiriting (bo'shliqlarsiz):", reply_markup=back_kb())
    await state.set_state(Cabinet.waiting_card_number)

@router.message(StateFilter(Cabinet.waiting_card_number))
async def card_number(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return
        
    if len(message.text) != 16 or not message.text.isdigit():
        await message.answer("Noto'g'ri format. 16 xonali raqam kiriting:")
        return
        
    data = await state.get_data()
    name = data.get("card_name")
    ctype = data.get("card_type")
    cnum = message.text
    
    await state.update_data(card_number=cnum)
    
    text = f"⚠️ Ma'lumotlaringiz to'g'rimi? Iltimos, ko'zdan kechiring.\n\nEgasi: {name}\nKarta: {ctype}\nRaqam: {cnum}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash va Saqlash", callback_data="save_card")],
        [InlineKeyboardButton(text="🔄 Qaytadan kiritish", callback_data="retry_card")]
    ])
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "save_card")
async def save_card(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        user = await session.get(User, call.from_user.id)
        user.card_name = data.get("card_name")
        user.card_type = data.get("card_type")
        user.card_number = data.get("card_number")
        await session.commit()
        
    await call.message.delete()
    await call.message.answer("✅ Kartangiz saqlandi!", reply_markup=cabinet_kb())
    await state.clear()

@router.callback_query(F.data == "retry_card")
async def retry_card(call: CallbackQuery, state: FSMContext):
    await call.message.delete()
    await call.message.answer("Iltimos, kartadagi Ism va Familiyangizni kiriting:", reply_markup=back_kb())
    await state.set_state(Cabinet.waiting_card_name)
