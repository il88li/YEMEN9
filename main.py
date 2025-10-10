import telebot
import requests
import random
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request
import threading
import time

# تهيئة Flask app للويب هووك
app = Flask(__name__)

# APIs
SeedReam = "https://sii3.top/api/SeedReam-4.php"
DeepSeek_API = "https://sii3.top/api/deepseek.php"

# Token البوت
T = telebot.TeleBot("7863334400:AAHDS2IuKno0tmU4tAQZ1E5avGDQlQe3o0g")

# تخزين المستخدمين
user_photos = {}
user_action = {}

# قائمة الرموز التعبيرية العشوائية
emojis = ["🪺", "🌴", "🍋", "😕", "🌼", "🔔", "🌻", "👋", "🌳", "🍀", "🌾", "🍻", "🍹", "🥝", "🟡", "🍍", "🖤", "🪵", "🏝️", "♥️", "❣️", "❤️‍🩹", "🫒", "🌚", "🍒", "🫀"]

# قناة الاشتراك الإجباري
CHANNEL_USERNAME = "@iIl337"

def check_subscription(user_id):
    """فحص إذا كان المستخدم مشترك في القناة"""
    try:
        chat_member = T.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['creator', 'administrator', 'member']
    except:
        return False

def get_random_emoji():
    """إرجاع رمز تعبيري عشوائي"""
    return random.choice(emojis)

def send_request(t, l=[]):
    """إرسال طلب إلى API SeedReam"""
    return requests.post(SeedReam, data={"text": t, "links": ",".join(l)}).json().get("image")

def enhance_prompt(text):
    """تحسين البرومبت باستخدام DeepSeek API"""
    try:
        # استخدام API DeepSeek لتحسين البرومبت
        params = {"v3": f"قم بتحسين هذا الوصف لإنشاء صورة: {text}. اجعله مفصلاً وواضحاً ومناسباً لإنتاج صور بدقة عالية وجودة ممتازة مع تفاصيل واقعية وألوان زاهية وإضاءة احترافية"}
        response = requests.get(f"{DeepSeek_API}", params=params, timeout=15)
        
        if response.status_code == 200 and response.text.strip():
            return response.text.strip()
        else:
            # وصف بديل في حالة فشل API
            return f"صورة عالية الجودة وواضحة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K، تفاصيل دقيقة، تركيز حاد"
    except Exception as e:
        # وصف بديل في حالة الخطأ
        return f"صورة عالية الجودة وواضحة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K، تفاصيل دقيقة، تركيز حاد"

# معالجة الأوامر والرسائل
@T.message_handler(commands=['start'])
def start_cmd(m):
    """معالج أمر البدء"""
    uid = m.from_user.id
    
    # فحص الاشتراك في القناة
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("انضم للقناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        T.send_message(uid, f"⚠️ يجب الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"إنشاء/تعديل صور {emoji1}", callback_data="create_edit_images"),
        InlineKeyboardButton(f"إنشاء مطالبات {emoji2}", callback_data="create_prompts")
    )
    T.send_message(uid, "أهلاً! أنا SeedReam 4.0 الذكاء الاصطناعي الخاص بك لإنشاء وتعديل الصور 🌴", reply_markup=markup)

@T.callback_query_handler(func=lambda c: c.data == "check_subscription")
def check_subscription_callback(c):
    """فحص الاشتراك مرة أخرى"""
    uid = c.from_user.id
    if check_subscription(uid):
        start_cmd(c.message)
    else:
        T.answer_callback_query(c.id, "لم تشترك بعد في القناة! ⚠️", show_alert=True)

@T.callback_query_handler(func=lambda c: c.data == "create_edit_images")
def create_edit_images(c):
    """عرض قائمة إنشاء/تعديل الصور"""
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"مطالبة إنشاء {emoji1}", callback_data="create_prompt"),
        InlineKeyboardButton(f"مطالبة تعديل {emoji2}", callback_data="edit_prompt"),
        InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main")
    )
    try:
        T.edit_message_text("اختر نوع المطالبة:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "create_prompts")
def create_prompts(c):
    """بدء إنشاء المطالبات المحسنة"""
    user_action[c.from_user.id] = "create_enhanced_prompt"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main"))
    
    try:
        T.edit_message_text("أرسل النص الذي تريد تحسينه لإنشاء مطالبة صور عالية الجودة:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data in ["create_prompt", "edit_prompt"])
def prompt_type_select(c):
    """اختيار نوع المطالبة"""
    user_action[c.from_user.id] = c.data
    
    if c.data == "create_prompt":
        text = "أرسل وصف الصورة التي تريد إنشاءها"
    else:  # edit_prompt
        text = "أرسل الصورة (الحد الأقصى 4) ثم أرسل وصف التعديل"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_create_edit"))
    
    try:
        T.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_main")
def back_to_main(c):
    """العودة إلى القائمة الرئيسية"""
    uid = c.from_user.id
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"إنشاء/تعديل صور {emoji1}", callback_data="create_edit_images"),
        InlineKeyboardButton(f"إنشاء مطالبات {emoji2}", callback_data="create_prompts")
    )
    try:
        T.edit_message_text("أهلاً! أنا SeedReam 4.0 الذكاء الاصطناعي الخاص بك لإنشاء وتعديل الصور 🌴", 
                           c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_create_edit")
def back_to_create_edit(c):
    """العودة إلى قائمة إنشاء/تعديل الصور"""
    user_action.pop(c.from_user.id, None)
    create_edit_images(c)

@T.message_handler(content_types=['photo'])
def handle_photos(m):
    """معالجة الصور المرسلة للتعديل"""
    uid = m.from_user.id
    
    # فحص الاشتراك
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("انضم للقناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        T.send_message(uid, f"⚠️ يجب الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
    if user_action.get(uid) != "edit_prompt":
        return
        
    user_photos.setdefault(uid, []).append(m.photo[-1].file_id)
    if len(user_photos[uid]) > 4:
        user_photos[uid] = user_photos[uid][:4]
    
    if len(user_photos[uid]) == 1:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_create_edit"))
        T.send_message(uid, f"تم استلام {len(user_photos[uid])} صورة. أرسل وصف التعديل المطلوب", reply_markup=markup)
    else:
        T.send_message(uid, f"تم استلام {len(user_photos[uid])} صور. يمكنك إرسال وصف التعديل الآن")

@T.message_handler(func=lambda m: True)
def handle_description(m):
    """معالجة النصوص المرسلة"""
    uid = m.from_user.id
    
    # فحص الاشتراك
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("انحب للقناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        T.send_message(uid, f"⚠️ يجب الاشتراك في القناة أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
    action = user_action.get(uid)
    
    if action == "edit_prompt" and uid in user_photos and user_photos[uid]:
        # معالجة تعديل الصورة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        desc = m.text
        
        # تحسين البرومبت باستخدام DeepSeek
        enhanced_desc = enhance_prompt(desc)
        
        links = [f"https://api.telegram.org/file/bot{T.token}/{T.get_file(fid).file_path}" for fid in user_photos[uid]]
        cap = (enhanced_desc[:1021] + "...") if len(enhanced_desc) > 1024 else enhanced_desc
        
        with ThreadPoolExecutor() as e:
            results = list(e.map(lambda _: send_request(enhanced_desc, links), range(2)))
        
        media = []
        for i, u in enumerate(results):
            if not u:
                continue
            if i == 0:
                media.append(InputMediaPhoto(media=u, caption=f"<b><blockquote>{cap}</blockquote></b>", parse_mode="HTML", has_spoiler=True))
            else:
                media.append(InputMediaPhoto(media=u, has_spoiler=True))
        
        if media:
            T.send_media_group(uid, media)
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_photos[uid] = []
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للقائمة الرئيسية 🔙", callback_data="back_to_main"))
        T.send_message(uid, "تم الانتهاء من التعديل! 🎉", reply_markup=markup)
        
    elif action == "create_prompt":
        # معالجة إنشاء الصورة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        desc = m.text
        
        # تحسين البرومبت باستخدام DeepSeek
        enhanced_desc = enhance_prompt(desc)
        
        cap = (enhanced_desc[:1021] + "...") if len(enhanced_desc) > 1024 else enhanced_desc
        
        with ThreadPoolExecutor() as e:
            results = list(e.map(lambda _: send_request(enhanced_desc), range(2)))
        
        media = []
        for i, u in enumerate(results):
            if not u:
                continue
            if i == 0:
                media.append(InputMediaPhoto(media=u, caption=f"<b><blockquote>{cap}</blockquote></b>", parse_mode="HTML", has_spoiler=True))
            else:
                media.append(InputMediaPhoto(media=u, has_spoiler=True))
        
        if media:
            T.send_media_group(uid, media)
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للقائمة الرئيسية 🔙", callback_data="back_to_main"))
        T.send_message(uid, "تم الانتهاء من الإنشاء! 🎉", reply_markup=markup)
        
    elif action == "create_enhanced_prompt":
        # معالجة إنشاء المطالبات المحسنة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        prompt_text = m.text
        
        # تحسين البرومبت باستخدام DeepSeek
        enhanced_prompt_text = enhance_prompt(prompt_text)
        
        # إرسال البرومبت المحسن
        T.send_message(uid, f"🎯 **المطالبة المحسنة:**\n\n```\n{enhanced_prompt_text}\n```", parse_mode="Markdown")
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للقائمة الرئيسية 🔙", callback_data="back_to_main"))
        T.send_message(uid, "تم إنشاء المطالبة المحسنة بنجاح! 🎉", reply_markup=markup)

# إعداد ويب هووك
WEBHOOK_URL = "https://yemen9-1.onrender.com"
WEBHOOK_PATH = "/webhook"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    """معالجة الويب هووك"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        T.process_new_updates([update])
        return ''
    else:
        return 'Invalid content type', 403

@app.route('/')
def index():
    """الصفحة الرئيسية للحفاظ على تشغيل التطبيق"""
    return "البوت يعمل بشكل طبيعي! 🚀"

@app.route('/health')
def health_check():
    """فحص صحة التطبيق"""
    return "OK", 200

def set_webhook():
    """تعيين الويب هووك"""
    try:
        T.remove_webhook()
        time.sleep(1)
        T.set_webhook(url=WEBHOOK_URL + WEBHOOK_PATH)
        print(f"تم تعيين الويب هووك على: {WEBHOOK_URL + WEBHOOK_PATH}")
    except Exception as e:
        print(f"خطأ في تعيين الويب هووك: {e}")

def keep_alive():
    """إرسال طلبات دورية للحفاظ على التطبيق نشطاً"""
    while True:
        try:
            requests.get(WEBHOOK_URL)
            print("تم إرسال طلب للحفاظ على النشاط")
        except Exception as e:
            print(f"خطأ في إرسال طلب النشاط: {e}")
        time.sleep(300)  # انتظر 5 دقائق بين كل طلب

if __name__ == "__main__":
    # تعيين الويب هووك عند التشغيل
    set_webhook()
    
    # بدء خيط للحفاظ على النشاط
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # تشغيل تطبيق Flask
    app.run(host='0.0.0.0', port=10000, debug=False)
