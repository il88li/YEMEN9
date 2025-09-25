import telebot,requests
from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton,InputMediaPhoto
from concurrent.futures import ThreadPoolExecutor
SeedReam="https://sii3.top/api/SeedReam-4.php" # API
T=telebot.TeleBot("7863334400:AAHCp4jO-pd2qqGQKqxLF1GGHh4w-0zPhqQ") # Token
user_photos={}
user_action={}
def send_request(t,l=[]):return requests.post(SeedReam,data={"text":t,"links":",".join(l)}).json().get("image")
def darkai():T.polling()
@T.message_handler(commands=['start'])
def start_cmd(m):
 uid=m.from_user.id
 markup=InlineKeyboardMarkup(row_width=2)
 markup.add(InlineKeyboardButton("Create Image",callback_data="create_img"),InlineKeyboardButton("Edit Image",callback_data="edit_img"))
 T.send_message(uid,"Welcome! im SeedReam 4.0 your AI for image create + edit 🫧",reply_markup=markup)
@T.callback_query_handler(func=lambda c:c.data in ["create_img","edit_img"])
def action_select(c):
 user_action[c.from_user.id]=c.data
 text="Send image description" if c.data=="create_img" else "Send image (max 4)"
 try:T.edit_message_text(text, c.message.chat.id, c.message.message_id)
 except:pass
 try:T.edit_message_reply_markup(c.message.chat.id, c.message.message_id, reply_markup=None)
 except:pass
@T.message_handler(content_types=['photo'])
def handle_photos(m):
 uid=m.from_user.id
 if user_action.get(uid)!="edit_img":return
 user_photos.setdefault(uid,[]).append(m.photo[-1].file_id)
 if len(user_photos[uid])>4:user_photos[uid]=user_photos[uid][:4]
 if len(user_photos[uid])==1:T.send_message(uid,"Send edit description")
@T.message_handler(func=lambda m:True)
def handle_description(m):
 uid=m.from_user.id
 action=user_action.get(uid)
 if action=="edit_img" and uid in user_photos and user_photos[uid]:
  wait_st=T.send_sticker(uid,"CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
  desc=m.text
  links=[f"https://api.telegram.org/file/bot{T.token}/{T.get_file(fid).file_path}" for fid in user_photos[uid]]
  cap=(desc[:1021]+"...") if len(desc)>1024 else desc
  with ThreadPoolExecutor() as e:results=list(e.map(lambda _:send_request(desc,links),range(2)))
  media=[]
  for i,u in enumerate(results):
   if not u:continue
   if i==0:media.append(InputMediaPhoto(media=u,caption=f"<b><blockquote>{cap}</blockquote></b>",parse_mode="HTML",has_spoiler=True))
   else:media.append(InputMediaPhoto(media=u,has_spoiler=True))
  if media:T.send_media_group(uid,media)
  try:T.delete_message(uid,wait_st.message_id)
  except:pass
  user_photos[uid]=[]
  user_action.pop(uid,None)
 elif action=="create_img":
  wait_st=T.send_sticker(uid,"CAACAgIAAxkBAAIMcmjDndyMvCb2OBQhIGobGVZU4f6JAAK0IwACmEspSN65vs0qW-TZNgQ")
  desc=m.text
  cap=(desc[:1021]+"...") if len(desc)>1024 else desc
  with ThreadPoolExecutor() as e:results=list(e.map(lambda _:send_request(desc),range(2)))
  media=[]
  for i,u in enumerate(results):
   if not u:continue
   if i==0:media.append(InputMediaPhoto(media=u,caption=f"<b><blockquote>{cap}</blockquote></b>",parse_mode="HTML",has_spoiler=True))
   else:media.append(InputMediaPhoto(media=u,has_spoiler=True))
  if media:T.send_media_group(uid,media)
  try:T.delete_message(uid,wait_st.message_id)
  except:pass
  user_action.pop(uid,None)
darkai()