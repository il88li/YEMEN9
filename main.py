import telebot
import requests
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request
import threading
import time

# تهيئة Flask app للويب هووك
app = Flask(__name__)

# APIs
SeedReam = "https://sii3.top/api/SeedReam-4.php"
PromptAPI = "https://sii3.top/api/prompt-img.php?text="

# Token البوت
T = telebot.TeleBot("7863334400:AAHCp4jO-pd2qqGQKqxLF1GGHh4w-0zPhqQ")

# تخزين المستخدمين
user_photos = {}
user_action = {}

# قائمة الرموز التعبيرية العشوائية
emojis = ["❤️", "🧡", "💛", "💚", "🩵", "💙", "💜", "🤎", "💓", "💗", "💖", "💝", "🩷", "💘", "🤍", "🩶", "🖤", "💞", "💕", "♥️", "❣️", "❤️‍🩹", "💔", "❤️‍🔥", "💋", "🫀"]

def get_random_emoji():
    """إرجاع رمز تعبيري عشوائي"""
    return random.choice(emojis)

def send_request(t, l=[]):
    """إرسال طلب إلى API SeedReam"""
    return requests.post(SeedReam, data={"text": t, "links": ",".join(l)}).json().get("image")

def generate_prompt(text):
    """إنشاء برومبت باستخدام الذكاء الاصطناعي"""
    try:
        # استخدام API لإنشاء البرومبت
        response = requests.get(f"https://si13.top/api/prompt-img.php?text={requests.utils.quote(text)}")
        if response.status_code == 200:
            return response.text
        else:
            return f"# البرومبت المُنشئ:\n\n**الفكرة الأصلية:** {text}\n\n**الوصف المُفصل:**\nتم إنشاء وصف مفصل للصورة بناءً على طلبك. يمكنك استخدام هذا النص لتوليد الصور باستخدام الذكاء الاصطناعي."
    except Exception as e:
        return f"# البرومبت المُنشئ:\n\n**الفكرة الأصلية:** {text}\n\n**الوصف المُفصل:**\nحدث خطأ في إنشاء البرومبت: {str(e)}"

# معالجة الأوامر والرسائل
@T.message_handler(commands=['start'])
def start_cmd(m):
    """معالج أمر البدء"""
    uid = m.from_user.id
    markup = InlineKeyboardMarkup(row_width=1)
    emoji = get_random_emoji()
    markup.add(InlineKeyboardButton(f"خدماتنا {emoji}", callback_data="our_services"))
    T.send_message(uid, "أهلاً! أنا SeedReam 4.0 الذكاء الاصطناعي الخاص بك لإنشاء وتعديل الصور 🫧", reply_markup=markup)

@T.callback_query_handler(func=lambda c: c.data == "our_services")
def our_services(c):
    """عرض قائمة الخدمات"""
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    emoji3 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"إنشاء صورة {emoji1}", callback_data="create_img"),
        InlineKeyboardButton(f"تعديل صورة {emoji2}", callback_data="edit_img"),
        InlineKeyboardButton(f"إنشاء برومبت {emoji3}", callback_data="create_prompt"),
        InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main")
    )
    try:
        T.edit_message_text("اختر الخدمة التي تريدها:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_main")
def back_to_main(c):
    """العودة إلى القائمة الرئيسية"""
    uid = c.from_user.id
    markup = InlineKeyboardMarkup(row_width=1)
    emoji = get_random_emoji()
    markup.add(InlineKeyboardButton(f"خدماتنا {emoji}", callback_data="our_services"))
    try:
        T.edit_message_text("أهلاً! أنا SeedReam 4.0 الذكاء الاصطناعي الخاص بك لإنشاء وتعديل الصور 🫧", 
                           c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data in ["create_img", "edit_img", "create_prompt"])
def action_select(c):
    """اختيار نوع الخدمة"""
    user_action[c.from_user.id] = c.data
    if c.data == "create_img":
        text = "أرسل وصف الصورة"
    elif c.data == "edit_img":
        text = "أرسل الصورة (الحد الأقصى 4)"
    else:  # create_prompt
        text = "أرسل النص لإنشاء البرومبت"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_services"))
    
    try:
        T.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "back_to_services")
def back_to_services(c):
    """العودة إلى قائمة الخدمات"""
    user_action.pop(c.from_user.id, None)
    our_services(c)

@T.message_handler(content_types=['photo'])
def handle_photos(m):
    """معالجة الصور المرسلة للتعديل"""
    uid = m.from_user.id
    if user_action.get(uid) != "edit_img":
        return
    user_photos.setdefault(uid, []).append(m.photo[-1].file_id)
    if len(user_photos[uid]) > 4:
        user_photos[uid] = user_photos[uid][:4]
    if len(user_photos[uid]) == 1:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="back_to_services"))
        T.send_message(uid, "أرسل وصف التعديل", reply_markup=markup)

@T.message_handler(func=lambda m: True)
def handle_description(m):
    """معالجة النصوص المرسلة"""
    uid = m.from_user.id
    action = user_action.get(uid)
    
    if action == "edit_img" and uid in user_photos and user_photos[uid]:
        # معالجة تعديل الصورة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        desc = m.text
        links = [f"https://api.telegram.org/file/bot{T.token}/{T.get_file(fid).file_path}" for fid in user_photos[uid]]
        cap = (desc[:1021] + "...") if len(desc) > 1024 else desc
        
        with ThreadPoolExecutor() as e:
            results = list(e.map(lambda _: send_request(desc, links), range(2)))
        
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
        markup.add(InlineKeyboardButton("العودة للخدمات 🔙", callback_data="our_services"))
        T.send_message(uid, "تم الانتهاء من التعديل! 🎉", reply_markup=markup)
        
    elif action == "create_img":
        # معالجة إنشاء الصورة
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        desc = m.text
        cap = (desc[:1021] + "...") if len(desc) > 1024 else desc
        
        with ThreadPoolExecutor() as e:
            results = list(e.map(lambda _: send_request(desc), range(2)))
        
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
        markup.add(InlineKeyboardButton("العودة للخدمات 🔙", callback_data="our_services"))
        T.send_message(uid, "تم الانتهاء من الإنشاء! 🎉", reply_markup=markup)
        
    elif action == "create_prompt":
        # معالجة إنشاء البرومبت
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        prompt_text = m.text
        
        # إنشاء البرومبت باستخدام الذكاء الاصطناعي
        generated_prompt = generate_prompt(prompt_text)
        
        # إرسال البرومبت كنص ماركداون
        try:
            T.send_message(uid, f"```markdown\n{generated_prompt}\n```", parse_mode="Markdown")
        except:
            # إذا فشل إرسال ماركداون، نرسله كنص عادي
            T.send_message(uid, generated_prompt)
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للخدمات 🔙", callback_data="our_services"))
        T.send_message(uid, "تم إنشاء البرومبت بنجاح! 🎉", reply_markup=markup)

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

