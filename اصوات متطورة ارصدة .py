
# =====================================================
# Sajjad Voice Bot
# المطور والحقوق: سجاد العسكري
# 32 صوت | نظام رصيد | تشخيص التشغيل
# =====================================================

import os
import sys
import time
import logging
import sqlite3
import threading
from io import BytesIO

try:
    import requests
    import telebot
    from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
except ImportError as e:
    print("مكتبة ناقصة:", e)
    print("ثبّت المكتبات من الطرفية:")
    print("pip install -U pyTelegramBotAPI requests")
    raise SystemExit(1)

# ========= ضع مفاتيحك الجديدة هنا =========
BOT_TOKEN = "8950907222:AAE7dj2LxlLmm78ReGWt3XkwWz2SW157FK0"
FISH_API_KEY = "sk-fish-sZdzszb0g07CiffrshcMFDFwWQjDxleaUj-KuT3B2qc"

ADMIN_ID = 8407089956
ADMIN_USERNAME = "C_58a"

STARTING_BALANCE = 10
VOICE_COST = 1
MAX_TEXT_LENGTH = 500

API_URL = "https://api.fish.audio/v1/tts"
MODEL = "s2.1-pro-free"
DB_FILE = "sajjad_voice_bot.db"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ========= الأصوات الـ32 =========
VOICES = {
    "voice_1": ("6843639bb79c4b0ba2c15307280465ca", "👧 صوت بنية"),
    "voice_2": ("baeba69bf83d47f9adb0e66e8f8f1658", "👨 صوت والد"),
    "voice_3": ("8ea1c102258b4496b2234e6e7d20b5c2", "🇸🇾 صوت بنت سوريا"),
    "voice_4": ("060bb46361764a668119db1f06f00982", "✨ صوت حلو"),
    "voice_5": ("7e4fa512aa564e198f8659b466f6ff70", "🎤 صوت أبو فلة"),
    "voice_6": ("4b06a9b39328408f95420f1ff675cd6d", "🌍 صوت ناشيونال جيوغرافيك"),
    "voice_7": ("ce57a282aa274f94a61d7256e5f264c2", "🎙️ صوت عصام الشوالي"),
    "voice_8": ("2127ba3dd08e4b7fbf7136cc45c76fff", "🎙️ صوت الحوثي"),
    "voice_9": ("c4ec6e6fca4d4a5486fb1806109d7ac5", "🇮🇶 صوت بنية عراقية"),
    "voice_10": ("041537ad14a4456abf20499c9fe0b1bf", "🇮🇶 صوت بنية عراقية 2"),
    "voice_11": ("8d2a4f1202ad4615b5fe2110a3ad8fee", "📰 صوت الأخبار"),
    "voice_12": ("12d72ab8c79040c78e72342a44a3cf48", "📺 صوت مقدمة الأخبار"),
    "voice_13": ("0bfcb93380aa4928bb1a6914ea754f3a", "🍥 صوت نارو"),
    "voice_14": ("2f0ab00b78f84e2eb128b63416dc982c", "🎙️ صوت حميد الأعرج"),
    "voice_15": ("6cadb046845b48f195118514e77539c6", "🎙️ صوت علي الزيدي"),
    "voice_16": ("8f32c2fd156644bb869672992d60e700", "🎙️ صوت علي شاكر"),
    "voice_17": ("05b67f79f822458f82d20153ce367273", "🎤 صوت بنت تغني"),
    "voice_18": ("1d785d369dbf41589e421f4c72713629", "🇸🇦 صوت بنت خليجية"),
    "voice_19": ("c81277ee8c25464687cdfda5df94152d", "🎙️ صوت بنت $"),
    "voice_20": ("37a9369db9474cc79328f49d6231c48b", "🎙️ صوت بنت ©"),
    "voice_21": ("bc5e2eccf7c149b9a515d6b4598e9f9a", "🎙️ صوت صدام حسين"),
    "voice_22": ("8a51eebc85e644ce80460199cc5ec743", "🎙️ صوت محمد بن سلمان"),
    "voice_23": ("8cfbfeb71510423da485e2ebb83c3f63", "🎙️ صوت أحمد الشرع"),
    "voice_24": ("b3c8c4d3b1ef46b7ab4ee5ab77d24f41", "🎙️ صوت نوري المالكي"),
    "voice_25": ("1ed0ba24d1224234b408584b1eb41e22", "🎙️ صوت مقتدى الصدر"),
    "voice_26": ("3622e41aa200447fa5924e480ac048a2", "🎙️ صوت مقتدى الصدر 2"),
    "voice_27": ("e6ed4a18cf8a41fcb322cf401ea1d431", "🎙️ صوت السيد علي خامنئي"),
    "voice_28": ("75171350ef994929a33959cf91bbb64a", "🎙️ صوت بارق"),
    "voice_29": ("134debcc85df42a3b19d3d594768cb29", "🎙️ يوسف لاز"),
    "voice_30": ("a66e3d12eb824ca88e75ee9c9a5fc356", "🕌 صوت الشيخ أحمد الوائلي"),
    "voice_31": ("7f039943bf1f417293f0d77fa9b797ca", "🎙️ صوت أبو جنة"),
    "voice_32": ("79b0fd32e00645e2827b841629034be5", "🎙️ صوت فارس عوض"),
}

if (
    not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN"
    or not FISH_API_KEY or FISH_API_KEY == "YOUR_FISH_API_KEY"
):
    print("❌ أدخل توكن تيليجرام ومفتاح Fish Audio بأعلى الملف.")
    raise SystemExit(1)

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)
db_lock = threading.Lock()
text_lock = threading.Lock()
user_texts = {}


# ========= قاعدة البيانات =========
def db_connect():
    conn = sqlite3.connect(DB_FILE, timeout=20)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance INTEGER NOT NULL DEFAULT 10
        )
    """)
    return conn


def init_db():
    with db_lock:
        conn = db_connect()
        conn.commit()
        conn.close()


def register_user(user_id):
    if user_id == ADMIN_ID:
        return
    with db_lock:
        conn = db_connect()
        conn.execute(
            "INSERT OR IGNORE INTO users(user_id, balance) VALUES (?, ?)",
            (user_id, STARTING_BALANCE)
        )
        conn.commit()
        conn.close()


def get_balance(user_id):
    if user_id == ADMIN_ID:
        return None
    register_user(user_id)
    with db_lock:
        conn = db_connect()
        row = conn.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        conn.close()
    return row[0] if row else 0


def change_balance(user_id, amount):
    register_user(user_id)
    if user_id == ADMIN_ID:
        return True
    with db_lock:
        conn = db_connect()
        row = conn.execute(
            "SELECT balance FROM users WHERE user_id = ?", (user_id,)
        ).fetchone()
        current = row[0] if row else 0
        new_balance = current + amount
        if new_balance < 0:
            conn.close()
            return False
        conn.execute(
            "UPDATE users SET balance = ? WHERE user_id = ?",
            (new_balance, user_id)
        )
        conn.commit()
        conn.close()
    return True


def get_user_count():
    with db_lock:
        conn = db_connect()
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        conn.close()
    return count


# ========= القوائم =========
def main_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("🎙️ اختيار صوت", callback_data="voices"),
        InlineKeyboardButton("💰 رصيدي", callback_data="balance")
    )
    kb.add(
        InlineKeyboardButton("➕ شحن الرصيد", url=f"https://t.me/{ADMIN_USERNAME}"),
        InlineKeyboardButton("👨‍💻 المطور", url=f"https://t.me/{ADMIN_USERNAME}")
    )
    return kb


def voice_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    for key, (voice_id, name) in VOICES.items():
        kb.add(InlineKeyboardButton(name, callback_data=key))
    kb.add(InlineKeyboardButton("🔊 تحويل بكل الأصوات", callback_data="voice_all"))
    kb.add(InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data="home"))
    return kb


def send_home(chat_id, user_id):
    balance = get_balance(user_id)
    balance_text = "غير محدود ♾️" if balance is None else f"{balance} نقطة"
    bot.send_message(
        chat_id,
        "🎙️ أهلاً بك في Sajjad Voice Bot\n\n"
        "حوّل النص إلى صوت واختَر من بين 32 صوتاً.\n"
        f"💰 رصيدك: {balance_text}\n"
        f"🔹 تكلفة التحويل: {VOICE_COST} نقطة\n\n"
        "أرسل النص الذي تريد تحويله، ثم اختر الصوت.",
        reply_markup=main_keyboard()
    )


# ========= تحويل النص إلى صوت =========
def fish_tts(text, voice_id):
    headers = {
        "Authorization": f"Bearer {FISH_API_KEY}",
        "Content-Type": "application/json",
        "model": MODEL
    }
    payload = {
        "text": text,
        "reference_id": voice_id,
        "format": "mp3",
        "latency": "normal"
    }
    response = requests.post(
        API_URL, headers=headers, json=payload, timeout=90
    )
    if response.status_code != 200:
        detail = response.text[:700]
        raise RuntimeError(f"Fish Audio HTTP {response.status_code}: {detail}")
    if not response.content:
        raise RuntimeError("Fish Audio رجّع ملفاً فارغاً.")
    return response.content


def convert_voice(chat_id, user_id, voice_key, text):
    if voice_key not in VOICES:
        bot.send_message(chat_id, "❌ الصوت غير موجود.")
        return

    balance = get_balance(user_id)
    if balance is not None and balance < VOICE_COST:
        bot.send_message(
            chat_id,
            "❌ رصيدك ما يكفي.\n"
            "تواصل ويا المطور لشحن الرصيد.",
            reply_markup=main_keyboard()
        )
        return

    voice_id, voice_name = VOICES[voice_key]
    status = bot.send_message(
        chat_id, f"⏳ جاري تحويل النص باستخدام {voice_name}..."
    )

    try:
        audio_bytes = fish_tts(text, voice_id)
        audio = BytesIO(audio_bytes)
        audio.name = "sajjad_voice.mp3"

        bot.send_audio(
            chat_id,
            audio,
            caption=f"🎙️ {voice_name}\n© حقوق سجاد العسكري",
            timeout=120
        )

        if balance is not None:
            change_balance(user_id, -VOICE_COST)

        new_balance = get_balance(user_id)
        if new_balance is None:
            balance_text = "غير محدود ♾️"
        else:
            balance_text = f"{new_balance} نقطة"

        bot.send_message(chat_id, f"✅ تم التحويل بنجاح!\n💰 رصيدك: {balance_text}")

    except Exception as e:
        logging.exception("فشل تحويل الصوت")
        bot.send_message(
            chat_id,
            "❌ فشل تحويل الصوت.\n"
            f"السبب: {str(e)[:900]}\n\n"
            "إذا ظهر 402 فقد تكون الخدمة تتطلب رصيداً أو خطة مدفوعة."
        )
    finally:
        try:
            bot.delete_message(chat_id, status.message_id)
        except Exception:
            pass


# ========= أوامر تيليجرام =========
@bot.message_handler(commands=["start"])
def start(message):
    user_id = message.from_user.id
    register_user(user_id)

    if user_id != ADMIN_ID:
        try:
            user = message.from_user
            username = f"@{user.username}" if user.username else "بدون يوزر"
            bot.send_message(
                ADMIN_ID,
                "👤 مستخدم دخل إلى Sajjad Voice Bot\n"
                f"الاسم: {user.first_name}\n"
                f"المعرف: {username}\n"
                f"ID: {user_id}"
            )
        except Exception:
            logging.info("لم يتم إرسال إشعار دخول للمطور.")

    send_home(message.chat.id, user_id)


@bot.message_handler(commands=["help"])
def help_command(message):
    bot.send_message(
        message.chat.id,
        "/start - تشغيل البوت\n"
        "/balance - عرض الرصيد\n"
        "/myid - عرض معرفك\n"
        "/admin - إحصائيات الإدارة\n"
        "/addbalance USER_ID AMOUNT - إضافة رصيد للمستخدم\n"
        "/checkbalance USER_ID - فحص رصيد مستخدم"
    )


@bot.message_handler(commands=["balance"])
def balance_command(message):
    balance = get_balance(message.from_user.id)
    if balance is None:
        text = "💰 رصيدك غير محدود ♾️"
    else:
        text = f"💰 رصيدك الحالي: {balance} نقطة"
    bot.reply_to(message, text)


@bot.message_handler(commands=["myid"])
def myid_command(message):
    bot.reply_to(message, f"🆔 معرفك: {message.from_user.id}")


@bot.message_handler(commands=["admin"])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط.")
        return
    bot.reply_to(
        message,
        f"📊 عدد المستخدمين المسجلين: {get_user_count()}\n"
        f"🎙️ عدد الأصوات: {len(VOICES)}"
    )


@bot.message_handler(commands=["addbalance"])
def addbalance_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط.")
        return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        if amount <= 0:
            raise ValueError("المبلغ يجب أن يكون أكبر من صفر")
        change_balance(target_id, amount)
        bot.reply_to(
            message,
            f"✅ تمت إضافة {amount} نقطة للمستخدم {target_id}."
        )
        try:
            bot.send_message(
                target_id, f"🎁 تمت إضافة {amount} نقطة إلى رصيدك."
            )
        except Exception:
            pass
    except Exception:
        bot.reply_to(
            message,
            "طريقة الاستخدام:\n/addbalance USER_ID AMOUNT"
        )


@bot.message_handler(commands=["checkbalance"])
def checkbalance_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ هذا الأمر للمطور فقط.")
        return
    try:
        target_id = int(message.text.split()[1])
        balance = get_balance(target_id)
        if balance is None:
            result = "رصيد المطور غير محدود."
        else:
            result = f"رصيد المستخدم {target_id}: {balance} نقطة."
        bot.reply_to(message, result)
    except Exception:
        bot.reply_to(message, "الاستخدام: /checkbalance USER_ID")


# ========= استقبال النصوص =========
@bot.message_handler(content_types=["text"], func=lambda m: not m.text.startswith("/"))
def receive_text(message):
    text = message.text.strip()
    if not text:
        bot.reply_to(message, "أرسل نصاً أولاً.")
        return
    if len(text) > MAX_TEXT_LENGTH:
        bot.reply_to(
            message,
            f"❌ الحد الأقصى للنص هو {MAX_TEXT_LENGTH} حرف."
        )
        return

    key = (message.chat.id, message.from_user.id)
    with text_lock:
        user_texts[key] = text

    bot.send_message(
        message.chat.id,
        "✅ استلمت النص.\n"
        "اختَر الصوت المطلوب من القائمة:",
        reply_markup=voice_keyboard()
    )


# ========= أزرار القائمة =========
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        user_id = call.from_user.id
        chat_id = call.message.chat.id
        data = call.data
        bot.answer_callback_query(call.id)

        if data == "home":
            send_home(chat_id, user_id)
            return

        if data == "balance":
            balance = get_balance(user_id)
            if balance is None:
                text = "💰 رصيدك غير محدود ♾️"
            else:
                text = f"💰 رصيدك: {balance} نقطة"
            bot.send_message(chat_id, text, reply_markup=main_keyboard())
            return

        if data == "voices":
            bot.send_message(
                chat_id,
                "🎙️ اختَر الصوت:",
                reply_markup=voice_keyboard()
            )
            return

        key = (chat_id, user_id)
        with text_lock:
            text = user_texts.get(key)

        if not text:
            bot.send_message(
                chat_id,
                "❗ أرسل النص الذي تريد تحويله أولاً."
            )
            return

        if data == "voice_all":
            bot.send_message(
                chat_id,
                "🔊 سأحوّل النص بالأصوات بالترتيب. "
                "قد يستغرق ذلك وقتاً وقد ينفد رصيدك."
            )
            for voice_key in VOICES:
                balance = get_balance(user_id)
                if balance is not None and balance < VOICE_COST:
                    bot.send_message(chat_id, "انتهى رصيدك، توقفت التحويلات.")
                    break
                convert_voice(chat_id, user_id, voice_key, text)
            return

        if data in VOICES:
            threading.Thread(
                target=convert_voice,
                args=(chat_id, user_id, data, text),
                daemon=True
            ).start()

    except Exception:
        logging.exception("خطأ بمعالجة زر")
        try:
            bot.send_message(
                call.message.chat.id,
                "صار خطأ بمعالجة الزر. جرّب مرة ثانية."
            )
        except Exception:
            pass


# ========= تشغيل وتشخيص =========
if __name__ == "__main__":
    print("Sajjad Voice Bot - بدء التشغيل", flush=True)
    try:
        init_db()
        print("قاعدة البيانات جاهزة.", flush=True)

        me = bot.get_me()
        print(f"تم الاتصال بتيليجرام: @{me.username}", flush=True)
        print("البوت يعمل الآن. لا تغلق Pydroid 3.", flush=True)

        bot.infinity_polling(
            skip_pending=True,
            timeout=30,
            long_polling_timeout=30
        )

    except KeyboardInterrupt:
        print("تم إيقاف البوت يدوياً.", flush=True)
    except Exception as e:
        logging.exception("فشل تشغيل البوت")
        print(
            f"❌ خطأ تشغيل: {type(e).__name__}: {e}",
            flush=True
        )
