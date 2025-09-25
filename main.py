import telebot
import requests
import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor

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

def darkai():
    """تشغيل البوت"""
    T.polling()

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
        InlineKeyboardButton(f"إنشاء برومبت {emoji3}", callback_data="create_prompt")
    )
    try:
        T.edit_message_text("اختر الخدمة التي تريدها:", c.message.chat.id, c.message.message_id, reply_markup=markup)
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
    try:
        T.edit_message_text(text, c.message.chat.id, c.message.message_id)
    except:
        pass
    try:
        T.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
    except:
        pass

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
        T.send_message(uid, "أرسل وصف التعديل")

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
        
    elif action == "create_prompt":
        # معالجة إنشاء البرومبت
        wait_st = T.send_sticker(uid, "CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
        prompt_text = m.text
        
        # استخدام API إنشاء البرومبت
        image_url = PromptAPI + requests.utils.quote(prompt_text)
        
        try:
            T.send_photo(uid, image_url, caption=f"<b><blockquote>{prompt_text}</blockquote></b>", parse_mode="HTML")
        except Exception as e:
            T.send_message(uid, f"حدث خطأ أثناء إنشاء الصورة: {str(e)}")
        
        try:
            T.delete_message(uid, wait_st.message_id)
        except:
            pass
        
        user_action.pop(uid, None)

# تشغيل البوت
if __name__ == "__main__":
    darkai()
