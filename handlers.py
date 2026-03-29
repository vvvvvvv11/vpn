import uuid
import logging
import aiosqlite
from datetime import datetime

from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, CallbackQuery, PhotoSize,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import (
    PLANS, SUPPORT_USERNAME, ADMIN_ID,
    TUTORIAL_IOS, TUTORIAL_ANDROID,
    TUTORIAL_SUBSCRIPTION_IOS, TUTORIAL_SUBSCRIPTION_ANDROID,
    SUBSCRIPTION_BASE_URL, VPN_CONFIG,
    PAYMENT_CARD, PAYMENT_BANK, PAYMENT_NAME, PAYMENT_SBP
)
from database import (
    add_user, get_user, get_active_subscription,
    create_payment, get_payment_by_label,
    confirm_payment, reject_payment, activate_subscription,
    activate_subscription_days, increment_ref, get_ref_count,
    get_stats, get_all_user_ids, get_expiring_soon,
    get_user_os, set_user_os, has_used_trial, activate_trial,
    add_review, get_reviews, get_avg_rating, user_has_reviewed,
    create_promo, get_promo, use_promo, list_promos
)
from subscription import get_all_configs_text, get_subscription_link

router = Router()
logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════
# FSM
# ══════════════════════════════════════════════════════════════════════════

class BroadcastState(StatesGroup):
    waiting_message = State()

class ReviewState(StatesGroup):
    waiting_rating = State()
    waiting_text   = State()

class PromoCreateState(StatesGroup):
    waiting_input = State()

class ScreenshotState(StatesGroup):
    waiting_photo = State()


# ══════════════════════════════════════════════════════════════════════════
# Клавиатуры
# ══════════════════════════════════════════════════════════════════════════

def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Купить подписку",  callback_data="buy")],
        [InlineKeyboardButton(text="📡 Моя подписка",     callback_data="myconfig")],
        [InlineKeyboardButton(text="👤 Профиль",          callback_data="profile")],
        [InlineKeyboardButton(text="⭐️ Отзывы",          callback_data="reviews")],
        [InlineKeyboardButton(text="❓ Помощь",           callback_data="help")],
    ])

def os_select_kb(action: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🍎 iPhone (iOS)",  callback_data=f"os_ios_{action}")],
        [InlineKeyboardButton(text="🤖 Android",       callback_data=f"os_android_{action}")],
        [InlineKeyboardButton(text="◀️ Назад",         callback_data="back_main")],
    ])

def plans_kb(os: str) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"{p['label']} — {p['price']} ₽",
            callback_data=f"plan_{os}_{key}"
        )]
        for key, p in PLANS.items()
    ]
    buttons.append([InlineKeyboardButton(text="🎟 У меня есть промокод", callback_data=f"promo_enter_{os}")])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="buy")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_payment_kb(label: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{label}"),
        InlineKeyboardButton(text="❌ Отклонить",   callback_data=f"reject_{label}"),
    ]])

def rating_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⭐️ 1", callback_data="rate_1"),
            InlineKeyboardButton(text="⭐️ 2", callback_data="rate_2"),
            InlineKeyboardButton(text="⭐️ 3", callback_data="rate_3"),
            InlineKeyboardButton(text="⭐️ 4", callback_data="rate_4"),
            InlineKeyboardButton(text="⭐️ 5", callback_data="rate_5"),
        ],
        [InlineKeyboardButton(text="◀️ Отмена", callback_data="back_main")],
    ])

def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")]
    ])


# ══════════════════════════════════════════════════════════════════════════
# Хелперы
# ══════════════════════════════════════════════════════════════════════════

def os_label(os: str) -> str:
    return "🍎 iOS" if os == "ios" else "🤖 Android"

def get_tutorial(os: str) -> str:
    return TUTORIAL_ANDROID if os == "android" else TUTORIAL_IOS

def build_config_message(user_id: int, os: str = "ios") -> str:
    tutorial = TUTORIAL_SUBSCRIPTION_ANDROID if os == "android" else TUTORIAL_SUBSCRIPTION_IOS
    if SUBSCRIPTION_BASE_URL:
        link = get_subscription_link(SUBSCRIPTION_BASE_URL)
        return (
            f"🔗 <b>Ваша ссылка-подписка:</b>\n\n<code>{link}</code>\n\n"
            + tutorial.format(support=SUPPORT_USERNAME)
        )
    configs = get_all_configs_text()
    return (
        "📋 <b>Ваши конфиги VPN (5 серверов):</b>\n\n"
        f"<code>{configs}</code>\n\n"
        + tutorial.format(support=SUPPORT_USERNAME)
    )

def payment_requisites_text(amount: int, label: str) -> str:
    return (
        f"💳 <b>Реквизиты для оплаты</b>\n\n"
        f"🏦 Банк: <b>{PAYMENT_BANK}</b>\n"
        f"💳 Карта: <code>{PAYMENT_CARD}</code>\n"
        f"📲 СБП: <code>{PAYMENT_SBP}</code>\n"
        f"👤 Получатель: <b>{PAYMENT_NAME}</b>\n\n"
        f"💰 Сумма: <b>{amount} ₽</b>\n\n"
        f"После оплаты нажми кнопку ниже и <b>отправь скриншот</b> чека."
    )


# ══════════════════════════════════════════════════════════════════════════
# /start
# ══════════════════════════════════════════════════════════════════════════

@router.message(CommandStart())
async def cmd_start(message: Message):
    user_id  = message.from_user.id
    username = message.from_user.username or ""

    ref_by = None
    args   = message.text.split()
    if len(args) > 1:
        try:
            ref_by = int(args[1])
            if ref_by == user_id:
                ref_by = None
        except ValueError:
            ref_by = None

    existing = await get_user(user_id)
    await add_user(user_id, username, ref_by)
    if ref_by and not existing:
        await increment_ref(ref_by)

    await message.answer(
        f"👋 Привет, <b>{message.from_user.first_name}</b>!\n\n"
        "Я — бот для подключения к VPN.\n"
        "🇷🇺 Работает на всех операторах · iOS · Android\n\n"
        "Выбери действие:",
        reply_markup=main_menu_kb(),
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════
# Навигация
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "back_main")
async def back_main(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.edit_text("Выбери действие:", reply_markup=main_menu_kb())

@router.callback_query(F.data == "help")
async def cb_help(call: CallbackQuery):
    await call.message.edit_text(
        f"❓ <b>Помощь</b>\n\nПо всем вопросам: @{SUPPORT_USERNAME}",
        reply_markup=back_kb(), parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════
# Пробный период
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "trial")
async def cb_trial(call: CallbackQuery):
    if await has_used_trial(call.from_user.id):
        await call.answer("❌ Вы уже использовали пробный период.", show_alert=True)
        return
    if await get_active_subscription(call.from_user.id):
        await call.answer("У вас уже есть активная подписка.", show_alert=True)
        return
    await call.message.edit_text(
        "🎁 <b>3 дня бесплатно!</b>\n\nВыберите вашу ОС:",
        reply_markup=os_select_kb("trial"), parse_mode="HTML"
    )

@router.callback_query(F.data.in_({"os_ios_trial", "os_android_trial"}))
async def cb_trial_os(call: CallbackQuery):
    os      = "android" if "android" in call.data else "ios"
    user_id = call.from_user.id
    if await has_used_trial(user_id):
        await call.answer("❌ Уже использован.", show_alert=True)
        return
    await activate_trial(user_id, os)
    await call.message.edit_text(
        f"✅ <b>Пробный период активирован на 3 дня!</b>\n\n"
        f"🔑 Ваш конфиг:\n\n<code>{VPN_CONFIG}</code>",
        parse_mode="HTML", reply_markup=back_kb()
    )
    await call.message.answer(
        get_tutorial(os).format(support=SUPPORT_USERNAME),
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════
# Покупка — выбор ОС → тариф → оплата скриншотом
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "buy")
async def cb_buy(call: CallbackQuery):
    await call.message.edit_text(
        "💳 <b>Покупка подписки</b>\n\nВыберите вашу ОС:",
        reply_markup=os_select_kb("buy"), parse_mode="HTML"
    )

@router.callback_query(F.data.in_({"os_ios_buy", "os_android_buy"}))
async def cb_os_selected(call: CallbackQuery):
    os = "android" if "android" in call.data else "ios"
    await set_user_os(call.from_user.id, os)
    await call.message.edit_text(
        f"💳 <b>Выберите тариф</b> ({os_label(os)}):",
        reply_markup=plans_kb(os), parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("plan_"))
async def cb_plan(call: CallbackQuery, state: FSMContext):
    parts    = call.data.split("_")   # plan_ios_1m
    os       = parts[1]
    plan_key = parts[2]
    plan     = PLANS.get(plan_key)
    if not plan:
        await call.answer("Неизвестный тариф", show_alert=True)
        return

    label   = f"vpn_{call.from_user.id}_{plan_key}_{uuid.uuid4().hex[:8]}"
    amount  = plan["price"]

    await create_payment(call.from_user.id, label, amount, plan_key, os)
    await state.update_data(label=label, os=os)
    await state.set_state(ScreenshotState.waiting_photo)

    await call.message.edit_text(
        payment_requisites_text(amount, label),
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Отправить скриншот", callback_data="send_screenshot")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="buy")],
        ])
    )

@router.callback_query(F.data == "send_screenshot")
async def cb_send_screenshot(call: CallbackQuery, state: FSMContext):
    await state.set_state(ScreenshotState.waiting_photo)
    await call.message.edit_text(
        "📸 <b>Отправь скриншот чека об оплате</b>\n\n"
        "Просто прикрепи фото прямо в этот чат.",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

@router.message(ScreenshotState.waiting_photo, F.photo)
async def cb_screenshot_received(message: Message, state: FSMContext, bot: Bot):
    data     = await state.get_data()
    label    = data.get("label")
    os       = data.get("os", "ios")
    await state.clear()

    if not label:
        await message.answer("❌ Что-то пошло не так. Начни заново.", reply_markup=back_kb())
        return

    payment  = await get_payment_by_label(label)
    if not payment:
        await message.answer("❌ Платёж не найден.", reply_markup=back_kb())
        return

    user_id  = message.from_user.id
    username = message.from_user.username or "нет"
    plan_key = payment[4]
    plan     = PLANS.get(plan_key, {})

    # Обновляем статус
    async with aiosqlite.connect("bot.db") as db:
        await db.execute("UPDATE payments SET status='pending_review' WHERE label=?", (label,))
        await db.commit()

    # Пересылаем скриншот админу с кнопками
    photo_id = message.photo[-1].file_id
    try:
        await bot.send_photo(
            int(ADMIN_ID),
            photo=photo_id,
            caption=(
                f"📸 <b>Скриншот оплаты!</b>\n\n"
                f"👤 @{username} (<code>{user_id}</code>)\n"
                f"📱 ОС: {os_label(os)}\n"
                f"📦 Тариф: {plan.get('label', plan_key)}\n"
                f"💵 Сумма: {payment[3]} ₽\n"
                f"🏷 Метка: <code>{label}</code>"
            ),
            reply_markup=admin_payment_kb(label),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Не удалось отправить скриншот админу: {e}")

    await message.answer(
        "⏳ <b>Скриншот получен и отправлен на проверку!</b>\n\n"
        "Обычно подтверждение занимает несколько минут.\n"
        "После проверки вы получите конфиг автоматически.",
        parse_mode="HTML",
        reply_markup=back_kb()
    )


# ══════════════════════════════════════════════════════════════════════════
# Промокоды
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("promo_enter_"))
async def cb_promo_enter(call: CallbackQuery, state: FSMContext):
    os = call.data.split("_")[-1]
    await state.update_data(os=os)
    await state.set_state(PromoCreateState.waiting_input)
    await call.message.edit_text(
        "🎟 <b>Введи промокод:</b>",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

@router.message(PromoCreateState.waiting_input)
async def cb_promo_check(message: Message, state: FSMContext, bot: Bot):
    data  = await state.get_data()
    os    = data.get("os", "ios")
    code  = message.text.strip().upper()
    promo = await get_promo(code)

    if not promo:
        await message.answer(
            "❌ <b>Промокод не найден или уже использован.</b>\n\nПопробуй другой или выбери тариф.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Выбрать тариф", callback_data=f"os_{os}_buy")],
                [InlineKeyboardButton(text="◀️ Назад",         callback_data="back_main")],
            ])
        )
        await state.clear()
        return

    await state.clear()
    # promo: (id, code, type, value, uses_left, created_at)
    promo_type  = promo[2]
    promo_value = promo[3]

    if promo_type == "days":
        # Бесплатные дни — сразу активируем
        await use_promo(code)
        await activate_subscription_days(message.from_user.id, promo_value)
        await message.answer(
            f"✅ <b>Промокод активирован!</b>\n\n"
            f"🎁 Добавлено <b>{promo_value} дней</b> подписки.\n\n"
            f"🔑 Ваш конфиг:\n\n<code>{VPN_CONFIG}</code>",
            parse_mode="HTML"
        )
        await message.answer(
            get_tutorial(os).format(support=SUPPORT_USERNAME),
            parse_mode="HTML",
            reply_markup=back_kb()
        )
    elif promo_type == "discount":
        # Скидка — показываем тарифы со скидкой
        buttons = []
        for key, plan in PLANS.items():
            discounted = int(plan["price"] * (1 - promo_value / 100))
            buttons.append([InlineKeyboardButton(
                text=f"{plan['label']} — {discounted} ₽ (−{promo_value}%)",
                callback_data=f"promo_plan_{os}_{key}_{code}"
            )])
        buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")])
        await message.answer(
            f"✅ <b>Промокод принят! Скидка {promo_value}%</b>\n\nВыбери тариф:",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
        )

@router.callback_query(F.data.startswith("promo_plan_"))
async def cb_promo_plan(call: CallbackQuery, state: FSMContext, bot: Bot):
    # promo_plan_ios_1m_CODE
    parts    = call.data.split("_")
    os       = parts[2]
    plan_key = parts[3]
    code     = parts[4]

    promo = await get_promo(code)
    if not promo:
        await call.answer("Промокод уже использован", show_alert=True)
        return

    plan   = PLANS.get(plan_key, {})
    discount = promo[3]
    amount = int(plan["price"] * (1 - discount / 100))
    label  = f"vpn_{call.from_user.id}_{plan_key}_{uuid.uuid4().hex[:8]}"

    await use_promo(code)
    await create_payment(call.from_user.id, label, amount, plan_key, os)
    await state.update_data(label=label, os=os)
    await state.set_state(ScreenshotState.waiting_photo)

    await call.message.edit_text(
        payment_requisites_text(amount, label)
        + f"\n\n🎟 Промокод применён: скидка {discount}%",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📸 Отправить скриншот", callback_data="send_screenshot")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_main")],
        ])
    )


# ══════════════════════════════════════════════════════════════════════════
# Профиль
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "profile")
async def cb_profile(call: CallbackQuery, bot: Bot):
    user_id   = call.from_user.id
    sub       = await get_active_subscription(user_id)
    ref_count = await get_ref_count(user_id)
    os        = await get_user_os(user_id) or "ios"
    bot_info  = await bot.get_me()

    if sub:
        try:
            dt      = datetime.strptime(sub[3][:10], "%Y-%m-%d")
            expires = dt.strftime("%d.%m.%Y")
        except Exception:
            expires = sub[3][:10]
        status = f"✅ Активна до: <b>{expires}</b>"
    else:
        status = "❌ Нет активной подписки"

    ref_link = f"https://t.me/{bot_info.username}?start={user_id}"

    await call.message.edit_text(
        f"👤 <b>Профиль</b>\n\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"📱 ОС: {os_label(os)}\n"
        f"📡 Подписка: {status}\n"
        f"👥 Рефералов: <b>{ref_count}</b>\n\n"
        f"🔗 Реферальная ссылка:\n<code>{ref_link}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сменить ОС",    callback_data="change_os")],
            [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data="leave_review")],
            [InlineKeyboardButton(text="◀️ Назад",          callback_data="back_main")],
        ]),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "change_os")
async def cb_change_os(call: CallbackQuery):
    await call.message.edit_text(
        "🔄 Выберите вашу ОС:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🍎 iPhone (iOS)", callback_data="set_os_ios")],
            [InlineKeyboardButton(text="🤖 Android",      callback_data="set_os_android")],
            [InlineKeyboardButton(text="◀️ Назад",        callback_data="profile")],
        ])
    )

@router.callback_query(F.data.startswith("set_os_"))
async def cb_set_os(call: CallbackQuery):
    os = "android" if "android" in call.data else "ios"
    await set_user_os(call.from_user.id, os)
    await call.message.edit_text(
        f"✅ ОС изменена на {os_label(os)}", reply_markup=back_kb()
    )


# ══════════════════════════════════════════════════════════════════════════
# Мой конфиг
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "myconfig")
async def cb_myconfig(call: CallbackQuery):
    user_id = call.from_user.id
    sub     = await get_active_subscription(user_id)
    if not sub:
        await call.message.edit_text(
            "❌ У вас нет активной подписки.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Купить",  callback_data="buy")],
                [InlineKeyboardButton(text="◀️ Назад",   callback_data="back_main")],
            ])
        )
        return
    os   = await get_user_os(user_id) or "ios"
    text = build_config_message(user_id, os)
    await call.message.edit_text(text, reply_markup=back_kb(), parse_mode="HTML")


# ══════════════════════════════════════════════════════════════════════════
# Отзывы
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data == "reviews")
async def cb_reviews(call: CallbackQuery):
    reviews = await get_reviews(5)
    avg, total = await get_avg_rating()

    stars = "⭐️" * int(avg) if avg else "—"
    header = f"⭐️ <b>Отзывы</b>\n\nСредняя оценка: {stars} <b>{avg}/5</b> ({total} отзывов)\n\n"

    if not reviews:
        text = header + "Пока нет отзывов. Будьте первым!"
    else:
        lines = []
        for username, rating, text, created_at in reviews:
            date  = created_at[:10] if created_at else ""
            stars_row = "⭐️" * rating
            lines.append(f"{stars_row} <b>@{username}</b> · {date}\n{text}")
        text = header + "\n\n".join(lines)

    await call.message.edit_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✍️ Написать отзыв", callback_data="leave_review")],
            [InlineKeyboardButton(text="◀️ Назад",           callback_data="back_main")],
        ])
    )

@router.callback_query(F.data == "leave_review")
async def cb_leave_review(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id

    if not await get_active_subscription(user_id):
        await call.answer("❌ Отзывы могут оставлять только активные пользователи.", show_alert=True)
        return

    if await user_has_reviewed(user_id):
        await call.answer("Вы уже оставили отзыв. Спасибо! ❤️", show_alert=True)
        return

    await state.set_state(ReviewState.waiting_rating)
    await call.message.edit_text(
        "⭐️ <b>Оцените наш VPN:</b>",
        parse_mode="HTML",
        reply_markup=rating_kb()
    )

@router.callback_query(F.data.startswith("rate_"), ReviewState.waiting_rating)
async def cb_rate(call: CallbackQuery, state: FSMContext):
    rating = int(call.data.split("_")[1])
    await state.update_data(rating=rating)
    await state.set_state(ReviewState.waiting_text)
    await call.message.edit_text(
        f"{'⭐️' * rating}\n\n✍️ <b>Напишите короткий отзыв</b> (1-2 предложения):",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

@router.message(ReviewState.waiting_text)
async def cb_review_text(message: Message, state: FSMContext, bot: Bot):
    data     = await state.get_data()
    rating   = data.get("rating", 5)
    text     = message.text.strip()
    user_id  = message.from_user.id
    username = message.from_user.username or f"user{user_id}"

    if len(text) < 5:
        await message.answer("❌ Слишком короткий отзыв. Напишите подробнее.")
        return

    await state.clear()
    await add_review(user_id, username, rating, text)

    await message.answer(
        "✅ <b>Спасибо за отзыв!</b> ❤️",
        parse_mode="HTML",
        reply_markup=back_kb()
    )

    # Уведомляем админа
    try:
        await bot.send_message(
            int(ADMIN_ID),
            f"⭐️ <b>Новый отзыв!</b>\n\n"
            f"👤 @{username}\n"
            f"Оценка: {'⭐️' * rating}\n\n"
            f"{text}",
            parse_mode="HTML"
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════
# Админ: подтверждение / отклонение
# ══════════════════════════════════════════════════════════════════════════

@router.callback_query(F.data.startswith("confirm_"))
async def cb_confirm(call: CallbackQuery, bot: Bot):
    if str(call.from_user.id) != str(ADMIN_ID):
        await call.answer("Нет доступа", show_alert=True)
        return

    label   = call.data[8:]
    payment = await get_payment_by_label(label)
    if not payment:
        await call.answer("Платёж не найден", show_alert=True)
        return

    user_id  = payment[1]
    plan_key = payment[4]
    os       = payment[6] if len(payment) > 6 else "ios"
    plan     = PLANS.get(plan_key, {})

    await confirm_payment(label)
    await activate_subscription(user_id, plan_key)

    try:
        await bot.send_message(
            user_id,
            f"✅ <b>Оплата подтверждена! Подписка активирована.</b>\n"
            f"Тариф: {plan.get('label', plan_key)} · {os_label(os)}\n\n"
            f"🔑 <b>Ваш конфиг:</b>\n\n<code>{VPN_CONFIG}</code>",
            parse_mode="HTML"
        )
        await bot.send_message(
            user_id,
            get_tutorial(os).format(support=SUPPORT_USERNAME),
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⭐️ Оставить отзыв", callback_data="leave_review")]
            ])
        )
    except Exception as e:
        logger.error(f"Ошибка отправки конфига: {e}")

    await call.message.edit_caption(
        call.message.caption + "\n\n✅ <b>Подтверждено</b>",
        parse_mode="HTML"
    ) if call.message.caption else await call.message.edit_text(
        f"✅ Платёж <code>{label}</code> подтверждён.", parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("reject_"))
async def cb_reject(call: CallbackQuery, bot: Bot):
    if str(call.from_user.id) != str(ADMIN_ID):
        await call.answer("Нет доступа", show_alert=True)
        return

    label   = call.data[7:]
    payment = await get_payment_by_label(label)
    if not payment:
        await call.answer("Платёж не найден", show_alert=True)
        return

    user_id = payment[1]
    await reject_payment(label)

    try:
        await bot.send_message(
            user_id,
            f"❌ <b>Платёж отклонён.</b>\n\nОбратитесь в поддержку: @{SUPPORT_USERNAME}",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")

    await call.message.edit_caption(
        call.message.caption + "\n\n❌ <b>Отклонено</b>",
        parse_mode="HTML"
    ) if call.message.caption else await call.message.edit_text(
        f"❌ Платёж <code>{label}</code> отклонён.", parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════
# /admin
# ══════════════════════════════════════════════════════════════════════════

@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    stats = await get_stats()
    await message.answer(
        "🛠 <b>Админ-панель</b>\n\n"
        f"👥 Пользователей: <b>{stats['total_users']}</b>\n"
        f"✅ Активных подписок: <b>{stats['active_subs']}</b>\n"
        f"💰 Оплачено: <b>{stats['paid_payments']}</b>\n"
        f"⏳ На проверке: <b>{stats['pending_payments']}</b>\n"
        f"💵 Выручка: <b>{stats['total_revenue']} ₽</b>\n"
        f"⭐️ Отзывов: <b>{stats['total_reviews']}</b>\n\n"
        "📢 /broadcast — рассылка\n"
        "🎟 /promo — управление промокодами\n"
        "⏰ /reminders — напомнить истекающим",
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════
# /promo — управление промокодами
# ══════════════════════════════════════════════════════════════════════════

@router.message(Command("promo"))
async def cmd_promo(message: Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return

    promos = await list_promos()
    lines  = []
    for code, type_, value, uses_left in promos:
        desc = f"{value}%" if type_ == "discount" else f"{value} дней"
        lines.append(f"• <code>{code}</code> — {desc} · осталось: {uses_left}")

    text = "🎟 <b>Промокоды</b>\n\n"
    text += "\n".join(lines) if lines else "Промокодов нет."
    text += (
        "\n\n<b>Создать промокод:</b>\n"
        "/newpromo ЛЕТO20 discount 20 5\n"
        "→ код ЛЕТО20, скидка 20%, 5 использований\n\n"
        "/newpromo ДРУГ days 30 1\n"
        "→ код ДРУГ, 30 бесплатных дней, 1 использование"
    )
    await message.answer(text, parse_mode="HTML")

@router.message(Command("newpromo"))
async def cmd_newpromo(message: Message):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    parts = message.text.split()
    # /newpromo CODE type value uses
    if len(parts) < 4:
        await message.answer("❌ Формат: /newpromo КОД тип значение [количество]\nТип: discount или days")
        return
    code   = parts[1].upper()
    type_  = parts[2]
    value  = int(parts[3])
    uses   = int(parts[4]) if len(parts) > 4 else 1

    if type_ not in ("discount", "days"):
        await message.answer("❌ Тип должен быть: discount или days")
        return

    await create_promo(code, type_, value, uses)
    desc = f"скидка {value}%" if type_ == "discount" else f"{value} бесплатных дней"
    await message.answer(
        f"✅ Промокод <code>{code}</code> создан!\n{desc} · {uses} использований",
        parse_mode="HTML"
    )


# ══════════════════════════════════════════════════════════════════════════
# /reminders
# ══════════════════════════════════════════════════════════════════════════

@router.message(Command("reminders"))
async def cmd_reminders(message: Message, bot: Bot):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    expiring = await get_expiring_soon()
    if not expiring:
        await message.answer("Нет подписок истекающих в течение 3 дней.")
        return
    sent = 0
    for user_id, expires in expiring:
        try:
            await bot.send_message(
                user_id,
                f"⏰ <b>Напоминание!</b>\n\n"
                f"Ваша подписка истекает <b>{expires[:10]}</b>.\n\n"
                f"Продлите подписку, чтобы не потерять доступ к VPN 👇",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 Продлить", callback_data="buy")]
                ])
            )
            sent += 1
        except Exception:
            pass
    await message.answer(f"✅ Напоминания отправлены: {sent} пользователям.")


# ══════════════════════════════════════════════════════════════════════════
# /broadcast
# ══════════════════════════════════════════════════════════════════════════

@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, state: FSMContext):
    if str(message.from_user.id) != str(ADMIN_ID):
        return
    await message.answer("📢 Отправь сообщение для рассылки. /cancel — отмена")
    await state.set_state(BroadcastState.waiting_message)

@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Отменено.")

@router.message(BroadcastState.waiting_message)
async def do_broadcast(message: Message, state: FSMContext):
    await state.clear()
    all_users  = await get_all_user_ids()
    sent, fail = 0, 0
    status     = await message.answer(f"📤 Рассылка на {len(all_users)} пользователей...")
    for uid in all_users:
        try:
            await message.copy_to(uid)
            sent += 1
        except Exception:
            fail += 1
    await status.edit_text(
        f"✅ <b>Готово!</b>\n📨 Отправлено: <b>{sent}</b>\n❌ Ошибок: <b>{fail}</b>",
        parse_mode="HTML"
    )
