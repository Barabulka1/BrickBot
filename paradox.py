import json
import logging
from fileinput import close

from telebot.types import Update, Message
from telegram.ext import Application, MessageHandler, filters
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup

with open('rooms.json', 'r') as rms:  #  загружаем данные
    rooms = json.load(rms)
with open('users.json', 'r') as rms:
    users = json.load(rms)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
markup = ReplyKeyboardMarkup([['/start', '/help']], one_time_keyboard=False)
some_magic = {}


async def check_and_send(usr):
    names_of_those = list(filter(lambda y: users[y]['room'] == users[usr]['room'], users.keys()))  #  ники людей из той же
    #  комнаты, что и юзер
    if all(list(map(lambda x: users[x]['ready'], names_of_those))):  #  все ли готовы сделать действие?
        for x in some_magic.items():
            if x[0] in names_of_those:             #  рассылка ответов по этим юзерам (в some_magic хранятся переменные
                users[x[0]]['ready'] = 0           #  для отсылки сообщений
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

    #  сменить юзеру комнату или, если он еще не в списке юзеров, добавить его туда
    if user in users:
        last_room = users[user]['room']

        # delete user from previous room
        last_users = rooms[last_room]
        last_users.remove(user)
        rooms[last_room] = last_users
        if not rooms[last_room]:
            del rooms[last_room]
        users[user]['room'] = context.args[0]
    else:
        users[user] = {'room': context.args[0], 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': 0}

    if context.args[0] in rooms:                #  комната существует?
        if user not in rooms[context.args[0]]:  #  юзер уже находится в этой комнате?
            rooms[context.args[0]].append(user)
            users[user]['ready'] = 0
    else:
        rooms[context.args[0]] = [user]

    await update.message.reply_text('Успешно добавлена комната')


def make_action(update):
    user = update.effective_user.mention_html()
    users[user]['ready'] = 1                     #  он готов сделать действие
    some_magic[user] = update                    #  переменная для отсылки сообщений
    if users[user]['frozen'] == 1:               #  он в цементе?
        return False
    return True


async def brick(update, context):
    user = update.effective_user.mention_html()
    can_make = make_action(update)                #  не в цементе ли юзер?
    if can_make:
        if 'brick' not in users[user]['inventory']:   #  нет ли у юзера кирпича уже (можно держать один за раз)
            users[user]['action'] = 'take_brick - -'  #  вместо первого прочерка будет стоять номер слота, куда будет
            #  взят кирпич (если понадобится), вместо второго - в кого будет кинут предмет (для действия кидания)
            inv = users[user]['inventory']
            if len(inv) >= 4:                      #  не переполнен ли инвентарь?
                await update.message.reply_text("Нужно выкинуть что-то. Инвентарь переполнен")
                await update.message.reply_text(f"1. {inv[0]} 2. {inv[1]} 3. {inv[2]} 4. {inv[3]} '-' нафиг эти ваши "
                                                f"кирпичи, так обойдусь", reply_markup=
                ReplyKeyboardMarkup([['/throw_out_1', '/throw_out_2', '/throw_out_3'],
                                     ['/throw_out_4', '/throw_out_none']], one_time_keyboard=False))
                #  вызов клавиатуры для выброса чего-либо для очистки инвентаря (либо отказаться от подбора кирпича)
            else:
                await update.message.reply_text("Теперь у вас будет кирпич!")
                await check_and_send(user)
        else:
            await update.message.reply_text('У вас уже есть кирпич')
            users[user]['ready'] = 0


async def throw_out_base(usr, num):
    act = users[usr]['action'].split()     #  базовая функция выброса. Она записывает в действие вместо чего
    act[1] = num                           #  пользователь берет кирпич (или предмет)
    users[usr]['action'] = ' '.join(act)
    await check_and_send(usr)


async def throw_out1(update, context):
    await update.message.reply_text('1')
    await throw_out_base(update.effective_user.mention_html(), '1')


async def throw_out2(update, context):
    await update.message.reply_text('2')
    await throw_out_base(update.effective_user.mention_html(), '2')


async def throw_out3(update, context):
    await update.message.reply_text('3')
    await throw_out_base(update.effective_user.mention_html(), '3')


async def throw_out4(update, context):
    await update.message.reply_text('4')
    await throw_out_base(update.effective_user.mention_html(), '4')


async def throw_out_none(update, context):         #  как 4 предыдущих функции, но назначает юзера как не готового
    user = update.effective_user.mention_html()    #  сделать действие
    await update.message.reply_text('-')
    users[user]['ready'] = 0
    await throw_out_base(user, '-')


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    text_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, echo)

    application.add_handler(text_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("join_room", add_room))
    application.add_handler(CommandHandler("take_brick", brick))
    application.add_handler(CommandHandler("throw_out_1", throw_out1))
    application.add_handler(CommandHandler("throw_out_2", throw_out2))
    application.add_handler(CommandHandler("throw_out_3", throw_out3))
    application.add_handler(CommandHandler("throw_out_4", throw_out4))
    application.add_handler(CommandHandler("throw_out_none", throw_out_none))

    application.run_polling()


if __name__ == '__main__':
    main()

    with open('rooms.json', 'w') as rms:
        json.dump(rooms, rms, ensure_ascii=True)
    with open('users.json', 'w') as rms:
        json.dump(users, rms, ensure_ascii=True)
