import json
import logging
from fileinput import close

from telebot.types import Update, Message
from telegram.ext import Application, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup

rooms = {}
users = {}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
markup = ReplyKeyboardMarkup([['/start', '/help']], one_time_keyboard=False)
some_magic = {}


async def check_and_send(usr):
    names_of_those = rooms[users[usr]['room']]  #  ники людей из той же
    #  комнаты, что и юзер
    if all(list(map(lambda x: users[x]['ready'], names_of_those))):  #  все ли готовы сделать действие?
        msg = brain(names_of_those)
        for x in some_magic.items():
            if x[0] in names_of_those:             #  рассылка ответов по этим юзерам (в some_magic хранятся переменные
                users[x[0]]['ready'] = 0           #  для отсылки сообщений
                await x[1].message.reply_text(msg)


def brain(users1):
    fin_message = ''
    for user in users1:
        act = users[user]['action'].split()
        if act[0] == 'take_brick':
            if act[1] == '-':
                users[user]['inventory'].append('brick')
            else:
                users[user]['inventory'][int(act[1]) - 1] = 'brick'
            fin_message += f'{user.split(">")[1][:-3]} взял кирпич'
    return fin_message


async def start(update, context):
    user = update.effective_user.mention_html()
    users[user] = {'room': "wait", 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': 0}
    await update.message.reply_html(
        rf'Привет {user}! Я бот для игры в "Догони меня кирпич!". Узнать правила можно по команде /rules',
        reply_markup=markup
    )
    return 1


async def rules(update, context):
    await update.message.reply_text('potom dobavlu')


async def help_command(update, context):
    await update.message.reply_text("Я пока не умею помогать... Я только ваше эхо.")


#  rooms starting
async def join_room(update, context):
    user = update.effective_user.mention_html()

    #  сменить юзеру комнату или, если он еще не в списке юзеров, добавить его туда
    if users[user]["room"] != "wait":
        room = users[user]['room']

        room_users = rooms[room]
        room_users.remove(user)
        rooms[room] = room_users  # удаление пользователя из комнаты
        if not rooms[room]:
            del rooms[room]
    users[user]['room'] = context.args[0]

    if context.args[0] in rooms:  # комната существует?
        if user not in rooms[context.args[0]]:  # юзер уже находится в этой комнате?
            rooms[context.args[0]].append(user)
            users[user]['ready'] = 0
    else:
        rooms[context.args[0]] = [user]

    await update.message.reply_text('Успешно добавлена комната')


def make_action(update):
    user = update.effective_user.mention_html()
    some_magic[user] = update                    #  переменная для отсылки сообщений
    if users[user]['frozen'] == 1:               #  он в цементе?
        return False
    return True


async def brick(update, context):
    user = update.effective_user.mention_html()
    can_make = make_action(update)                #  не в цементе ли юзер?
    if can_make:
        if 'brick' not in users[user]['inventory']:   #  нет ли у юзера кирпича уже (можно держать один за раз)
            users[user]['action'] = 'take_brick -'  #  вместо прочерка будет стоять номер слота, куда будет
            #  взят кирпич или в кого будет кинут предмет (для действия кидания)
            inv = users[user]['inventory']
            if len(inv) >= 4:  #  не переполнен ли инвентарь?
                return 2
            else:
                users[user]['action'] = 'take_brick -'
                users[user]['ready'] = 1                     #  он готов сделать действие
                await update.message.reply_text("Теперь у вас будет кирпич!")
                await check_and_send(user)
        else:
            await update.message.reply_text('У вас уже есть кирпич')
    else:
        users[user]['ready'] = 1
    return 1


async def throw_out(update, context):
    user = update.effective_user.mention_html()
    inv = users[user]['inventory']
    await update.message.reply_text("Нужно выкинуть что-то. Инвентарь переполнен")
    await update.message.reply_text(f"1. {inv[0]} 2. {inv[1]} 3. {inv[2]} 4. {inv[3]} '-' нафиг эти ваши "
                                        f"кирпичи, так обойдусь")
    inp = update.message.text
    if inp in ['1', '2', '3', '4', '-']:
        act = users[user]['action'].split()
        act[1] = inp
        users[user]['action'] = ' '.join(act)
        if not inp == '-':
            users[user]['ready'] = 1
    else:
        return 2
    return 1


async def stop(update, context):
    await update.message.reply_text('stopped')
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(ConversationHandler(entry_points=[CommandHandler("start", start)],
                                                states={1: [CommandHandler('take_brick', brick),
                                                            CommandHandler("join_room", join_room)],
                                                        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, throw_out)]
                                                        },
                                                fallbacks=[CommandHandler('stop', stop)]))

    application.run_polling()


if __name__ == '__main__':
    main()
