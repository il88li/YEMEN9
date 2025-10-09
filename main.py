import telebot
import requests
import random
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request
import threading
import time
from google import genai

# تهيئة Flask app للويب هووك
app = Flask(__name__)

# APIs
SeedReam = "https://sii3.top/api/SeedReam-4.php"
PromptAPI = "https://sii3.top/api/prompt-img.php?text="

# Token البوت و Gemini API
BOT_TOKEN = "8228285723:AAGLH7ljG2lyMQ6SaMVZVqf-Y44zVdMLDRo"
GEMINI_API_KEY = "AIzaSyABlAHgp2wpiH3OKzOHq2QKiI2xjIQaPAE"

# تهيئة العميل Gemini
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

T = telebot.TeleBot(BOT_TOKEN)

# قناة الاشتراك الإجباري
CHANNEL_USERNAME = "@iIl337"

# تخزين المستخدمين
user_photos = {}
user_action = {}

# قائمة الرموز التعبيرية العشوائية
emojis = ["🪺", "🌴", "🍋", "😕", "🌼", "🔔", "🌻", "👋", "🌳", "🍀", "🌾", "🍻", "🍹", "🥝", "🟡", "🍍", "🖤", "🪵", "🏝️", "♥️", "❣️", "❤️‍🩹", "🫒", "🌚", "🍒", "🫀"]

def get_random_emoji():
    """إرجاع رمز تعبيري عشوائي"""
    return random.choice(emojis)

def check_subscription(user_id):
    """التحقق من اشتراك المستخدم في القناة"""
    try:
        chat_member = T.get_chat_member(CHANNEL_USERNAME, user_id)
        return chat_member.status in ['creator', 'administrator', 'member']
    except:
        return False

def send_request(t, l=[]):
    """إرسال طلب إلى API SeedReam"""
    return requests.post(SeedReam, data={"text": t, "links": ",".join(l)}).json().get("image")

def generate_prompt(text):
    """إنشاء برومبت باستخدام الذكاء الاصطناعي"""
    try:
        # استخدام API لإنشاء البرومبت مع التعامل مع الأخطاء
        response = requests.get(f"{PromptAPI}{requests.utils.quote(text)}", timeout=10)
        if response.status_code == 200 and response.text.strip():
            # محاولة تحليل الاستجابة كـ JSON
            try:
                data = json.loads(response.text)
                # استخراج النص من حقل response فقط
                if "response" in data:
                    return data["response"].strip()
                else:
                    return response.text.strip()
            except:
                # إذا لم تكن JSON، نستخدم النص كما هو
                return response.text.strip()
        else:
            # إنشاء وصف بديل إذا فشل API
            return f"صورة عالية الجودة ودقيقة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."
    except Exception as e:
        # إنشاء وصف بديل في حالة الخطأ
        return f"صورة عالية الجودة ودقيقة لل: {text}. تفاصيل واقعية، ألوان زاهية، إضاءة احترافية، دقة 4K."

def generate_edit_prompt(text):
    """إنشاء برومبت تعديل باستخدام Gemini"""
    try:
        response = gemini_client.models.generate_content(
            model="gemini-2.5-flash", 
            contents=f"أنت مساعد محترف في إنشاء مطالبات تعديل الصور. أنشئ مطالبة تعديل احترافية باللغة العربية بناءً على الطلب التالي: {text}. يجب أن تكون المطالبة مفصلة وتصف التعديلات المطلوبة بدقة."
        )
        return response.text.strip()
    except Exception as e:
        return f"مطالبة تعديل احترافية لل: {text}. تحسين الجودة، تعديل الألوان، تحسين التفاصيل، إضاءة مثالية."

# معالجة الأوامر والرسائل
@T.message_handler(commands=['start'])
def start_cmd(m):
    """معالج أمر البدء"""
    uid = m.from_user.id
    
    # التحقق من الاشتراك في القناة
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً لاستخدام البوت:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"إنشاء مطالبة {emoji1}", callback_data="create_prompt_menu"),
        InlineKeyboardButton(f"خدمات البوت {emoji2}", callback_data="bot_services")
    )
    T.send_message(uid, "أهلاً! أنا @TeSi7_BOT الذكاء الاصطناعي الخاص بك لإنشاء المطالبات والصور 🌴", reply_markup=markup)

@T.callback_query_handler(func=lambda c: c.data == "check_subscription")
def check_subscription_callback(c):
    """التحقق من الاشتراك عند الضغط على الزر"""
    uid = c.from_user.id
    
    if check_subscription(uid):
        markup = InlineKeyboardMarkup(row_width=1)
        emoji1 = get_random_emoji()
        emoji2 = get_random_emoji()
        markup.add(
            InlineKeyboardButton(f"إنشاء مطالبة {emoji1}", callback_data="create_prompt_menu"),
            InlineKeyboardButton(f"خدمات البوت {emoji2}", callback_data="bot_services")
        )
        try:
            T.edit_message_text("أهلاً! أنا @TeSi7_BOT الذكاء الاصطناعي الخاص بك لإنشاء المطالبات والصور 🌴", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            pass
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ لم تشترك بعد في القناة:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            pass

@T.callback_query_handler(func=lambda c: c.data == "create_prompt_menu")
def create_prompt_menu(c):
    """قائمة إنشاء المطالبات"""
    uid = c.from_user.id
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            pass
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"مطالبة إنشاء {emoji1}", callback_data="create_prompt_type"),
        InlineKeyboardButton(f"مطالبة تعديل {emoji2}", callback_data="edit_prompt_type"),
        InlineKeyboardButton("رجوع 🔙", callback_data="back_to_main")
    )
    try:
        T.edit_message_text("اختر نوع المطالبة التي تريد إنشاءها:", c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data == "bot_services")
def bot_services(c):
    """قائمة خدمات البوت"""
    uid = c.from_user.id
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            pass
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"إنشاء صورة {emoji1}", callback_data="create_img"),
        InlineKeyboardButton(f"تعديل صورة {emoji2}", callback_data="edit_img"),
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
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            pass
        return
    
    markup = InlineKeyboardMarkup(row_width=1)
    emoji1 = get_random_emoji()
    emoji2 = get_random_emoji()
    markup.add(
        InlineKeyboardButton(f"إنشاء مطالبة {emoji1}", callback_data="create_prompt_menu"),
        InlineKeyboardButton(f"خدمات البوت {emoji2}", callback_data="bot_services")
    )
    try:
        T.edit_message_text("أهلاً! أنا @TeSi7_BOT الذكاء الاصطناعي الخاص بك لإنشاء المطالبات والصور 🌴", 
                          c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.callback_query_handler(func=lambda c: c.data in ["create_prompt_type", "edit_prompt_type", "create_img", "edit_img"])
def action_select(c):
    """اختيار نوع الخدمة"""
    uid = c.from_user.id
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            pass
        return
    
    user_action[c.from_user.id] = c.data
    
    if c.data == "create_prompt_type":
        text = "أرسل وصف الصورة لإنشاء مطالبة إنشاء احترافية"
        back_data = "create_prompt_menu"
    elif c.data == "edit_prompt_type":
        text = "أرسل وصف التعديل المطلوب لإنشاء مطالبة تعديل احترافية"
        back_data = "create_prompt_menu"
    elif c.data == "create_img":
        text = "أرسل وصف الصورة"
        back_data = "bot_services"
    else:  # edit_img
        text = "أرسل الصورة (الحد الأقصى 4)"
        back_data = "bot_services"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("رجوع 🔙", callback_data=back_data))
    
    try:
        T.edit_message_text(text, c.message.chat.id, c.message.message_id, reply_markup=markup)
    except:
        pass

@T.message_handler(content_types=['photo'])
def handle_photos(m):
    """معالجة الصور المرسلة للتعديل"""
    uid = m.from_user.id
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
    if user_action.get(uid) != "edit_img":
        return
        
    user_photos.setdefault(uid, []).append(m.photo[-1].file_id)
    if len(user_photos[uid]) > 4:
        user_photos[uid] = user_photos[uid][:4]
    if len(user_photos[uid]) == 1:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("رجوع 🔙", callback_data="bot_services"))
        T.send_message(uid, "أرسل وصف التعديل", reply_markup=markup)

@T.message_handler(func=lambda m: True)
def handle_description(m):
    """معالجة النصوص المرسلة"""
    uid = m.from_user.id
    
    # التحقق من الاشتراك في القناة
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
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
        markup.add(InlineKeyboardButton("العودة للخدمات 🔙", callback_data="bot_services"))
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
        markup.add(InlineKeyboardButton("العودة للخدمات 🔙", callback_data="bot_services"))
        T.send_message(uid, "تم الانتهاء من الإنشاء! 🎉", reply_markup=markup)
        
    elif action == "create_prompt_type":
        # معالجة إنشاء برومبت الإنشاء
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        prompt_text = m.text
        
        # إنشاء البرومبت باستخدام الذكاء الاصطناعي
        generated_prompt = generate_prompt(prompt_text)
        
        # إرسال البرومبت فقط بشكل ماركداون
        T.send_message(uid, f"```\n{generated_prompt}\n```", parse_mode="Markdown")
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للقائمة 🔙", callback_data="create_prompt_menu"))
        T.send_message(uid, "تم إنشاء مطالبة الإنشاء بنجاح! 🎉", reply_markup=markup)
        
    elif action == "edit_prompt_type":
        # معالجة إنشاء برومبت التعديل باستخدام Gemini
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        prompt_text = m.text
        
        # إنشاء البرومبت باستخدام Gemini
        generated_prompt = generate_edit_prompt(prompt_text)
        
        # إرسال البرومبت فقط بشكل ماركداون
        T.send_message(uid, f"```\n{generated_prompt}\n```", parse_mode="Markdown")
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)
        
        # إظهار زر العودة بعد الانتهاء
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("العودة للقائمة 🔙", callback_data="create_prompt_menu"))
        T.send_message(uid, "تم إنشاء مطالبة التعديل بنجاح! 🎉", reply_markup=markup)

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
