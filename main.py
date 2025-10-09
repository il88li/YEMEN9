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
DeepSeekAPI = "https://sii3.top/api/deepseek.php"

# Token البوت
T = telebot.TeleBot("7863334400:AAHDS2IuKno0tmU4tAQZ1E5avGDQlQe3o0g")

# تخزين المستخدمين
user_photos = {}
user_action = {}

# قائمة الرموز التعبيرية العشوائية
emojis = ["🪺", "🌴", "🍋", "😕", "🌼", "🔔", "🌻", "👋", "🌳", "🍀", "🌾", "🍻", "🍹", "🥝", "🟡", "🍍", "🖤", "🪵", "🏝️", "♥️", "❣️", "❤️‍🩹", "🫒", "🌚", "🍒", "🫀"]

def get_random_emoji():
    """إرجاع رمز تعبيري عشوائي"""
    return random.choice(emojis)

def send_request(t, l=[]):
    """إرسال طلب إلى API SeedReam"""
    return requests.post(SeedReam, data={"text": t, "links": ",".join(l)}).json().get("image")

def generate_prompt(text, prompt_type):
    """إنشاء برومبت باستخدام الذكاء الاصطناعي"""
    try:
        # استخدام API DeepSeek لإنشاء البرومبت
        if prompt_type == "create":
            base_prompt = f"قم بتوسيع ووصف هذا النص ليصبح مطالبة مثالية لإنشاء صور واضحة وعالية الدقة: {text}"
        else:  # edit
            base_prompt = f"قم بتوسيع ووصف هذا النص ليصبح مطالبة مثالية لتعديل الصور واضحة وعالية الدقة: {text}"
        
        response = requests.post(DeepSeekAPI, data={"r1": base_prompt}, timeout=10)
        if response.status_code == 200 and response.text.strip():
            return response.text.strip()
        else:
            # إنشاء وصف بديل إذا فشل API
            if prompt_type == "create":
                return f"صورة عالية الجودة ودقيقة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."
            else:
                return f"تعديل الصورة لتصبح: {text}. تحسين الجودة، تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."
    except Exception as e:
        # إنشاء وصف بديل في حالة الخطأ
        if prompt_type == "create":
            return f"صورة عالية الجودة ودقيقة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."
        else:
            return f"تعديل الصورة لتصبح: {text}. تحسين الجودة، تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."

# معالجة الأوامر والرسائل
@T.message_handler(commands=['start'])
def start_cmd(m):
    """معالج أمر البدء"""
    uid = m.from_user.id
    
    # فحص الاشتراك في القناة
    try:
        chat_member = T.get_chat_member('@iIl337', uid)
        if chat_member.status in ['left', 'kicked']:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("اشترك في القناة 🔔", url="https://t.me/iIl337"))
            T.send_message(uid, "❗ يجب الاشتراك في القناة أولاً @iIl337", reply_markup=markup)
            return
    except:
        pass
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"انشاء/تعديل صور {emoji1}", callback_data="create_edit_images"),
        InlineKeyboardButton(f"انشاء مطالبات {emoji2}", callback_data="create_prompts")
    )
    T.send_message(uid, "أهلاً! أنا SeedReam 4.0 الذكاء الاصطناعي الخاص بك لإنشاء وتعديل الصور🌴", reply_markup=markup)

@T.callback_query_handler(func=lambda c: c.data == "create_edit_images")
def create_edit_images(c):
    """عرض قائمة إنشاء/تعديل الصور"""
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"مطالبة انشاء {emoji1}", callback_data="prompt_create"),
        InlineKeyboardButton(f"مطالبة تعديل {emoji2}", callback_data="prompt_edit"),
        InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main")
    )
    try:
        T.edit_message_text("اختر نوع المطالبة:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "create_prompts")
def create_prompts(c):
    """إنشاء مطالبات عامة"""
    user_action[c.from_user.id] = "create_prompt"
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main"))
    
    try:
        T.edit_message_text("أرسل النص الذي تريد إنشاء مطالبة منه:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data in ["prompt_create", "prompt_edit"])
def prompt_type_select(c):
    """اختيار نوع المطالبة للصور"""
    user_action[c.from_user.id] = c.data
    
    if c.data == "prompt_create":
        text = "أرسل وصف الصورة الأساسي وسأقوم بتوسيعه إلى مطالبة مثالية"
    else:  # prompt_edit
        text = "أرسل وصف التعديل الأساسي وسأقوم بتوسيعه إلى مطالبة مثالية"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_images"))
    
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
        InlineKeyboardButton(f"انشاء/تعديل صور {emoji1}", callback_data="create_edit_images"),
        InlineKeyboardButton(f"انشاء مطالبات {emoji2}", callback_data="create_prompts")
    )
    try:
        T.edit_message_text("أهلاً! أنا SeedReam 4.0 الذكاء الاصطناعي الخاص بك لإنشاء وتعديل الصور🌴", 
                           c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_images")
def back_to_images(c):
    """العودة إلى قائمة إنشاء/تعديل الصور"""
    user_action.pop(c.from_user.id, None)
    create_edit_images(c)

@T.message_handler(content_types=['photo'])
def handle_photos(m):
    """معالجة الصور المرسلة للتعديل"""
    uid = m.from_user.id
    
    # فحص الاشتراك في القناة
    try:
        chat_member = T.get_chat_member('@iIl337', uid)
        if chat_member.status in ['left', 'kicked']:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("اشترك في القناة 🔔", url="https://t.me/iIl337"))
            T.send_message(uid, "❗ يجب الاشتراك في القناة أولاً @iIl337", reply_markup=markup)
            return
    except:
        pass
    
    if user_action.get(uid) != "prompt_edit":
        return
        
    user_photos.setdefault(uid, []).append(m.photo[-1].file_id)
    if len(user_photos[uid]) > 4:
        user_photos[uid] = user_photos[uid][:4]
    if len(user_photos[uid]) == 1:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_images"))
        T.send_message(uid, "أرسل وصف التعديل الأساسي وسأقوم بتوسيعه إلى مطالبة مثالية", reply_markup=markup)

@T.message_handler(func=lambda m: True)
def handle_description(m):
    """معالجة النصوص المرسلة"""
    uid = m.from_user.id
    
    # فحص الاشتراك في القناة
    try:
        chat_member = T.get_chat_member('@iIl337', uid)
        if chat_member.status in ['left', 'kicked']:
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("اشترك في القناة 🔔", url="https://t.me/iIl337"))
            T.send_message(uid, "❗ يجب الاشتراك في القناة أولاً @iIl337", reply_markup=markup)
            return
    except:
        pass
    
    action = user_action.get(uid)
    
    if action == "prompt_edit" and uid in user_photos and user_photos[uid]:
        # معالجة تعديل الصورة مع توسيع المطالبة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        desc = m.text
        
        # توسيع المطالبة باستخدام الذكاء الاصطناعي
        expanded_prompt = generate_prompt(desc, "edit")
        
        links = [f"https://api.telegram.org/file/bot{T.token}/{T.get_file(fid).file_path}" for fid in user_photos[uid]]
        cap = (expanded_prompt[:1021] + "...") if len(expanded_prompt) > 1024 else expanded_prompt
        
        with ThreadPoolExecutor() as e:
            results = list(e.map(lambda _: send_request(expanded_prompt, links), range(2)))
        
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
        
    elif action == "prompt_create":
        # معالجة إنشاء الصورة مع توسيع المطالبة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        desc = m.text
        
        # توسيع المطالبة باستخدام الذكاء الاصطناعي
        expanded_prompt = generate_prompt(desc, "create")
        
        cap = (expanded_prompt[:1021] + "...") if len(expanded_prompt) > 1024 else expanded_prompt
        
        with ThreadPoolExecutor() as e:
            results = list(e.map(lambda _: send_request(expanded_prompt), range(2)))
        
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
        
    elif action == "create_prompt":
        # معالجة إنشاء المطالبات العامة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        prompt_text = m.text
        
        # إنشاء المطالبة باستخدام الذكاء الاصطناعي
        generated_prompt = generate_prompt(prompt_text, "create")
        
        # إرسال المطالبة بشكل ماركداون
        T.send_message(uid, f"```\n{generated_prompt}\n```", parse_mode="Markdown")
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للقائمة الرئيسية 🔙", callback_data="back_to_main"))
        T.send_message(uid, "تم إنشاء المطالبة بنجاح! 🎉", reply_markup=markup)

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
