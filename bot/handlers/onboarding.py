from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from bot.database import async_session, User, Settings
from bot.keyboards import tos_kb, contact_kb, sub_kb, main_menu_kb
from bot.states import Onboarding
from sqlalchemy import select

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: Bot):
    await state.clear()
    if message.chat.type != 'private':
        return

    args = message.text.split()[1] if len(message.text.split()) > 1 else None
    referrer_id = None
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.split("_")[1])
        except ValueError:
            pass
            
    async with async_session() as session:
        user = await session.get(User, message.from_user.id)
        if user:
            await message.answer("Asosiy menyu", reply_markup=main_menu_kb())
            return
            
        if referrer_id and referrer_id != message.from_user.id:
            ref_user = await session.get(User, referrer_id)
            if ref_user:
                await state.update_data(referrer_id=referrer_id)
                ref_text = f"🤝 Sizni ushbu platformaga do'stingiz — <b>{ref_user.fullname}</b> taklif qildi!\n\n"
            else:
                ref_text = ""
        else:
            ref_text = ""

    text = f"👋 <b>E-Tycoon elektron tijorat simulyatoriga xush kelibsiz!</b>\n\n{ref_text}" \
           f"📜 <b>PLATFORMA QOIDALARI VA SHARTLARI</b>\n" \
           f"🔞 1. Siz 18 yoshga to'lgansiz.\n" \
           f"⚠️ 2. Barcha moliyaviy amaliyotlar o'z xohishingiz va tavakkalchiligingiz asosida amalga oshiriladi.\n" \
           f"🚫 3. Bitta shaxs tomonidan bir nechta akkaunt ochish, botdagi xatoliklardan g'arazli maqsadda foydalanish qat'iyan man etiladi va barcha akkauntlar bloklanishiga olib keladi.\n" \
           f"🕒 4. Yakshanba — dam olish kuni. Pul yechish va vazifalar bajarish to'xtatiladi.\n\n" \
           f"Tugmani bosish orqali siz yuqoridagi qoidalarga to'liq rozi ekanligingizni bildirasiz."
           
    await message.answer(text, reply_markup=tos_kb())

@router.message(F.text == "✅ Qoidalarga roziman")
async def tos_accept(message: Message, state: FSMContext):
    async with async_session() as session:
        if await session.get(User, message.from_user.id):
            await message.answer("Asosiy menyu", reply_markup=main_menu_kb())
            return
    text = "📱 Akkauntni tasdiqlash\n\nXavfsizlikni ta'minlash va hisobingizni himoyalash uchun telefon raqamingizni tizimga kiritishingiz kerak.\nIltimos, pastdagi \"📱 Telefon raqamni yuborish\" tugmasini bosing."
    await message.answer(text, reply_markup=contact_kb())
    await state.set_state(Onboarding.waiting_for_contact)

@router.message(StateFilter(Onboarding.waiting_for_contact), F.contact)
async def contact_received(message: Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        link = settings.community_link if settings else "https://t.me/ETycoon_Community"
        
    text = f"🤝 E-Tycoon hamjamiyatiga qo'shiling!\n\nLoyihamiz yangiliklari, to'lovlar isboti va boshqa ishtirokchilar bilan suhbatlashish uchun rasmiy guruhimizga a'zo bo'lishingiz shart.\n🔗 Guruhimiz: {link}"
    await message.answer(text, reply_markup=sub_kb(link))
    await state.set_state(Onboarding.waiting_for_sub)

@router.callback_query(Onboarding.waiting_for_sub, F.data == "check_sub")
async def check_sub(call: CallbackQuery, state: FSMContext, bot: Bot):
    async with async_session() as session:
        settings = await session.get(Settings, 1)
        channel_id = settings.community_id if settings and settings.community_id else "@ETycoon_Community"
        
    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=call.from_user.id)
        if member.status in ['left', 'kicked']:
            await call.answer("❌ Kechirasiz, siz guruhga a'zo bo'lmadingiz. Iltimos, a'zo bo'lib, tasdiqlash tugmasini bosing", show_alert=True)
            return
    except Exception as e:
        pass # If bot is not admin in the channel, it will fail. Ignore for now.
        
    data = await state.get_data()
    phone = data.get("phone", "")
    referrer_id = data.get("referrer_id", None)
    
    async with async_session() as session:
        existing = await session.get(User, call.from_user.id)
        if existing:
            await call.message.delete()
            await call.message.answer("Siz allaqachon ro'yxatdan o'tgansiz.", reply_markup=main_menu_kb())
            await state.clear()
            return
            
        user = User(
            id=call.from_user.id,
            fullname=call.from_user.full_name,
            username=call.from_user.username,
            phone=phone,
            referrer_id=referrer_id
        )
        session.add(user)
        await session.commit()
        
        if referrer_id:
            try:
                user_link = f"<a href='tg://user?id={call.from_user.id}'>{call.from_user.full_name}</a>"
                if call.from_user.username:
                    user_link = f"<a href='tg://user?id={call.from_user.id}'>@{call.from_user.username}</a>"
                await bot.send_message(
                    referrer_id, 
                    f"🎉 <b>Yangi a'zo qo'shildi!</b>\n\nSizda yangi a'zo ro'yxatdan o'tdi: {user_link}\nUnga yo'l ko'rsating, birgalikda E-Tycoon bilan daromad toping!"
                )
            except Exception:
                pass

    await call.message.delete()
    text = f"🎉 Akkauntingiz muvaffaqiyatli tasdiqlandi!\n\nE-Tycoon olamiga yana bir bor xush kelibsiz!\n💡 Qanday boshlayman? Tizim bo'yicha barcha savollaringizga javobni va botdan to'g'ri foydalanish bo'yicha to'liq qo'llanmani pastdagi [ ℹ️ Yordam / FAQ ] bo'limidan topishingiz mumkin.\nO'z biznesingizni boshlash uchun hoziroq [ 🏬 Do'konlar ] bo'limiga o'ting va \"Boshlang'ich Ombor\"ni bepul faollashtirib, birinchi daromadingizni ishlang!"
    
    await call.message.answer(text, reply_markup=main_menu_kb())
    await state.clear()
