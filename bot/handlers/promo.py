from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from bot.database import async_session, User, PromoCode, UserPromo
from bot.keyboards import main_menu_kb, back_kb
from bot.config import ADMIN_IDS
from bot.states import Promo
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_
import asyncio

router = Router()

@router.message(F.text == "🧧 Qizil xalta")
async def promo_menu(message: Message, state: FSMContext):
    await message.answer("🧧 SIRLI QIZIL XALTA BO'LIMIGA XUSH KELIBSIZ!\n\nSiz maxsus sirli xalta promo kodini topdingizmi? Unday bo'lsa, kodni quyidagi xabarga yozib yuboring va darhol balansingizga bonus pulni oling!\n\n✍️ Kodni kiriting:", reply_markup=back_kb())
    await state.set_state(Promo.waiting_code)

@router.message(StateFilter(Promo.waiting_code))
async def check_promo(message: Message, state: FSMContext):
    if message.text == "⬅️ Asosiy menyu":
        await state.clear()
        await message.answer("Asosiy menyuga qaytdingiz.", reply_markup=main_menu_kb())
        return
        
    code = message.text.strip()
    msg = await message.answer("⏳ Kod tizimdan tekshirilmoqda... Bazadagi faolligi aniqlanmoqda...")
    await asyncio.sleep(1.5)
    
    async with async_session() as session:
        result = await session.execute(select(PromoCode).where(and_(PromoCode.code == code, PromoCode.is_active == True)))
        promo = result.scalars().first()
        
        if not promo or promo.used_count >= promo.limit:
            await msg.delete()
            await message.answer("❌ Afsuski, xatolik yuz berdi! Kiritilgan kod mavjud emas, muddati tugagan yoki foydalanish limiti to'lgan.", reply_markup=main_menu_kb())
            await state.clear()
            return
            
        result = await session.execute(select(UserPromo).where(and_(UserPromo.user_id == message.from_user.id, UserPromo.promo_id == promo.id)))
        if result.scalars().first():
            await msg.delete()
            await message.answer("❌ Siz ushbu kodni allaqachon ishlatib bo'lgansiz.", reply_markup=main_menu_kb())
            await state.clear()
            return
            
        user = await session.get(User, message.from_user.id)
        user.balance += promo.amount
        promo.used_count += 1
        
        session.add(UserPromo(user_id=message.from_user.id, promo_id=promo.id))
        await session.commit()
        

        await msg.delete()
        await message.answer(f"🎉 Tabriklaymiz! Sirli xalta ochildi! Kodingiz muvaffaqiyatli qabul qilindi. Balansingiz +{promo.amount:,.0f} UZS ga ko'paydi!", reply_markup=main_menu_kb())
        await state.clear()
        
        # Adminlarga xabar yuborish
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id, 
                    f"🎁 <b>Yangi promokoddan foydalanish!</b>\n\n"
                    f"👤 Mijoz: <a href='tg://user?id={user.id}'>{user.fullname}</a> (ID: {user.id})\n"
                    f"🎟 Promokod: <b>{promo.code}</b>\n"
                    f"💰 Olingan summa: {promo.amount:,.0f} UZS\n"
                    f"📊 Limit holati: {promo.used_count}/{promo.limit}",
                    parse_mode="HTML"
                )
            except:
                pass

