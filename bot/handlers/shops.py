from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from bot.database import async_session, User, Shop, Transaction
from bot.keyboards import shops_kb, main_menu_kb
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import asyncio

router = Router()

SHOPS_INFO = {
    0: {"name": "Boshlang'ich Ombor", "price": 0, "days": 2, "tasks": 3, "income": 5000},
    1: {"name": "eBay Global", "price": 110000, "days": 60, "tasks": 3, "income": 5000},
    2: {"name": "Walmart Direct", "price": 210000, "days": 60, "tasks": 3, "income": 9000},
    3: {"name": "Amazon Prime", "price": 350000, "days": 60, "tasks": 3, "income": 12500}
}

@router.message(F.text == "🏬 Do'konlar")
async def shops_menu(message: Message):
    text = "🏬 XALQARO MARKETPLACE DO'KONLARI VA TARIFLAR\n\n" \
           "🆓 Boshlang'ich Ombor (Sinov paketi)\n💵 Ijara narxi: Bepul (0 UZS)\n⏳ Ijara muddati: 2 kun\n📦 Kunlik buyurtmalar: 3 ta\n❗️ Eslatma: Ombor daromadini yechib olib bo'lmaydi, u pullik do'kon xaridida chegirma (bonus) sifatida ishlatiladi.\n\n" \
           "1️⃣ eBay Global (Tier-1)\n💵 Ijara narxi: 110,000 UZS\n⏳ Ijara muddati: 60 kun\n📦 Kunlik buyurtmalar: 3 ta\n\n" \
           "2️⃣ Walmart Direct (Tier-2)\n💵 Ijara narxi: 210,000 UZS\n⏳ Ijara muddati: 60 kun\n📦 Kunlik buyurtmalar: 3 ta\n\n" \
           "3️⃣ Amazon Prime (Tier-3 VIP)\n💵 Ijara narxi: 350,000 UZS\n⏳ Ijara muddati: 60 kun\n📦 Kunlik buyurtmalar: 3 ta"
    await message.answer(text, reply_markup=shops_kb())

async def buy_shop(user_id: int, tier: int, message: Message):
    shop_info = SHOPS_INFO[tier]
    price = shop_info["price"]
    
    async with async_session() as session:
        user = await session.get(User, user_id)
        
        result = await session.execute(select(Shop).where(and_(Shop.user_id == user_id, Shop.is_active == True)))
        active_shops = result.scalars().all()
        
        if len(active_shops) >= 3:
            await message.answer("❌ Maksimal limit: Sizda allaqachon 3 ta faol do'kon bor.")
            return
            
        if tier == 0:
            result = await session.execute(select(Shop).where(and_(Shop.user_id == user_id, Shop.tier == 0)))
            if result.scalars().first():
                await message.answer("❌ Bu paket har bir mijozga faqat 1 marta beriladi.")
                return
                
        # Deduct balance
        if user.balance < price:
            await message.answer(f"❌ Mablag' yetishmovchiligi. Do'kon narxi {price:,.0f} UZS. Hisobingizni to'ldiring.", reply_markup=main_menu_kb())
            return
            
        user.balance -= price
        
        end_date = add_working_days(datetime.utcnow(), shop_info["days"])
        new_shop = Shop(user_id=user_id, tier=tier, end_date=end_date)
        session.add(new_shop)
        
        # Add transaction
        trans = Transaction(user_id=user_id, type="shop_buy", amount=-price, status="completed")
        session.add(trans)
        
        await session.commit()
        
        # Referral bonus logic
        await process_referral_bonus(user, price, tier, session, message.bot, shop_info['name'])
        
    await message.answer(f"✅ Muvaffaqiyatli xarid! Siz {shop_info['name']} do'konini ijaraga oldingiz.", reply_markup=main_menu_kb())

async def process_referral_bonus(user: User, price: float, tier: int, session, bot, shop_name: str):
    if price <= 0:
        return
        
    if not user.referrer_id:
        return
        
    user_link = f"<a href='tg://user?id={user.id}'>{user.fullname}</a>"
    if user.username:
        user_link = f"<a href='tg://user?id={user.id}'>@{user.username}</a>"
        
    # Check if returning (downgrade logic)
    result = await session.execute(select(Shop).where(and_(Shop.user_id == user.id, Shop.tier == tier)))
    is_returning = len(result.scalars().all()) > 1
    
    percents = {
        'A': 4.0 if is_returning else 7.0,
        'B': 1.5 if is_returning else 3.0,
        'C': 0.5
    }
    
    # Process A
    ref_a = await session.get(User, user.referrer_id)
    if ref_a:
        bonus_a = (price * percents['A']) / 100
        ref_a.balance += bonus_a
        ref_a.ref_profit_total += bonus_a
        session.add(Transaction(user_id=ref_a.id, type="ref_bonus", amount=bonus_a, status="completed"))
        try:
            await bot.send_message(ref_a.id, f"🎉 Sizning A-darajali a'zoingiz {user_link} <b>{shop_name}</b> do'konini xarid qildi!\nSiz {bonus_a:,.0f} UZS daromadga ega bo'ldingiz. Ishonch uchun rahmat!")
        except Exception:
            pass
        
        # Process B
        if ref_a.referrer_id:
            ref_b = await session.get(User, ref_a.referrer_id)
            if ref_b:
                bonus_b = (price * percents['B']) / 100
                ref_b.balance += bonus_b
                ref_b.ref_profit_total += bonus_b
                session.add(Transaction(user_id=ref_b.id, type="ref_bonus", amount=bonus_b, status="completed"))
                try:
                    await bot.send_message(ref_b.id, f"🎉 Sizning B-darajali a'zoingiz {user_link} <b>{shop_name}</b> do'konini xarid qildi!\nSiz {bonus_b:,.0f} UZS daromadga ega bo'ldingiz. Ishonch uchun rahmat!")
                except Exception:
                    pass
                
                # Process C
                if ref_b.referrer_id:
                    ref_c = await session.get(User, ref_b.referrer_id)
                    if ref_c:
                        bonus_c = (price * percents['C']) / 100
                        ref_c.balance += bonus_c
                        ref_c.ref_profit_total += bonus_c
                        session.add(Transaction(user_id=ref_c.id, type="ref_bonus", amount=bonus_c, status="completed"))
                        try:
                            await bot.send_message(ref_c.id, f"🎉 Sizning C-darajali a'zoingiz {user_link} <b>{shop_name}</b> do'konini xarid qildi!\nSiz {bonus_c:,.0f} UZS daromadga ega bo'ldingiz. Ishonch uchun rahmat!")
                        except Exception:
                            pass
                        
    await session.commit()

@router.message(F.text == "🎁 Boshlang'ich Ombor (Bepul)")
async def buy_ombor(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Ijaraga olishni tasdiqlash", callback_data="buy_shop_0")]])
    text = "🎁 <b>Boshlang'ich Ombor (Sinov paketi)</b>\n\n" \
           "💵 <b>Ijara narxi:</b> Bepul (0 UZS)\n" \
           "⏳ <b>Ijara muddati:</b> 2 kun\n" \
           "📦 <b>Kunlik buyurtmalar:</b> 3 ta\n" \
           "💰 <b>1 ta buyurtma daromadi:</b> ~1,300 - 1,650 UZS\n" \
           "📈 <b>Kunlik daromad diapazoni:</b> ~4,000 - 5,000 UZS\n" \
           "💎 <b>Jami daromad (2 kunda):</b> ~8,000 - 10,000 UZS\n\n" \
           "💡 <b>Daromad diapazoni nima?</b> Har bir buyurtmadagi foyda xaridorning ehtiyoji va tovar turiga qarab ko'rsatilgan oraliqda tasodifiy beriladi.\n\n" \
           "❗️ <b>Eslatma:</b> Ombor daromadini yechib olib bo'lmaydi, u pullik do'kon xaridida chegirma (bonus) sifatida ishlatiladi.\n\n" \
           "Ushbu paketni faollashtirishni tasdiqlaysizmi?"
    await message.answer(text, reply_markup=kb)

@router.message(F.text == "🛒 eBay Global (110,000 UZS)")
async def buy_ebay(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Ijaraga olishni tasdiqlash", callback_data="buy_shop_1")]])
    text = "🛒 <b>eBay Global (Tier-1)</b>\n\n" \
           "💵 <b>Ijara narxi:</b> 110,000 UZS\n" \
           "⏳ <b>Ijara muddati:</b> 60 kun\n" \
           "🛡 <b>Depozit qoplanishi:</b> ~22 kun\n" \
           "📦 <b>Kunlik buyurtmalar:</b> 3 ta\n" \
           "💰 <b>1 ta buyurtma daromadi:</b> ~1,500 - 1,900 UZS\n" \
           "📈 <b>Kunlik daromad diapazoni:</b> ~4,500 - 5,700 UZS\n" \
           "💎 <b>Jami daromad (60 kunda):</b> ~270,000 - 342,000 UZS\n\n" \
           "💡 <b>Daromad diapazoni nima?</b> Har bir buyurtmadagi foyda ko'rsatilgan oraliqda tasodifiy beriladi.\n\n" \
           "Ushbu do'konni ijaraga olishni tasdiqlaysizmi?"
    await message.answer(text, reply_markup=kb)

@router.message(F.text == "🛒 Walmart Direct (210,000 UZS)")
async def buy_walmart(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Ijaraga olishni tasdiqlash", callback_data="buy_shop_2")]])
    text = "🛒 <b>Walmart Direct (Tier-2)</b>\n\n" \
           "💵 <b>Ijara narxi:</b> 210,000 UZS\n" \
           "⏳ <b>Ijara muddati:</b> 60 kun\n" \
           "🛡 <b>Depozit qoplanishi:</b> ~23 kun\n" \
           "📦 <b>Kunlik buyurtmalar:</b> 3 ta\n" \
           "💰 <b>1 ta buyurtma daromadi:</b> ~2,700 - 3,250 UZS\n" \
           "📈 <b>Kunlik daromad diapazoni:</b> ~8,100 - 9,750 UZS\n" \
           "💎 <b>Jami daromad (60 kunda):</b> ~486,000 - 585,000 UZS\n\n" \
           "💡 <b>Daromad diapazoni nima?</b> Har bir buyurtmadagi foyda ko'rsatilgan oraliqda tasodifiy beriladi.\n\n" \
           "Ushbu do'konni ijaraga olishni tasdiqlaysizmi?"
    await message.answer(text, reply_markup=kb)

@router.message(F.text == "🛒 Amazon Prime (350,000 UZS)")
async def buy_amazon(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Ijaraga olishni tasdiqlash", callback_data="buy_shop_3")]])
    text = "🛒 <b>Amazon Prime (Tier-3 VIP)</b>\n\n" \
           "💵 <b>Ijara narxi:</b> 350,000 UZS\n" \
           "⏳ <b>Ijara muddati:</b> 60 kun\n" \
           "🛡 <b>Depozit qoplanishi:</b> ~28 kun\n" \
           "📦 <b>Kunlik buyurtmalar:</b> 3 ta\n" \
           "💰 <b>1 ta buyurtma daromadi:</b> ~3,700 - 4,450 UZS\n" \
           "📈 <b>Kunlik daromad diapazoni:</b> ~11,100 - 13,350 UZS\n" \
           "💎 <b>Jami daromad (60 kunda):</b> ~666,000 - 801,000 UZS\n\n" \
           "💡 <b>Daromad diapazoni nima?</b> Har bir buyurtmadagi foyda ko'rsatilgan oraliqda tasodifiy beriladi.\n\n" \
           "Ushbu do'konni ijaraga olishni tasdiqlaysizmi?"
    await message.answer(text, reply_markup=kb)


def add_working_days(start_date, working_days):
    current = start_date
    added = 0
    while added < working_days:
        current += timedelta(days=1)
        if current.weekday() != 6: # 6 is Sunday
            added += 1
    return current

@router.callback_query(F.data.startswith("buy_shop_"))
async def process_buy_shop(call: CallbackQuery):

    tier = int(call.data.split("_")[2])
    await call.message.delete()
    await buy_shop(call.from_user.id, tier, call.message)
