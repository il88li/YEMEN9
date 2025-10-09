import telebot
import requests
import random
import json
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request
import threading
import time
import os

# تهيئة Flask app للويب هووك
app = Flask(__name__)

# APIs
SeedReam = "https://sii3.top/api/SeedReam-4.php"
DEEPSEEK_V3_API = "https://sii3.top/api/deepseek.php?v3="
DEEPSEEK_R1_API = "https://sii3.top/api/deepseek.php?r1="

# Token البوت
BOT_TOKEN = "8293003270:AAGf2GQvucNgi5fLbgBSpPHr-iKmMUp7l9U"
T = telebot.TeleBot(BOT_TOKEN)

# إعداد وقت أطول للطلبات
import requests
requests.adapters.DEFAULT_TIMEOUT = 60

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

def clean_prompt_text(text):
    """تنظيف النص من الرموز البرمجية وحقوق المطورين"""
    # إزالة علامات الكود
    cleaned = text.replace('```', '').replace('`', '').strip()
    
    # إزالة أي حقوق مطورين أو إعلانات
    lines = cleaned.split('\n')
    clean_lines = []
    
    for line in lines:
        # تجاهل الأسطر التي تحتوي على كلمات مثل channel, support, subscribe, إلخ
        lower_line = line.lower()
        if any(word in lower_line for word in ['channel', 'support', 'subscribe', 'developer', 'dev', 'تابع', 'قناة', 'دعم', 'مطور']):
            continue
        # تجاهل الأسطر التي تبدأ بعلامات خاصة
        if line.strip().startswith('***') or line.strip().startswith('---'):
            continue
        clean_lines.append(line)
    
    return '\n'.join(clean_lines).strip()

def send_request(t, l=[]):
    """إرسال طلب إلى API SeedReam مع معالجة أخطاء محسنة"""
    try:
        print(f"Sending request with text: {t}")
        print(f"Links: {l}")
        
        data = {"text": t}
        if l:
            data["links"] = ",".join(l)
        
        response = requests.post(SeedReam, data=data, timeout=60)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"API Response: {result}")
            return result.get("image")
        else:
            print(f"API returned error: {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print("Request timed out")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None

def generate_prompt(text):
    """إنشاء برومبت باستخدام DeepSeek V3"""
    try:
        # استخدام DeepSeek V3 لإنشاء البرومبت باللغة الإنجليزية
        prompt_request = f"Create a detailed professional image generation prompt in English for: {text}. Include details about scene, lighting, colors, composition, atmosphere, and style. Make it comprehensive and suitable for AI image generation."
        response = requests.get(f"{DEEPSEEK_V3_API}{requests.utils.quote(prompt_request)}", timeout=20)
        
        if response.status_code == 200 and response.text.strip():
            clean_prompt = clean_prompt_text(response.text)
            if clean_prompt:
                return clean_prompt
            else:
                return f"Professional photo of {text}, highly detailed, cinematic lighting, 8K resolution, realistic, sharp focus"
        else:
            print(f"API Error: Status {response.status_code}")
            return f"Professional photo of {text}, highly detailed, cinematic lighting, 8K resolution, realistic, sharp focus"
    except Exception as e:
        print(f"Error in generate_prompt: {e}")
        return f"Professional photo of {text}, highly detailed, cinematic lighting, 8K resolution, realistic, sharp focus"

def generate_edit_prompt(text):
    """إنشاء برومبت تعديل باستخدام DeepSeek R1"""
    try:
        # استخدام DeepSeek R1 لإنشاء برومبت التعديل
        prompt_request = f"Create a detailed professional image editing prompt in English for: {text}. Focus on specific modifications, enhancements, color adjustments, lighting changes, and technical improvements for image editing AI models."
        response = requests.post(
            DEEPSEEK_R1_API,
            data={"r1": prompt_request},
            timeout=20
        )
        
        if response.status_code == 200 and response.text.strip():
            clean_prompt = clean_prompt_text(response.text)
            if clean_prompt:
                return clean_prompt
            else:
                return f"Professional image editing for: {text}, enhance quality, improve lighting, adjust colors, refine details"
        else:
            print(f"API Error: Status {response.status_code}")
            return f"Professional image editing for: {text}, enhance quality, improve lighting, adjust colors, refine details"
    except Exception as e:
        print(f"Error in generate_edit_prompt: {e}")
        return f"Professional image editing for: {text}, enhance quality, improve lighting, adjust colors, refine details"

def safe_send_message(chat_id, text, reply_markup=None):
    """إرسال رسائل مع معالجة الأخطاء"""
    try:
        return T.send_message(chat_id, text, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def safe_edit_message(chat_id, message_id, text, reply_markup=None):
    """تعديل رسائل مع معالجة الأخطاء"""
    try:
        return T.edit_message_text(text, chat_id, message_id, reply_markup=reply_markup)
    except Exception as e:
        print(f"Error editing message: {e}")
        return None

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
            T.send_message(uid, "أهلاً! أنا @TeSi7_BOT الذكاء الاصطناعي الخاص بك لإنشاء المطالبات والصور 🌴", reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ لم تشترك بعد في القناة:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            T.send_message(uid, f"⚠️ لم تشترك بعد في القناة:\n{CHANNEL_USERNAME}", reply_markup=markup)

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
            T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
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
        T.send_message(uid, "اختر نوع المطالبة التي تريد إنشاءها:", reply_markup=markup)

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
            T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
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
        T.send_message(uid, "اختر الخدمة التي تريدها:", reply_markup=markup)

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
            T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
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
        T.send_message(uid, "أهلاً! أنا @TeSi7_BOT الذكاء الاصطناعي الخاص بك لإنشاء المطالبات والصور 🌴", reply_markup=markup)

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
            T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
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
        T.send_message(uid, text, reply_markup=markup)

@T.callback_query_handler(func=lambda c: c.data in ["back_to_services", "back_to_prompt_menu"])
def back_to_previous(c):
    """العودة إلى القوائم السابقة"""
    uid = c.from_user.id
    
    if not check_subscription(uid):
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("اشترك في القناة 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}"))
        markup.add(InlineKeyboardButton("تحقق من الاشتراك ✅", callback_data="check_subscription"))
        try:
            T.edit_message_text(f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", 
                              c.message.chat.id, c.message.message_id, reply_markup=markup)
        except:
            T.send_message(uid, f"⚠️ يجب الاشتراك في قناتنا أولاً:\n{CHANNEL_USERNAME}", reply_markup=markup)
        return
    
    if c.data == "back_to_services":
        bot_services(c)
    else:
        create_prompt_menu(c)

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
    """معالجة النصوص المرسلة مع تحسين معالجة الأخطاء"""
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
        wait_msg = T.send_message(uid, "⏳ جاري معالجة طلبك...")
        desc = m.text
        
        try:
            # الحصول على روابط الصور
            links = []
            for fid in user_photos[uid]:
                try:
                    file_info = T.get_file(fid)
                    file_url = f"https://api.telegram.org/file/bot{T.token}/{file_info.file_path}"
                    links.append(file_url)
                    print(f"Image link: {file_url}")
                except Exception as e:
                    print(f"Error getting file info: {e}")
                    continue
            
            if not links:
                T.send_message(uid, "❌ لم أتمكن من الحصول على الصور. حاول مرة أخرى.")
                return
            
            # إرسال الطلب لإنشاء الصور
            results = []
            for i in range(2):  # محاولتان
                try:
                    result = send_request(desc, links)
                    if result:
                        results.append(result)
                        print(f"Generated image {i+1}: {result}")
                except Exception as e:
                    print(f"Error in request attempt {i+1}: {e}")
            
            # إرسال الصور الناتجة
            if results:
                media = []
                for i, image_url in enumerate(results):
                    if image_url and image_url.startswith('http'):
                        if i == 0:
                            media.append(InputMediaPhoto(media=image_url, 
                                                       caption=f"📸 {desc}",
                                                       parse_mode="HTML"))
                        else:
                            media.append(InputMediaPhoto(media=image_url))
                
                if media:
                    T.send_media_group(uid, media)
                    T.send_message(uid, "✅ تم الانتهاء من التعديل بنجاح!")
                else:
                    T.send_message(uid, "❌ لم أتمكن من إنشاء الصور. حاول مرة أخرى.")
            else:
                T.send_message(uid, "❌ فشل في إنشاء الصور. حاول مرة أخرى.")
                
        except Exception as e:
            print(f"Error in edit_img: {e}")
            T.send_message(uid, "❌ حدث خطأ أثناء المعالجة. حاول مرة أخرى.")
        
        finally:
            # التنظيف
            try:
                T.delete_message(uid, wait_msg.message_id)
            except:
                pass
            user_photos[uid] = []
            user_action.pop(uid, None)
    
    elif action == "create_img":
        # معالجة إنشاء الصورة
        wait_msg = T.send_message(uid, "⏳ جاري إنشاء الصور...")
        desc = m.text
        
        try:
            # إرسال الطلب لإنشاء الصور
            results = []
            for i in range(2):  # محاولتان
                try:
                    result = send_request(desc)
                    if result:
                        results.append(result)
                        print(f"Generated image {i+1}: {result}")
                except Exception as e:
                    print(f"Error in request attempt {i+1}: {e}")
            
            # إرسال الصور الناتجة
            if results:
                media = []
                for i, image_url in enumerate(results):
                    if image_url and image_url.startswith('http'):
                        if i == 0:
                            media.append(InputMediaPhoto(media=image_url, 
                                                       caption=f"🎨 {desc}",
                                                       parse_mode="HTML"))
                        else:
                            media.append(InputMediaPhoto(media=image_url))
                
                if media:
                    T.send_media_group(uid, media)
                    T.send_message(uid, "✅ تم الإنشاء بنجاح!")
                else:
                    T.send_message(uid, "❌ لم أتمكن من إنشاء الصور. حاول مرة أخرى.")
            else:
                T.send_message(uid, "❌ فشل في إنشاء الصور. حاول مرة أخرى.")
                
        except Exception as e:
            print(f"Error in create_img: {e}")
            T.send_message(uid, "❌ حدث خطأ أثناء الإنشاء. حاول مرة أخرى.")
        
        finally:
            try:
                T.delete_message(uid, wait_msg.message_id)
            except:
                pass
            user_action.pop(uid, None)
        
    elif action == "create_prompt_type":
        # معالجة إنشاء برومبت الإنشاء باستخدام DeepSeek V3
        wait_msg = T.send_message(uid, "⏳ جاري إنشاء المطالبة...")
        prompt_text = m.text
        
        try:
            # إنشاء البرومبت باستخدام DeepSeek V3
            generated_prompt = generate_prompt(prompt_text)
            
            # إرسال البرومبت فقط كنص عادي بدون أي تنسيق
            T.send_message(uid, generated_prompt)
            
        except Exception as e:
            print(f"Error in create_prompt_type: {e}")
            T.send_message(uid, "❌ حدث خطأ أثناء إنشاء المطالبة. حاول مرة أخرى.")
        
        finally:
            try:
                T.delete_message(uid, wait_msg.message_id)
            except:
                pass
            user_action.pop(uid, None)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("العودة للقائمة 🔙", callback_data="create_prompt_menu"))
            T.send_message(uid, "✅ تم إنشاء مطالبة الإنشاء بنجاح!", reply_markup=markup)
        
    elif action == "edit_prompt_type":
        # معالجة إنشاء برومبت التعديل باستخدام DeepSeek R1
        wait_msg = T.send_message(uid, "⏳ جاري إنشاء المطالبة...")
        prompt_text = m.text
        
        try:
            # إنشاء البرومبت باستخدام DeepSeek R1
            generated_prompt = generate_edit_prompt(prompt_text)
            
            # إرسال البرومبت فقط كنص عادي بدون أي تنسيق
            T.send_message(uid, generated_prompt)
            
        except Exception as e:
            print(f"Error in edit_prompt_type: {e}")
            T.send_message(uid, "❌ حدث خطأ أثناء إنشاء المطالبة. حاول مرة أخرى.")
        
        finally:
            try:
                T.delete_message(uid, wait_msg.message_id)
            except:
                pass
            user_action.pop(uid, None)
            
            markup = InlineKeyboardMarkup()
            markup.add(InlineKeyboardButton("العودة للقائمة 🔙", callback_data="create_prompt_menu"))
            T.send_message(uid, "✅ تم إنشاء مطالبة التعديل بنجاح!", reply_markup=markup)

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
    """الصفحة الرئيسية"""
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
        time.sleep(300)

if __name__ == "__main__":
    # تعيين الويب هووك عند التشغيل
    set_webhook()
    
    # بدء خيط للحفاظ على النشاط
    keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
    keep_alive_thread.start()
    
    # تشغيل تطبيق Flask
    app.run(host='0.0.0.0', port=10000, debug=False)
