from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message
from bot.database import async_session, User, Shop, Transaction
from bot.keyboards import task_packing_kb, task_shipping_kb, task_review_kb, task_next_kb, main_menu_kb
from bot.states import Task
from aiogram.fsm.context import FSMContext
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import asyncio
import random

router = Router()

SHOPS_INCOME = {
    0: (1300, 1650),
    1: (1500, 1900),
    2: (2700, 3250),
    3: (3700, 4450)
}

def get_task_date(dt: datetime):
    return (dt + timedelta(hours=5, minutes=-30)).date()

@router.message(F.text == "📦 BUYURTMALAR / VAZIFALAR")
async def tasks_menu(message: Message, state: FSMContext):
    now_utc = datetime.utcnow()
    current_task_date = get_task_date(now_utc)
    
    if current_task_date.weekday() == 6: # Sunday
        await message.answer("❌ Yakshanba — dam olish kuni. Pul yechish va vazifalar bajarish to'xtatilgan.", reply_markup=main_menu_kb())
        return
        
    async with async_session() as session:
        result = await session.execute(select(Shop).where(and_(Shop.user_id == message.from_user.id, Shop.is_active == True)))
        shops = result.scalars().all()
        
        if not shops:
            await message.answer("❌ Sizda faol do'konlar yo'q. Iltimos do'kon xarid qiling.", reply_markup=main_menu_kb())
            return
            
        today = current_task_date
        shop_to_task = None
        total_capacity = 0
        total_done = 0
        
        for shop in shops:
            if shop.end_date < datetime.utcnow():
                shop.is_active = False
                continue
                
            if shop.last_task_date and get_task_date(shop.last_task_date) < today:
                shop.daily_tasks_done = 0
                
            total_capacity += 3
            total_done += shop.daily_tasks_done
                
            if shop.daily_tasks_done < 3 and not shop_to_task:
                shop_to_task = shop
                
        await session.commit()
        
        if not shop_to_task:
            await message.answer("❌ Siz bugungi barcha buyurtmalarni bajarib bo'lgansiz. Yangi buyurtmalar ertaga soat 00:30 da yangilanadi. Ertaga qaytib keling!", reply_markup=main_menu_kb())
            return
            
        current_task_num = total_done + 1
        await state.update_data(shop_id=shop_to_task.id, tier=shop_to_task.tier, current_task_num=current_task_num, total_capacity=total_capacity)
        
        items = [
            ("📱", "iPhone 16 Pro"), ("❄️", "Smart Konditsioner"), 
            ("💻", "MacBook Pro M3"), ("🎧", "AirPods Max"), 
            ("⌚️", "Apple Watch Ultra 2"), ("🎮", "PlayStation 5"),
            ("📷", "Sony A7 IV Kamera"), ("📺", "Samsung 4K Smart TV"),
            ("☕️", "Delonghi Qahva apparati"), ("🚗", "Avtomobil videoregistratori"),
            ("🥽", "Meta Quest 3 VR"), ("🎒", "Samsonite sayohat sumkasi"),
            ("👟", "Nike Air Jordan 1"), ("🕶", "Ray-Ban Quyosh ko'zoynagi"),
            ("🧴", "Dior Sauvage Parfyum"), ("💄", "Chanel Kosmetika to'plami"),
            ("🧹", "Dyson V15 Changyutgich"), ("🚲", "Trek Sport Velosiped")
        ]
        emoji, item_name = random.choice(items)
        
        await message.answer(emoji)
        await message.answer(f"📦 Sizning <b>{current_task_num}-chi</b> buyurtmangiz: <b>{item_name}</b>\n\nQadoqlashni boshlang!", reply_markup=task_packing_kb())
        await state.set_state(Task.packing)

@router.message(F.text == "📦 Yana buyurtma olish")
async def next_task_btn(message: Message, state: FSMContext):
    await tasks_menu(message, state)

@router.message(StateFilter(Task.packing), F.text == "📦 Qadoqlash")
async def task_packing(message: Message, state: FSMContext):
    await state.set_state(Task.processing)
    msg = await message.answer("⏳ Qadoqlanmoqda...")
    await asyncio.sleep(1.5)
    await msg.delete()
    await message.answer("Siz mahsulotni muvaffaqiyatli qadoqladingiz! Endi kuryerga topshiring.", reply_markup=task_shipping_kb())
    await state.set_state(Task.shipping)

@router.message(StateFilter(Task.shipping), F.text == "🚚 Kuryerga topshirish")
async def task_shipping(message: Message, state: FSMContext):
    await state.set_state(Task.processing)
    msg = await message.answer("🚚 Buyurtma yo'lda ketmoqda...")
    await asyncio.sleep(2)
    await msg.delete()
    await message.answer("Xaridorga yetkazib berildi! Iltimos, do'konga xaridor nomidan baho bering. Maslahat: 5-yulduzchani bosing.", reply_markup=task_review_kb())
    await state.set_state(Task.review)

@router.message(StateFilter(Task.review))
async def task_review(message: Message, state: FSMContext):
    if "⭐" not in message.text:
        return
        
    data = await state.get_data()
    shop_id = data.get("shop_id")
    tier = data.get("tier")
    current_task = data.get("current_task_num", 1)
    total_cap = data.get("total_capacity", 3)
    
    income_range = SHOPS_INCOME.get(tier, (1000, 2000))
    reward = random.randint(income_range[0], income_range[1])
    
    async with async_session() as session:
        shop = await session.get(Shop, shop_id)
        user = await session.get(User, message.from_user.id)
        
        if shop and shop.daily_tasks_done < 3:
            shop.daily_tasks_done += 1
            shop.last_task_date = datetime.utcnow()
            
            # Add all rewards directly to main balance for simplicity
            user.balance += reward
                
            trans = Transaction(user_id=user.id, type="task", amount=reward, status="completed")
            session.add(trans)
            await session.commit()
            
            if current_task < total_cap:
                await message.answer(f"✅ Vazifa bajarildi! Hisobingizga +{reward:,.0f} UZS qo'shildi.\n\nKeyingi buyurtmani olish uchun pastdagi tugmani bosing:", reply_markup=task_next_kb())
            else:
                await message.answer(f"✅ Barcha buyurtmalarni bajardingiz! E-Tycoon sizning mehnatingizni qadrlaydi.\nHisobingizga +{reward:,.0f} UZS qo'shildi.", reply_markup=main_menu_kb())
        else:
            await message.answer("Xatolik yoki limit to'lgan.", reply_markup=main_menu_kb())
            
    await state.clear()
