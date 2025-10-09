import telebot
import requests
import random
import json
import re
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
    """تنظيف النص من الرموز البرمجية وحقوق المطورين بشكل كامل"""
    # إذا كان النص يحتوي على JSON، نستخرج الـ response فقط
    if '"response":' in text:
        try:
            data = json.loads(text)
            if 'response' in data:
                text = data['response']
        except:
            pass
    
    # إزالة جميع علامات الكود والتنسيقات البرمجية
    cleaned = text.replace('```', '').replace('`', '').replace('***', '').replace('---', '').strip()
    
    # إزالة أي حقوق مطورين أو إعلانات باستخدام التعابير النمطية
    patterns_to_remove = [
        r'.*[Cc]hannel.*',
        r'.*[Ss]upport.*', 
        r'.*[Ss]ubscribe.*',
        r'.*[Dd]eveloper.*',
        r'.*[Dd]ev.*',
        r'.*تابع.*',
        r'.*قناة.*',
        r'.*دعم.*',
        r'.*مطور.*',
        r'.*@\w+.*',
        r'^---.*',
        r'^###.*',
        r'.*Note:.*',
        r'.*Adjust these.*',
        r'.*Midjourney.*',
        r'.*DALL-E.*',
        r'.*Stable Diffusion.*',
        r'.*--ar.*',
        r'.*--style.*',
        r'.*Final Concise Prompt.*',
        r'.*Professional Image Generation Prompt.*'
    ]
    
    lines = cleaned.split('\n')
    clean_lines = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # التحقق من عدم تطابق الخط مع الأنماط المرفوضة
        should_skip = False
        for pattern in patterns_to_remove:
            if re.match(pattern, line, re.IGNORECASE):
                should_skip = True
                break
                
        if not should_skip:
            clean_lines.append(line)
    
    # تجميع النص النظيف
    final_text = '\n'.join(clean_lines).strip()
    
    # إذا كان النص قصيراً جداً، نعيد نصاً بديلاً
    if len(final_text) < 20:
        return "Create a professional, high-quality image with detailed composition, excellent lighting, and vibrant colors."
    
    return final_text

def send_request(t, l=[]):
    """إرسال طلب إلى API SeedReam مع معالجة محسنة"""
    try:
        # تنظيف النص قبل الإرسال
        clean_text = clean_text_for_api(t)
        print(f"Sending cleaned text: {clean_text}")
        print(f"Number of links: {len(l)}")
        
        data = {"text": clean_text}
        if l and len(l) > 0:
            data["links"] = ",".join(l)
        
        # إضافة headers لتجنب الأخطاء
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        
        response = requests.post(SeedReam, data=data, headers=headers, timeout=30)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                image_url = result.get("image")
                if image_url:
                    print(f"Success! Image URL: {image_url}")
                    return image_url
                else:
                    print("No image URL in response")
                    return None
            except json.JSONDecodeError:
                print("JSON decode error - trying to extract image URL from text")
                # محاولة استخراج الرابط من النص مباشرة
                if 'http' in response.text:
                    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', response.text)
                    if urls:
                        return urls[0]
                return None
        else:
            print(f"API returned error: {response.status_code}")
            print(f"Response text: {response.text[:200]}")  # طباعة أول 200 حرف من الرد
            return None
            
    except requests.exceptions.Timeout:
        print("Request timed out after 30 seconds")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in send_request: {e}")
        return None

def clean_text_for_api(text):
    """تنظيف النص قبل إرساله إلى API الصور"""
    # إذا كان النص يحتوي على JSON، نستخرج النص الفعلي فقط
    if '"response":' in text:
        try:
            data = json.loads(text)
            if 'response' in data:
                text = data['response']
        except:
            pass
    
    # إزالة أي رموز أو تنسيقات غير مرغوب فيها
    cleaned = re.sub(r'[{}"\\]', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    # تقليل طول النص إذا كان طويلاً جداً
    if len(cleaned) > 500:
        cleaned = cleaned[:500] + "..."
    
    return cleaned

def generate_prompt(text):
    """إنشاء برومبت باستخدام DeepSeek V3"""
    try:
        # استخدام DeepSeek V3 لإنشاء البرومبت
        prompt_request = f"Create a detailed professional image generation prompt in English for: {text}. Make it descriptive and include details about scene, lighting, colors. Return only the prompt text without any explanations or code blocks."
        response = requests.get(f"{DEEPSEEK_V3_API}{requests.utils.quote(prompt_request)}", timeout=15)
        
        if response.status_code == 200 and response.text.strip():
            clean_prompt = clean_prompt_text(response.text)
            return clean_prompt
        else:
            return f"Professional high-quality image of {text}, detailed, realistic, excellent lighting"
    except Exception as e:
        print(f"Error in generate_prompt: {e}")
        return f"Professional high-quality image of {text}, detailed, realistic, excellent lighting"

def generate_edit_prompt(text):
    """إنشاء برومبت تعديل باستخدام DeepSeek R1"""
    try:
        # استخدام DeepSeek R1 لإنشاء برومبت التعديل
        prompt_request = f"Create a detailed professional image editing prompt in English for: {text}. Focus on specific modifications like color adjustments, lighting changes. Return only the prompt text without any explanations or code blocks."
        response = requests.post(
            DEEPSEEK_R1_API,
            data={"r1": prompt_request},
            timeout=15
        )
        
        if response.status_code == 200 and response.text.strip():
            clean_prompt = clean_prompt_text(response.text)
            return clean_prompt
        else:
            return f"Professional image editing for {text}, enhance quality, adjust colors, improve lighting"
    except Exception as e:
        print(f"Error in generate_edit_prompt: {e}")
        return f"Professional image editing for {text}, enhance quality, adjust colors, improve lighting"

# باقي الكود يبقى كما هو مع تحسينات بسيطة في معالجة الصور
# [جميع الـ handlers تبقى كما هي مع تحسينات في معالجة الأخطاء]

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
                        break  # إذا نجحت محاولة واحدة، نتوقف
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
                        break  # إذا نجحت محاولة واحدة، نتوقف
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
            
            # إرسال البرومبت فقط بشكل ماركداون
            T.send_message(uid, f"```\n{generated_prompt}\n```", parse_mode="Markdown")
            
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
            
            # إرسال البرومبت فقط بشكل ماركداون
            T.send_message(uid, f"```\n{generated_prompt}\n```", parse_mode="Markdown")
            
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

# باقي الكود يبقى كما هو...
# [الويب هووك والباقي بدون تغيير]

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
