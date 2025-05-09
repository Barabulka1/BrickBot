import logging
from fileinput import close

from telebot.types import Update, Message
from telegram.ext import Application, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup
import random

rooms = {}
users = {}
items = {'песок': 'песок', 'каска': 'каску', 'цемент': 'цемент', 'арматура': 'арматуру'}
items_translate = {'песок': 'sand', 'каска': 'helmet', 'цемент': 'cement', 'арматура': 'armature'}
items_translate_reverse = {'brick': 'кирпич', 'armature': 'арматура', 'cement': 'цемент'}

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
        for x in names_of_those:
            inv = users[x]['inventory']
            inv_str = 'Текущий инвентарь: '                     #  рассылка ответов по этим юзерам (в some_magic хранятся переменные
            users[x]['ready'] = 0            #  для отсылки сообщений
            users[x]['action'] = '- -'
            await some_magic[x].message.reply_text(msg)
            for i in range(len(inv)):
                inv_str += str(i + 1) + '. ' + inv[i] + ' '
            hp_str = f'\nВаше здоровье: {users[x]["hp"]}'
            await some_magic[x].message.reply_text(inv_str + hp_str)


def brain(users1):
    fin_message = ''
    for user in users1:
        act = users[user]['action'].split()
        if act[0] == 'take_brick':
            if act[1] == '-':
                users[user]['inventory'].append('кирпич')
            else:
                users[user]['inventory'][int(act[1]) - 1] = 'кирпич'
            fin_message += f'{user.split(">")[1][:-3]} взял кирпич'

        elif 'take_item' in act[0]:
            item = act[0][:-9]
            if act[1] == '-':
                users[user]['inventory'].append(item)
                fin_message += f'{user.split(">")[1][:-3]} взял {items[item]}'
            elif act[1] == '*':
                fin_message += f'{user.split(">")[1][:-3]} нашел {items[item]}, но выкинул('
            else:
                users[user]['inventory'][int(act[1]) - 1] = item
                fin_message += f'{user.split(">")[1][:-3]} взял {items[item]}'

        elif act[0] == 'throw_armature':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            if users[prey]['frozen'][0] == '0':
                if prey_act[0] == 'dodge':
                    fin_message += f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, но тот увернулся!'
                elif prey_act[0] == 'throw_sand':
                    fin_message += (f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, но промазал '
                                    f'из-за песка')
                else:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}!'
            else:
                fin_message += (f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, однако не пробил'
                                f' цемент.')
            users[user]['inventory'].remove('арматура')

        elif act[0] == 'throw_cement':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            if user == prey:
                lst = list(users[prey]['frozen'])
                lst[2] = '1'
                users[prey]['frozen'] = ''.join(lst)
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в себя! Ну и идиот).'
            elif users[prey]['action'][0] == 'dodge':
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но тот увернулся!'
            elif users[prey]['action'][0] == 'throw_sand':
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но промазал '
                                f'из-за песка')
            elif prey_act[0] == 'throw_brick' and ' '.join(prey_act[1:]) == user:
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но цемент врезался '
                                f'в кирпич')
            elif prey_act[0] == 'throw_cement' and ' '.join(prey_act[1:]) == user:
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но он встретил на '
                                f'пути брата-цемента')
            else:
                lst = list(users[prey]['frozen'])
                lst[2] = '1'
                users[prey]['frozen'] = ''.join(lst)
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}!'
            users[user]['inventory'].remove('цемент')

        elif act[0] == 'throw_brick':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            print(' '.join(prey_act[1:]))
            if users[prey]['frozen'][0] == '0':
                if user == prey:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в себя! Ну и нафига?'
                elif prey_act[0] == 'dodge':
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но тот увернулся!'
                elif prey_act[0] == 'throw_sand':
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но промазал '
                        f'из-за песка')
                elif prey_act[0] == 'throw_brick' and ' '.join(prey_act[1:]) == user:
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но кирпич врезался '
                        f'в ДРУГОЙ кирпич (много кирпичей однако)')
                elif prey_act[0] == 'throw_cement' and ' '.join(prey_act[1:]) == user:
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но он встретил на '
                        f'пути цемент :О')
                else:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}!'
            else:
                fin_message += (
                    f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, однако не пробил'
                    f' цемент.')
            users[user]['inventory'].remove('кирпич')
    for user in users1:
        fr = users[user]['frozen'].split()
        fr[0], fr[1] = fr[1], '0'
        users[user]['frozen'] = ' '.join(fr)
    return fin_message


async def start(update, context):
    user = update.effective_user.mention_html()
    users[user] = {'room': "wait", 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': '0 0'}
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
    if users[user]['frozen'][0] == '1':               #  он в цементе?
        return False
    return True


async def brick(update, context):
    user = update.effective_user.mention_html()
    can_make = make_action(update)                #  не в цементе ли юзер?
    if can_make:
        if 'кирпич' not in users[user]['inventory']:   #  нет ли у юзера кирпича уже (можно держать один за раз)
            users[user]['action'] = 'take_brick -'  #  вместо прочерка будет стоять номер слота, куда будет
            #  взят кирпич или в кого будет кинут предмет (для действия кидания)
            inv = users[user]['inventory']
            if len(inv) >= 4:  #  не переполнен ли инвентарь?
                await update.message.reply_text("Нужно выкинуть что-то. Инвентарь переполнен")
                await update.message.reply_text(f"1. {inv[0]} 2. {inv[1]} 3. {inv[2]} 4. {inv[3]} '-' нафиг эти ваши "
                                                f"кирпичи, так обойдусь")
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


async def take_item(update, context):
    user = update.effective_user.mention_html()
    can_make = make_action(update)                #  не в цементе ли юзер?
    print(can_make)
    if can_make:
        item = random.choice(['песок', 'каска', 'цемент', 'арматура'])
        users[user]['action'] = f'{item}take_item -'
        inv = users[user]['inventory']
        if len(inv) >= 4:  #  не переполнен ли инвентарь?
            await update.message.reply_text("Инвентарь переполнен! Надо что-то выкинуть")
            await update.message.reply_text(f"1. {inv[0]} 2. {inv[1]} 3. {inv[2]} 4. {inv[3]} \n'-' - выбросить "
                                                f"текущий предмет({item})")
            return 2
        else:
            users[user]['ready'] = 1                     #  он готов сделать действие
            await update.message.reply_text(f"В начале следующего хода вы получите {items[item]}!")
            await check_and_send(user)
    else:
        users[user]['ready'] = 1
    return 1


async def throw_out(update, context):
    user = update.effective_user.mention_html()
    inp = update.message.text
    if inp in ['1', '2', '3', '4', '-']:
        act = users[user]['action'].split()
        if inp == '-':
            act[1] = '*'
        else:
            act[1] = inp
        users[user]['action'] = ' '.join(act)
        users[user]['ready'] = 1
        await check_and_send(user)
    else:
        return 2
    return 1


async def throw_item(update, item):
    user = update.effective_user.mention_html()
    can_make = make_action(update)  # не в цементе ли юзер?
    if can_make:
        if items_translate_reverse[item] in users[user]['inventory']:
            users[user]['action'] = f'throw_{item} -'
            users[user]['ready'] = 1  # он готов сделать действие
            await update.message.reply_text("Выберите жертву")
            people = rooms[users[user]['room']]
            await update.message.reply_text('\n'.join([str(x + 1) + '. ' + people[x].split(">")[1][:-3] for x in range(len(people))]))
            return 3
        else:
            await update.message.reply_text('У вас нет этого предмета')
    else:
        users[user]['ready'] = 1
    return 1


async def throw_brick(update, context):
    p = await throw_item(update, 'brick')
    return p


async def throw_armature(update, context):
    p = await throw_item(update, 'armature')
    return p


async def throw_cement(update, context):
    p = await throw_item(update, 'cement')
    return p


async def choose_prey(update, context):
    user = update.effective_user.mention_html()
    people = rooms[users[user]['room']]
    inp = update.message.text
    nums = list(map(str, list(range(1, len(people) + 1))))
    if inp in nums + ['-']:
        act = users[user]['action'].split()
        if inp != '-':
            users[user]['ready'] = 1
            act[1] = people[int(inp) - 1]
            users[user]['action'] = ' '.join(act)
            await check_and_send(user)
    else:
        return 3
    return 1


async def stop(update, context):
    await update.message.reply_text('stopped')
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(ConversationHandler(entry_points=[CommandHandler("start", start)],
                                                states={1: [CommandHandler('take_brick', brick),
                                                            CommandHandler("join_room", join_room),
                                                            CommandHandler("take_item", take_item),
                                                            CommandHandler('throw_brick', throw_brick),
                                                            CommandHandler('throw_armature', throw_armature),
                                                            CommandHandler('throw_cement', throw_cement)],
                                                        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, throw_out)],
                                                        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_prey)]
                                                        },
                                                fallbacks=[CommandHandler('stop', stop)]))

    application.run_polling()


if __name__ == '__main__':
    main()
