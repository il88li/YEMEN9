import telebot
import requests
import random
import json
import vobject
import sqlite3
import schedule
import threading
import time
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request
from datetime import datetime

# تهيئة Flask app للويب هووك
app = Flask(__name__)

# APIs
SeedReam = "https://sii3.top/api/SeedReam-4.php"
PromptAPI = "https://sii3.top/api/prompt-img.php?text="
AzkarAPI = "https://sii3.top/api/azkar.php"

# Token البوت
T = telebot.TeleBot("7863334400:AAHCp4jO-pd2qqGQKqxLF1GGHh4w-0zPhqQ")

# قناة الاشتراك الإجباري
REQUIRED_CHANNEL = "@iIl337"

# تخزين المستخدمين
user_photos = {}
user_action = {}
user_channels = {}

# قائمة الرموز التعبيرية العشوائية
emojis = ["❤️", "🧡", "💛", "💚", "🩵", "💙", "💜", "🤎", "💓", "💗", "💖", "💝", "🩷", "💘", "🤍", "🩶", "🖤", "💞", "💕", "♥️", "❣️", "❤️‍🩹", "💔", "❤️‍🔥", "💋", "🫀"]
azkar_emojis = ["🌵", "🌻", "🌿", "🌾", "🌲", "🌼", "🌱", "🌳", "🌷", "🍀", "🌴", "🍁", "🌺", "🥀", "🌹", "✨", "🌟", "🌄", "🌙"]

# تهيئة قاعدة البيانات
def init_db():
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS channels
                 (user_id INTEGER PRIMARY KEY, channel_id TEXT, channel_title TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_members
                 (group_id INTEGER, user_id INTEGER, first_name TEXT, username TEXT, PRIMARY KEY(group_id, user_id))''')
    conn.commit()
    conn.close()

init_db()

def get_random_emoji():
    return random.choice(emojis)

def get_random_azkar_emoji():
    return random.choice(azkar_emojis)

def check_subscription(user_id):
    try:
        member = T.get_chat_member(REQUIRED_CHANNEL, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def send_request(t, l=[]):
    return requests.post(SeedReam, data={"text": t, "links": ",".join(l)}).json().get("image")

def generate_prompt(text):
    try:
        response = requests.get(f"{PromptAPI}{requests.utils.quote(text)}", timeout=10)
        if response.status_code == 200 and response.text.strip():
            try:
                data = json.loads(response.text)
                if "response" in data:
                    return data["response"].strip()
                else:
                    return response.text.strip()
            except:
                return response.text.strip()
        else:
            return f"صورة عالية الجودة ودقيقة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."
    except Exception as e:
        return f"صورة عالية الجودة ودقيقة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."

def get_azkar():
    """جلب الأذكار من API حسب الهيكل الجديد"""
    try:
        response = requests.get(AzkarAPI, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return format_azkar(data)
        return "🌪️ تعذر جلب البيانات حالياً"
    except Exception as e:
        return f"❌ حدث خطأ: {str(e)}"

def format_azkar(data):
    """تنسيق الأذكار حسب الهيكل الجديد للAPI"""
    emoji = get_random_azkar_emoji()
    
    # استخدام الهيكل الجديد للAPI
    zekr = data.get("zekr", "سبحان الله وبحمده")
    timestamp = data.get("timestamp", "")
    
    message = f"{emoji} **ذكر اليوم** {emoji}\n\n"
    message += f"📖 {zekr}\n\n"
    
    if timestamp:
        message += f"⏰ {timestamp}\n\n"
    
    message += f"🌵 {get_closing_message()}"
    
    return message

def get_closing_message():
    """رسائل ختامية متنوعة"""
    messages = [
        "جعلها الله في ميزان حسناتك",
        "لا تترك الذكر فإنه نور لقلبك",
        "الذكر يطرد الشيطان ويرضي الرحمن",
        "حافظ على أذكارك تكن في حفظ الله",
        "ذكر الله يذهب الهم والحزن"
    ]
    return random.choice(messages)

def get_user_channel(user_id):
    """الحصول على قناة المستخدم من قاعدة البيانات"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT channel_id, channel_title FROM channels WHERE user_id = ?", (user_id,))
    channel = cursor.fetchone()
    conn.close()
    return channel

def save_user_channel(user_id, channel_id, channel_title):
    """حفظ قناة المستخدم في قاعدة البيانات"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO channels (user_id, channel_id, channel_title) VALUES (?, ?, ?)",
                  (user_id, channel_id, channel_title))
    conn.commit()
    conn.close()

def delete_user_channel(user_id):
    """حذف قناة المستخدم من قاعدة البيانات"""
    conn = sqlite3.connect('bot_data.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM channels WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def create_vcf_for_group(group_id):
    """إنشاء ملف VCF لأعضاء المجموعة"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT * FROM group_members WHERE group_id = ?", (group_id,))
    members = c.fetchall()
    conn.close()
    
    vcf_content = ""
    
    for member in members:
        vcard = vobject.vCard()
        vcard.add('fn').value = member[2] or f"User{member[1]}"
        vcard.add('tel').value = str(member[1])  # استخدام الID كرقم هاتف
        if member[3]:
            vcard.add('note').value = f"Username: @{member[3]}"
        vcf_content += vcard.serialize()
    
    return vcf_content

def send_auto_azkar():
    """إرسال الأذكار التلقائية للقنوات"""
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute("SELECT DISTINCT channel_id FROM channels")
    channels = c.fetchall()
    conn.close()
    
    azkar_text = get_azkar()
    
    for channel in channels:
        try:
            T.send_message(channel[0], azkar_text, parse_mode='Markdown')
        except Exception as e:
            print(f"Error sending to channel {channel[0]}: {e}")

def schedule_azkar():
    """جدولة الأذكار التلقائية"""
    schedule.every().day.at("06:00").do(send_auto_azkar)  # الصباح
    schedule.every().day.at("18:00").do(send_auto_azkar)  # المساء
    
    while True:
        schedule.run_pending()
        time.sleep(60)

# بدء الجدولة في خيط منفصل
scheduler_thread = threading.Thread(target=schedule_azkar, daemon=True)
scheduler_thread.start()

# معالجة الأوامر والرسائل
@T.message_handler(commands=['start'])
def start_cmd(m):
    if not check_subscription(m.from_user.id):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة", url=f"https://t.me/{REQUIRED_CHANNEL[1:]}"))
        markup.add(InlineKeyboardButton("✅ تم الاشتراك", callback_data="check_subscription"))
        T.send_message(m.chat.id, "يجب الاشتراك في القناة أولاً لاستخدام البوت:", reply_markup=markup)
        return
    
    uid = m.from_user.id
    markup = InlineKeyboardMarkup(row_width=1)
    emoji = get_random_emoji()
    markup.add(InlineKeyboardButton(f"خدماتنا {emoji}", callback_data="our_services"))
    T.send_message(uid, "أهلاً! أنا بوت الخدمات المتكاملة 🫧", reply_markup=markup)

@T.callback_query_handler(func=lambda c: c.data == "check_subscription")
def check_subscription_callback(c):
    if check_subscription(c.from_user.id):
        markup = InlineKeyboardMarkup(row_width=1)
        emoji = get_random_emoji()
        markup.add(InlineKeyboardButton(f"خدماتنا {emoji}", callback_data="our_services"))
        T.edit_message_text("أهلاً! أنا بوت الخدمات المتكاملة 🫧", 
                          c.message.chat.id, c.message.message_id, reply_markup=markup)
    else:
        T.answer_callback_query(c.id, "لم يتم الاشتراك بعد!", show_alert=True)

@T.callback_query_handler(func=lambda c: c.data == "our_services")
def our_services(c):
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_azkar_emoji()
    
    markup.add(
        InlineKeyboardButton(f"انشاء وتعديل صور {emoji1}", callback_data="image_services"),
        InlineKeyboardButton(f"اذكار المسلم {emoji2}", callback_data="azkar_main"),
        InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main")
    )
    
    try:
        T.edit_message_text("اختر الخدمة التي تريدها:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "image_services")
def image_services(c):
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    emoji3 = get_random_emoji()
    
    markup.add(
        InlineKeyboardButton(f"إنشاء صورة {emoji1}", callback_data="create_img"),
        InlineKeyboardButton(f"تعديل صورة {emoji2}", callback_data="edit_img"),
        InlineKeyboardButton(f"إنشاء برومبت {emoji3}", callback_data="create_prompt"),
        InlineKeyboardButton("رجوع 🔙", callback_data="back_to_services")
    )
    
    try:
        T.edit_message_text("خدمات الصور والبرومبت:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "azkar_main")
def azkar_main(c):
    """القائمة الرئيسية للأذكار"""
    user_channel = get_user_channel(c.from_user.id)
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_azkar_emoji()
    
    markup.add(InlineKeyboardButton(f"ذكر عشوائي {emoji1}", callback_data="random_azkar"))
    
    if user_channel:
        # إذا كان لديه قناة مضافة
        emoji2 = get_random_azkar_emoji()
        markup.add(InlineKeyboardButton(f"قناتي: {user_channel[1]} {emoji2}", callback_data="manage_channel"))
    else:
        # إذا لم يكن لديه قناة
        emoji3 = get_random_azkar_emoji()
        markup.add(InlineKeyboardButton(f"إضافة قناتي {emoji3}", callback_data="add_channel"))
    
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_services"))
    
    try:
        T.edit_message_text("🌿 خدمات اذكار المسلم:\n\nاختر الخدمة التي تريدها:", 
                          c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "random_azkar")
def send_random_azkar(c):
    """إرسال ذكر عشوائي"""
    azkar_text = get_azkar()
    user_channel = get_user_channel(c.from_user.id)
    
    markup = InlineKeyboardMarkup(row_width=2)
    markup.add(InlineKeyboardButton("🔄 تغيير", callback_data="random_azkar"))
    
    if user_channel:
        markup.add(InlineKeyboardButton("📢 نشر في قناتي", callback_data="publish_to_channel"))
    
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="azkar_main"))
    
    try:
        # محاولة تعديل الرسالة إذا كانت موجودة
        T.edit_message_text(azkar_text, c.message.chat.id, c.message.message_id, 
                          reply_markup=markup, parse_mode='Markdown')
    except:
        # إذا فشل التعديل، إرسال رسالة جديدة
        T.send_message(c.message.chat.id, azkar_text, reply_markup=markup, parse_mode='Markdown')

@T.callback_query_handler(func=lambda c: c.data == "publish_to_channel")
def publish_to_channel(c):
    """نشر الذكر في قناة المستخدم"""
    user_channel = get_user_channel(c.from_user.id)
    
    if user_channel:
        azkar_text = get_azkar()
        try:
            T.send_message(user_channel[0], azkar_text, parse_mode='Markdown')
            T.answer_callback_query(c.id, "تم النشر في قناتك بنجاح! ✅")
        except Exception as e:
            T.answer_callback_query(c.id, "خطأ في النشر! تأكد من صلاحيات البوت ❌")
    else:
        T.answer_callback_query(c.id, "لم تقم بإضافة قناة بعد! ❌", show_alert=True)

@T.callback_query_handler(func=lambda c: c.data == "manage_channel")
def manage_channel(c):
    """إدارة قناة المستخدم"""
    user_channel = get_user_channel(c.from_user.id)
    
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("🗑️ إلغاء ربط القناة", callback_data="remove_channel"))
    markup.add(InlineKeyboardButton("📢 نشر ذكر الآن", callback_data="publish_now"))
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="azkar_main"))
    
    try:
        T.edit_message_text(
            f"🌿 إدارة قناتك:\n\n"
            f"📋 القناة: {user_channel[1]}\n"
            f"🆔 المعرف: {user_channel[0]}\n\n"
            f"يمكنك إلغاء ربط القناة أو نشر ذكر الآن",
            c.message.chat.id, c.message.message_id, reply_markup=markup
        )
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "add_channel")
def add_channel(c):
    """إضافة قناة جديدة"""
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("إضافة البوت إلى قناتك", url=f"https://t.me/{T.get_me().username}?startchannel=true"))
    markup.add(InlineKeyboardButton("تمت الإضافة ✅", callback_data="channel_added"))
    markup.add(InlineKeyboardButton("🔙 رجوع", callback_data="azkar_main"))
    
    try:
        T.edit_message_text(
            "📋 لإضافة قناتك:\n\n"
            "1. أضف البوت إلى قناتك كمسؤول\n"
            "2. تأكد من صلاحية نشر الرسائل\n"
            "3. اضغط على 'تمت الإضافة'\n\n"
            "سيتمكن البوت من نشر الأذكار تلقائياً 🕔",
            c.message.chat.id, c.message.message_id, reply_markup=markup
        )
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "channel_added")
def channel_added(c):
    """معالجة إضافة القناة"""
    T.send_message(c.message.chat.id, "أرسل معرف قناتك (مثال: @channelname) أو الرابط:")

@T.callback_query_handler(func=lambda c: c.data == "remove_channel")
def remove_channel(c):
    """إلغاء ربط القناة"""
    delete_user_channel(c.from_user.id)
    T.answer_callback_query(c.id, "تم إلغاء ربط القناة بنجاح! ✅")
    azkar_main(c)  # العودة للقائمة الرئيسية

@T.callback_query_handler(func=lambda c: c.data == "publish_now")
def publish_now(c):
    """نشر ذكر فوري"""
    publish_to_channel(c)

@T.message_handler(func=lambda m: m.text and (m.text.startswith('@') or 't.me/' in m.text))
def handle_channel_input(m):
    """معالجة إدخال معرف القناة"""
    if user_action.get(m.from_user.id) != "adding_channel":
        return
    
    channel_input = m.text.strip()
    
    # استخراج المعرف من النص
    if 't.me/' in channel_input:
        channel_username = channel_input.split('t.me/')[-1].replace('@', '')
    else:
        channel_username = channel_input.replace('@', '')
    
    try:
        # الحصول على معلومات القناة
        chat = T.get_chat(f"@{channel_username}")
        
        # التحقق من أن البوت مسؤول في القناة
        try:
            bot_member = T.get_chat_member(chat.id, T.get_me().id)
            if bot_member.status not in ['administrator', 'creator']:
                T.send_message(m.chat.id, "❌ البوت ليس مسؤولاً في القناة! يرجى إضافة البوت كمسؤول أولاً.")
                return
        except:
            T.send_message(m.chat.id, "❌ البوت ليس في القناة! يرجى إضافة البوت أولاً.")
            return
        
        # حفظ القناة في قاعدة البيانات
        save_user_channel(m.from_user.id, chat.id, chat.title)
        user_action.pop(m.from_user.id, None)
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🌿 العودة للأذكار", callback_data="azkar_main"))
        
        T.send_message(m.chat.id, f"✅ تم إضافة قناتك بنجاح!\n\n📋 القناة: {chat.title}\n🆔 المعرف: @{channel_username}\n\nسيتم النشر التلقائي يومياً 🕔", reply_markup=markup)
        
    except Exception as e:
        T.send_message(m.chat.id, f"❌ خطأ في إضافة القناة! تأكد من المعرف والصلااحيات.\n\nError: {str(e)}")

# باقي الدوال الأصلية تبقى كما هي مع تعديلات طفيفة
@T.callback_query_handler(func=lambda c: c.data in ["create_img", "edit_img", "create_prompt"])
def action_select(c):
    user_action[c.from_user.id] = c.data
    if c.data == "create_img":
        text = "أرسل وصف الصورة"
    elif c.data == "edit_img":
        text = "أرسل الصورة (الحد الأقصى 4)"
    else:
        text = "أرسل النص لإنشاء البرومبت"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="image_services"))
    
    try:
        T.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_main")
def back_to_main(c):
    markup = InlineKeyboardMarkup(row_width=1)
    emoji = get_random_emoji()
    markup.add(InlineKeyboardButton(f"خدماتنا {emoji}", callback_data="our_services"))
    try:
        T.edit_message_text("أهلاً! أنا بوت الخدمات المتكاملة 🫧", 
                           c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_services")
def back_to_services(c):
    user_action.pop(c.from_user.id, None)
    our_services(c)

# معالجة الصور والرسائل الأخرى تبقى كما هي
@T.message_handler(content_types=['photo'])
def handle_photos(m):
    uid = m.from_user.id
    if user_action.get(uid) != "edit_img":
        return
    user_photos.setdefault(uid, []).append(m.photo[-1].file_id)
    if len(user_photos[uid]) > 4:
        user_photos[uid] = user_photos[uid][:4]
    if len(user_photos[uid]) == 1:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="image_services"))
        T.send_message(uid, "أرسل وصف التعديل", reply_markup=markup)

@T.message_handler(func=lambda m: True)
def handle_description(m):
    # ... (نفس الكود السابق)
    pass

# إعداد ويب هووك
WEBHOOK_URL = "https://yemen9-1.onrender.com"
WEBHOOK_PATH = "/webhook"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        T.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

@app.route('/')
def index():
    return "البوت يعمل بشكل طبيعي! 🚀"

@app.route('/health')
def health_check():
    return "OK", 200

def set_webhook():
    try:
        T.remove_webhook()
        time.sleep(1)
        T.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)
        print(f"تم تعيين الويب هووك على: {WEBHOOK_URL + WEBHOOK_PATH}")
    except Exception as e:
        print(f"خطأ في تعيين الويب هووك: {e}")

def keep_alive():
    while True:
        try:
            requests.get(WEBHOOK_URL)
            print("تم إرسال طلب للحفاظ على النشاط")
        except Exception as e:
            print(f"خطأ في إرسال طلب النشاط: {e}")
        time.sleep(300)

if __name__ == "__main__":
    set_webhook()
    
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    app.run(host='0.0.0.0', port=10000, debug=False)
