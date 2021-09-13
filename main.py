from os import getenv

import telebot
from telebot.types import Message
from telebot.util import extract_arguments

from utils import autodelete, has_reply, log
from utils.db import Db

#pip install python-dotenv
try:
    from os.path import dirname, join

    from dotenv import load_dotenv
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
except ModuleNotFoundError:
    print('dotenv non è installato')
except:
    pass

db = Db(getenv('DB_NAME'))

bot = telebot.TeleBot(getenv('BOT_TOKEN'), parse_mode = 'HTML')

GROUPID = int(getenv('GROUP_ID'))

@bot.message_handler(commands=['notes'])
def notes(message: Message):
    if message.chat.id == GROUPID:
        keys = db.select("SELECT Key, Description FROM Notes")
        if keys:
            keys.sort()
            getkeytext = "Use '/get key' - to get note.\n\n<b>Keys:</b>\n"
            for key in keys:
                getkeytext+=f"<code>{str(key[0])}</code> - <i>{str(key[1])}</i>\n"
            msg = bot.send_message(message.chat.id, getkeytext, reply_to_message_id = has_reply(message))
        else:
            msg = bot.send_message(message.chat.id, "There are no keys yet. Use\n'/add_note key description\ntext'")
        bot.delete_message(message.chat.id, message.message_id)
        autodelete(bot, msg)

@bot.message_handler(commands=['get'])
def get_value(message: Message):
    if message.chat.id == GROUPID:
        a = extract_arguments(message.text)
        if a:
            key = db.select("SELECT Text FROM Notes WHERE key = ?", str(a))
            if key:
                msg = bot.send_message(message.chat.id, str(key[0][0]), reply_to_message_id = has_reply(message))
            else:
                msg = bot.send_message(message.chat.id, "Note with this key isn't available❌\n/notes")
        else:
            msg = bot.send_message(message.chat.id, "Use /get key - to get note.")
        bot.delete_message(message.chat.id, message.message_id)
        autodelete(bot, msg)

@bot.message_handler(commands=['add_note'])
def add_notes(message: Message):
    if message.chat.id == GROUPID:
        admin = db.select("SELECT Uid FROM Admins WHERE Uid = ?", message.from_user.id)
        if admin:
            text = message.html_text.split('\n', maxsplit=1)
            if len(text) > 1:
                nextext = text[0].split(maxsplit=2)
                if len(nextext) == 1:
                    msg = bot.send_message(message.chat.id, "Use '/add_note key description\ntext'")
                    bot.delete_message(message.chat.id, message.message_id)
                elif len(nextext) == 2:
                    msg = bot.send_message(message.chat.id, "You forgot the description❌")
                    autodelete(bot, message)
                elif len(nextext) == 3:
                    key = db.select("SELECT Text FROM Notes WHERE Key = ?", str(nextext[1]))
                if key:
                    msg = bot.send_message(message.chat.id, "Note with this key already exist❌\nPlease create note again with another key.")
                else:
                    db.query("INSERT INTO Notes(Key, Description, Text) VALUES(?, ?, ?)", str(nextext[1]), str(nextext[2]), str(text[1]), commit = True)
                    msg = bot.send_message(message.chat.id, "Note successfully added with key <code>{}</code> ✅".format(nextext[1]))
            else:
                msg = bot.send_message(message.chat.id, "You forgot the text❌")
        else:
            msg = bot.send_message(message.chat.id, "You're not a moderator❌")
        autodelete(bot, msg, 2)
        autodelete(bot, message, 2)

@bot.message_handler(commands=['delete_note'])
def delete_notes(message):
    if message.chat.id == GROUPID:
        admin = db.select("SELECT Uid FROM Admins WHERE Uid = ?", message.from_user.id)
        if admin:
            a = extract_arguments(message.text)
            if a:
                key = db.select("SELECT Key FROM Notes WHERE Key = ?", str(a))
                if key:
                    db.query("DELETE FROM Notes WHERE Key = ?", str(a), commit = True)
                    msg = bot.send_message(message.chat.id, "Note with key <code>{}</code> successfully deleted ✅".format(a))
                else:
                    msg = bot.send_message(message.chat.id, "Note with key <code>{}</code> isn't available ❌".format(a))
            else:
                msg = bot.send_message(message.chat.id, "You forgot the key ❌")
        else:
            msg = bot.send_message(message.chat.id, "You're not a moderator ❌")
        autodelete(bot, msg, 2)
        autodelete(bot, message, 0)

@bot.message_handler(commands=['add_admin'])
def add_admins(message: Message):
    if message.chat.id == GROUPID:
        admin = db.select("SELECT Uid FROM Admins WHERE Uid = ?", message.from_user.id)
        if admin:
            if message.reply_to_message:
                admin2 = db.select("SELECT Uid FROM Admins WHERE Uid = ?", message.reply_to_message.from_user.id)
                if admin2:
                    msg = bot.send_message(message.chat.id, "This user is already a moderator ❌")
                else:
                    db.query("INSERT INTO Admins(Uid) VALUES(?)", message.reply_to_message.from_user.id, commit = True)
                    msg = bot.send_message(message.chat.id, f"<a href='tg://user?id={message.reply_to_message.from_user.id}'>This</a> user has now successfully become a moderator ✅")
            else:
                msg = bot.send_message(message.chat.id, "This command must be a reply to the user ❌")
        else:
            msg = bot.send_message(message.chat.id, "You're not a moderator❌")
        autodelete(bot, msg, 2)
        autodelete(bot, message, 1)

@bot.message_handler(commands=['help'])
def help_func(message):
    if message.chat.id == GROUPID:
        msg = bot.send_message(message.chat.id, "Usage:\n/notes - list of notes\n/add_note - add new note\n/delete_note - delete note\n/get - get note\n/add_admin - add new moderator")
        autodelete(bot, msg, 2)
        autodelete(bot, message, 0)

@bot.message_handler(commands=['start'])
def welcome(message: Message):
    if message.chat.id == GROUPID:
        msg = bot.send_message(message.chat.id, "Hi, I'm online!\nSend /help")
        autodelete(bot, msg, 0.5)
    elif message.chat.type == 'private':
        bot.send_message(message.chat.id, "Join pyTelegramBotApi's Telegram Group to get code snippets\n\nhttps://telegram.me/joinchat/Bn4ixj84FIZVkwhk2jag6A")
    autodelete(bot, message, 0)

msg = log.info_log(bot, "I'm started!", GROUPID)
autodelete(bot, msg, 1)
bot.polling()
