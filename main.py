# ----------------------------------------------------
# نسخه یا سئخیندی پلن‌ها / VPN - ریلف فروش پروکسی
# ----------------------------------------------------

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ⚠️ توکن ربات خودت رو اینجا بذار (از BotFather گرفتی)
BOT_TOKEN = "8831432109:AAH1qD4DCvL-4d9nu0ESM_1Yl7jFeoEWvsA"

# ⚠️ آیدی عددی خودت (ادمین) - سفارش‌های جدید و درخواست‌های تست به این آیدی فرستاده میشه
ADMIN_CHAT_ID = 2064026398

# شماره کارتی که کاربر باید بهش پول واریز کنه
CARD_NUMBER = "5022291545430785"
CARD_OWNER_NAME = "رضا آذرشین"

# یوزرنیم کانال اصلی (برای چک عضویت اجباری)
CHANNEL_USERNAME = "@proxxymaster"

# فایلی که آیدی کاربرهایی که قبلاً درخواست تست داده‌اند رو نگه می‌داره
TRIAL_REQUESTS_FILE = "trial_requests.txt"

# دسته‌بندی پلن‌ها (فقط یک دسته: نامحدود)
CATEGORIES = {
    "unlimited": "نامحدود",
}

# توضیح مخصوص هر دسته (اختیاری) - اگه دسته‌ای توی این دیکشنری نباشه، متن پیش‌فرض نشون داده میشه
CATEGORY_DESCRIPTIONS = {}

# پلن‌های هر دسته
PLANS = {
    "unlimited": {
        "unl_1m_1u": {"title": "نامحدود ۱ ماهه تک کاربره", "price": 200000},
        "unl_1m_2u": {"title": "نامحدود ۱ ماهه ۲ کاربره", "price": 400000},
        "unl_2m_3u": {"title": "نامحدود 1 ماهه ۳ کاربره", "price": 600000},
    },
}


def build_category_keyboard():
    keyboard = []
    keyboard.append([InlineKeyboardButton("🎁 تست رایگان ۱ گیگ", callback_data="trial_request")])
    for cat_id, title in CATEGORIES.items():
        keyboard.append([InlineKeyboardButton(title, callback_data=f"cat:{cat_id}")])
    return InlineKeyboardMarkup(keyboard)


def build_plans_keyboard(cat_id):
    keyboard = []
    for plan_id, plan in PLANS[cat_id].items():
        button_text = f"{plan['title']} - {plan['price']:,} تومان"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"plan:{plan_id}")])
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="back:categories")])
    return InlineKeyboardMarkup(keyboard)


def build_join_keyboard():
    keyboard = [
        [InlineKeyboardButton("📢 عضویت در کانال", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}")],
        [InlineKeyboardButton("✅ عضو شدم", callback_data="checksub:trial")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ---------- کمک‌تابع‌های مدیریت فایل درخواست‌های تست ----------

def has_requested_trial(user_id: int) -> bool:
    try:
        with open(TRIAL_REQUESTS_FILE, "r", encoding="utf-8") as f:
            ids = f.read().splitlines()
        return str(user_id) in ids
    except FileNotFoundError:
        return False


def mark_trial_requested(user_id: int):
    with open(TRIAL_REQUESTS_FILE, "a", encoding="utf-8") as f:
        f.write(f"{user_id}\n")


async def is_channel_member(context: ContextTypes.DEFAULT_TYPE, user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def notify_admin_trial_request(context: ContextTypes.DEFAULT_TYPE, user):
    text = (
        "🆕 درخواست کانفیگ تست ۱ گیگ!\n\n"
        f"کاربر: {user.first_name} (@{user.username})\n"
        f"آیدی عددی: {user.id}\n\n"
        f"برای ارسال کانفیگ:\n/send {user.id} <متن کانفیگ>"
    )
    await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text)


# ---------- هندلرها ----------

# این تابع بعد از تایید عضویت (چه توی /start چه بعد از زدن دکمه «عضو شدم») اجرا میشه
async def show_main_content(reply_func, context: ContextTypes.DEFAULT_TYPE, user, args):
    # حالت لینک تست رایگان
    if args and args[0] == "trial":
        if has_requested_trial(user.id):
            await reply_func(
                "شما قبلاً یک بار درخواست کانفیگ تست ثبت کرده‌اید. "
                "اگر کانفیگ رو دریافت نکردید کمی صبر کنید یا با ادمین در ارتباط باشید."
            )
            return

        mark_trial_requested(user.id)
        await notify_admin_trial_request(context, user)
        await reply_func(
            "✅ درخواست شما ثبت شد!\nکانفیگ تست ۱ گیگ به‌زودی برات ارسال میشه، لطفاً کمی صبر کن."
        )
        return

    # حالت عادی /start (بدون لینک تست) -> منوی پلن‌ها
    await reply_func(
        "سلام 👋\nبه ربات فروش Proxy Master خوش اومدی!\nپلن VPN خود را انتخاب کنید:",
        reply_markup=build_category_keyboard(),
    )


# وقتی کاربر دستور /start رو بزنه (با یا بدون پارامتر trial) -> همیشه اول عضویت چک میشه
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    args = context.args  # لیست پارامترهای بعد از /start (مثلاً از لینک t.me/BotUsername?start=trial)

    # پارامترهای start رو ذخیره می‌کنیم تا بعد از تایید عضویت (با دکمه) بدونیم قرار بود چیکار کنیم
    context.user_data["pending_start_args"] = args

    is_member = await is_channel_member(context, user.id)
    if not is_member:
        await update.message.reply_text(
            "برای استفاده از ربات، اول باید عضو کانال ما بشی 👇\n"
            "بعد از عضویت، روی دکمه «✅ عضو شدم» بزن.",
            reply_markup=build_join_keyboard(),
        )
        return

    await show_main_content(update.message.reply_text, context, user, args)


# مدیریت همه‌ی کلیک‌های دکمه (دسته، پلن، بازگشت، چک عضویت)
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    user = query.from_user

    # کاربر روی دکمه «✅ عضو شدم» زده -> دوباره چک عضویت
    if data == "checksub:trial":
        is_member = await is_channel_member(context, user.id)

        if not is_member:
            await query.answer("هنوز عضو کانال نشدی! اول جوین کن بعد دکمه رو بزن.", show_alert=True)
            return

        # پارامترهایی که هنگام /start ذخیره کرده بودیم (مثلاً trial یا خالی)
        pending_args = context.user_data.get("pending_start_args", [])
        await show_main_content(query.edit_message_text, context, user, pending_args)
        return

    # کاربر روی دکمه «تست رایگان ۱ گیگ» توی منو زده
    # (کاربر تا اینجا حتماً عضو کانال بوده، چون منو فقط بعد از تایید عضویت نشون داده میشه)
    if data == "trial_request":
        if has_requested_trial(user.id):
            await query.edit_message_text(
                "شما قبلاً یک بار درخواست کانفیگ تست ثبت کرده‌اید. "
                "اگر کانفیگ رو دریافت نکردید کمی صبر کنید یا با ادمین در ارتباط باشید."
            )
            return

        mark_trial_requested(user.id)
        await notify_admin_trial_request(context, user)
        await query.edit_message_text(
            "✅ درخواست شما ثبت شد!\nکانفیگ تست ۱ گیگ به‌زودی برات ارسال میشه، لطفاً کمی صبر کن."
        )
        return

    # کاربر یک دسته (نامحدود) رو انتخاب کرده
    if data.startswith("cat:"):
        cat_id = data.split(":", 1)[1]
        description = CATEGORY_DESCRIPTIONS.get(cat_id)
        if description:
            header = f"{CATEGORIES[cat_id]}\n\n{description}\n\nیکی از گزینه‌های زیر رو انتخاب کن:"
        else:
            header = f"{CATEGORIES[cat_id]}\nیکی از پلن‌های زیر رو انتخاب کن:"
        await query.edit_message_text(
            header,
            reply_markup=build_plans_keyboard(cat_id),
        )
        return

    # کاربر دکمه بازگشت رو زده -> برگرد به انتخاب دسته
    if data == "back:categories":
        await query.edit_message_text(
            "پلن VPN خود را انتخاب کنید:",
            reply_markup=build_category_keyboard(),
        )
        return

    # کاربر یک پلن نهایی رو انتخاب کرده
    if data.startswith("plan:"):
        plan_id = data.split(":", 1)[1]
        plan = None
        for cat_plans in PLANS.values():
            if plan_id in cat_plans:
                plan = cat_plans[plan_id]
                break

        if plan is None:
            await query.edit_message_text("پلن نامعتبر است. لطفاً دوباره از منو انتخاب کنید.")
            return

        text = (
            f"پلن انتخابی: {plan['title']}\n"
            f"مبلغ: {plan['price']:,} تومان\n\n"
            f"لطفاً مبلغ رو به شماره کارت زیر واریز کن:\n"
            f"💳 {CARD_NUMBER}\n"
            f"به نام: {CARD_OWNER_NAME}\n\n"
            f"بعد از واریز، عکس رسید رو همینجا برام بفرست تا کانفیگت رو براب بسازم و بفرستم."
        )
        await query.edit_message_text(text)

        # ثبت سفارش در فایل
        with open("orders.txt", "a", encoding="utf-8") as f:
            f.write(
                f"کاربر: {user.first_name} (@{user.username}) | آیدی عددی: {user.id} | "
                f"پلن: {plan['title']} | مبلغ: {plan['price']}\n"
            )

        # 🔔 اطلاع‌رسانی سفارش جدید به ادمین (خودت) توی تلگرام
        admin_text = (
            "🔔 سفارش جدید!\n\n"
            f"کاربر: {user.first_name} (@{user.username})\n"
            f"آیدی عددی کاربر: {user.id}\n"
            f"پلن: {plan['title']}\n"
            f"مبلغ: {plan['price']:,} تومان"
        )
        await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=admin_text)
        return


# دستور ادمین برای ارسال کانفیگ به مشتری: /send USER_ID config_text
async def send_config(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # فقط خود ادمین بتونه از این دستور استفاده کنه
    if update.effective_user.id != ADMIN_CHAT_ID:
        return

    if not context.args or len(context.args) < 2:
        await update.message.reply_text("فرمت درست: /send USER_ID config_text")
        return

    target_user_id = context.args[0]
    config_text = " ".join(context.args[1:])

    try:
        await context.bot.send_message(chat_id=int(target_user_id), text=config_text)
        await update.message.reply_text("✅ کانفیگ با موفقیت برای مشتری ارسال شد.")
    except Exception as e:
        await update.message.reply_text(f"❌ ارسال ناموفق بود: {e}")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("send", send_config))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("ربات روشن شد و منتظر پیام‌هاست...")
    app.run_polling()


if __name__ == "__main__":
    main()
