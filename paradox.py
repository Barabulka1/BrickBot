import json
import logging
from fileinput import close

from telebot.types import Update, Message
from telegram.ext import Application, MessageHandler, filters
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup

with open('rooms.json', 'r') as rms:
    rooms = json.load(rms)
with open('users.json', 'r') as rms:
    users = json.load(rms)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
markup = ReplyKeyboardMarkup([['/start', '/help']], one_time_keyboard=False)
some_magic = {}


async def exp(update, context):
    print(context.args[0])
    await update.message.reply_text('yeah')


async def check_and_send(usr):
    who_is_in_the_room = list(filter(lambda y: y['room'] == users[usr]['room'], users.values()))
    names_of_those = list(filter(lambda y: users[y]['room'] == users[usr]['room'], users.keys()))
    if all(list(map(lambda x: x['ready'], who_is_in_the_room))):
        for x in some_magic.items():
            if x[0] in names_of_those:
                users[x[0]]['ready'] = 0
                print(111111111111111111111)
                await x[1].message.reply_text('some answer(don`t have brain yet)')


async def echo(update, context):
    with open('fbi.txt', 'r') as fbi:
        f = fbi.read()
    with open('fbi.txt', 'w') as fbi:
        fbi.write(f + '\n' + update.message.text)
    await update.message.reply_text('записал' + update.message.text)


async def start(update, context):
    user = update.effective_user
    await update.message.reply_html(
        rf'Привет {user.mention_html()}! Я бот для игры в "Догони меня кирпич!". Узнать правила можно по команде /rules',
        reply_markup=markup
    )


async def rules(update, context):
    await update.message.reply_text('potom dobavlu')


async def help_command(update, context):
    await update.message.reply_text("Я пока не умею помогать... Я только ваше эхо.")


#  rooms starting
async def add_room(update, context):
    user = update.effective_user.mention_html()

    # add user to list of all users
    if user in users:
        last_room = users[user]['room']

        # delete user from previous room
        last_users = rooms[last_room]
        print(last_users)
        last_users.remove(user)
        print(last_users)
        rooms[last_room] = last_users
        users[user]['room'] = context.args[0]
    else:
        users[user] = {'room': context.args[0], 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': 0}
    if context.args[0] in rooms and user not in rooms[context.args[0]]:
        rooms[context.args[0]].append(user)
        users[user]['ready'] = 0
    else:
        rooms[context.args[0]] = [user]

    with open('rooms.json', 'w') as rms:
        json.dump(rooms, rms, ensure_ascii=True)
    with open('users.json', 'w') as rms:
        json.dump(users, rms, ensure_ascii=True)

    await update.message.reply_text('Успешно добавлена комната')


async def make_action(update, context):
    user = update.effective_user.mention_html()
    users[user]['ready'] = 1
    some_magic[user] = update

    with open('rooms.json', 'w') as rms:
        json.dump(rooms, rms, ensure_ascii=True)
    with open('users.json', 'w') as rms:
        json.dump(users, rms, ensure_ascii=True)
    print(type(update.message))

    await check_and_send(user)


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, echo)

    application.add_handler(text_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("join_room", add_room))
    application.add_handler(CommandHandler('make_action', make_action))
    application.add_handler(CommandHandler('exp', exp))
    print(dir(Message))

    application.run_polling()


if __name__ == '__main__':
    main()

    # kostili for erasing empty rooms
    goofy_ah = rooms.keys()
    del_list = []
    for i in goofy_ah:
        if rooms[i] == None:
            del_list.append(i)
    for j in del_list:
        del rooms[j]

    with open('rooms.json', 'w') as rms:
        json.dump(rooms, rms, ensure_ascii=True)
    with open('users.json', 'w') as rms:
        json.dump(users, rms, ensure_ascii=True)