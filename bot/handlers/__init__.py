from aiogram import Router
from . import onboarding, main_menu, shops, tasks, cabinet, finance, promo, admin

router = Router()

router.include_router(onboarding.router)
router.include_router(main_menu.router)
router.include_router(shops.router)
router.include_router(tasks.router)
router.include_router(cabinet.router)
router.include_router(finance.router)
router.include_router(promo.router)
router.include_router(admin.router)
