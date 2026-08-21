from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from bot.database import async_session, User, Transaction, Settings
from bot.keyboards import cabinet_kb, main_menu_kb, back_kb
from bot.states import Cabinet
from bot.config import ADMIN_IDS
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

router = Router()

@router.message(F.text == "📥 Hisobni to'ldirish")
async def deposit_menu(message: Message, state: FSMContext):
    await message.answer("Iltimos, to'ldirish miqdorini kiriting (Minimal miqdor: 100,000 so'm):", reply_markup=back_kb())
    await state.set_state(Cabinet.waiting_deposit_amount)

@router.message(StateFilter(Cabinet.waiting_deposit_amount))
async def deposit_amount(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return

    if not message.text.isdigit():
        await message.answer("Faqat raqam kiriting.")
        return
        
    if len(message.text) > 15:
        await message.answer("Summa juda katta.")
        return
        
    amount = int(message.text)
    if amount < 100000:
        await message.answer("Minimal miqdor 100,000 so'm.")
        return
        
    await state.update_data(dep_amount=amount)
    
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        card = settings.admin_card_number if settings else "8600123456789012"
        name = settings.admin_card_name if settings else "Admin"
        
    text = f"🧾 <b>DEPOZIT ARIZASI</b>\n" \
           f"💰 Kiritilgan summa: <b>{amount:,.0f} UZS</b>\n\n" \
           f"💳 To'lovni quyidagi karta raqamiga o'tkazing:\n" \
           f"Karta: <code>{card}</code>\n" \
           f"Egasi: {name}\n\n" \
           f"⚠️ <b>DIQQAT, MUHIM QOIDALAR!</b>\n" \
           f"Siz hisobni to'ldirmoqdasiz. Iltimos, aynan o'zingiz kiritgan miqdorni yuboring.\n" \
           f"🚫 Soxta chek yubormang! Har bir rasm qo'lda tekshiriladi.\n\n" \
           f"To'lovni amalga oshirgach, to'lov chekini (rasm/skrinshot) shu yerga yuboring:"
    await message.answer(text, parse_mode="HTML")
    await state.set_state(Cabinet.waiting_deposit_receipt)

@router.message(StateFilter(Cabinet.waiting_deposit_receipt), F.photo)
async def deposit_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    amount = data.get("dep_amount")
    photo_id = message.photo[-1].file_id
    
    async with async_session() as session:
        trans = Transaction(user_id=message.from_user.id, type="deposit", amount=amount, status="pending", photo_id=photo_id)
        session.add(trans)
        await session.flush()
        trans_id = trans.id
        await session.commit()
        
    await message.answer("✅ Arizangiz qabul qilindi! Moliya bo'limi tomonidan tekshirilmoqda.", reply_markup=main_menu_kb())
    await state.clear()
    
    # Notify Admin
    admin_text = f"📥 Yangi depozit arizasi\nID: {trans_id}\nUser ID: {message.from_user.id}\nSumma: {amount:,.0f} UZS"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"dep_app_{trans_id}"),
         InlineKeyboardButton(text="❌ Rad etish", callback_data=f"dep_rej_{trans_id}")]
    ])
    for admin_id in ADMIN_IDS:
        try:
            await message.bot.send_photo(admin_id, photo=photo_id, caption=admin_text, reply_markup=kb)
        except:
            pass

@router.message(StateFilter(Cabinet.waiting_deposit_receipt))
async def deposit_receipt_invalid(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return
    await message.answer("Iltimos, rasm shaklida to'lov chekini yuboring yoki 'Asosiy menyu' ga qayting.")

@router.message(F.text == "📤 Pul yechish")
async def withdraw_menu(message: Message, state: FSMContext):
    uzb_time = datetime.utcnow() + timedelta(hours=5)
    if uzb_time.weekday() == 6:
        await message.answer("❌ Yakshanba kuni pul yechib bo'lmaydi.")
        return
        
    hour = uzb_time.hour
    if not (10 <= hour < 17):
        await message.answer("❌ Pul yechish faqat 10:00 dan 17:00 gacha ishlaydi.")
        return
        
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if not user.card_number:
            await message.answer("Avval kartangizni ulang.", reply_markup=cabinet_kb())
            return
            
    await message.answer("Yechib olmoqchi bo'lgan summani kiriting (Minimal: 15,000 UZS):", reply_markup=back_kb())
    await state.set_state(Cabinet.waiting_withdraw_amount)

@router.message(StateFilter(Cabinet.waiting_withdraw_amount))
async def withdraw_amount(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Bekor qilindi.", reply_markup=main_menu_kb())
        return

    if not message.text.isdigit():
        return
        
    if len(message.text) > 15:
        await message.answer("Summa juda katta.")
        return
        
    amount = int(message.text)
    if amount < 15000:
        await message.answer("Minimal: 15,000 UZS")
        return
        
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user.balance < amount:
            await message.answer(f"Balansingizda yetarli mablag' yo'q. Sizning balansingiz: {user.balance:,.0f} UZS")
            return
            
    fee = amount * 0.11
    final = amount - fee
    
    await state.update_data(with_amount=amount, with_final=final)
    
    text = f"📤 Pul yechish arizasi\nKiritilgan summa: {amount:,.0f} UZS\nTizim komissiyasi (11%): {fee:,.0f} UZS\n💳 Kartangizga tushadigan sof summa: {final:,.0f} UZS\n\nUshbu summani yechishni tasdiqlaysizmi?"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="with_confirm"),
         InlineKeyboardButton(text="❌ Bekor qilish", callback_data="with_cancel")]
    ])
    await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "with_confirm")
async def withdraw_confirm(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amount = data.get("with_amount")
    final = data.get("with_final")
    
    if not amount or not final:
        await call.answer("❌ Xato: Ariza bekor qilingan yoki muddati o'tgan.", show_alert=True)
        await call.message.delete()
        return
        
    async with async_session() as session:
        user = await session.get(User, call.from_user.id)
        if user.balance < amount:
            await call.answer("Balans yetarli emas", show_alert=True)
            return
            
        user.balance -= amount
        
        trans = Transaction(user_id=user.id, type="withdraw", amount=-amount, status="pending")
        session.add(trans)
        await session.flush()
        trans_id = trans.id
        await session.commit()
        
        text = f"⏳ Yechish arizasi ko'rib chiqilmoqda...\nQabul qiluvchi: {user.card_name}\nKarta: {user.card_number}\nSumma: {final:,.0f} UZS\n\nArizangiz moliya bo'limiga yuborildi."
        await call.message.edit_text(text)
        await state.clear()
        
        admin_text = f"📤 Pul yechish arizasi\nID: {trans_id}\nUser ID: {user.id}\nIsm: {user.card_name}\nKarta: {user.card_number}\nKiritilgan: {amount:,.0f}\nTo'lanadi: {final:,.0f} UZS"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ To'landi", callback_data=f"with_app_{trans_id}"),
             InlineKeyboardButton(text="❌ Rad etish", callback_data=f"with_rej_{trans_id}")]
        ])
        for admin_id in ADMIN_IDS:
            try:
                await call.bot.send_message(admin_id, admin_text, reply_markup=kb)
            except:
                pass
                
@router.callback_query(F.data == "with_cancel")
async def withdraw_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.delete()
    await call.message.answer("Bekor qilindi.", reply_markup=cabinet_kb())
