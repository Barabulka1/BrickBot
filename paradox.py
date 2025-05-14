import logging
from fileinput import close

from telebot.types import Update, Message
from telegram.ext import Application, MessageHandler, filters, ConversationHandler
from config import BOT_TOKEN
from telegram.ext import CommandHandler
from telegram import ReplyKeyboardMarkup
import random

rooms = {}
running_games = []
users = {}
items = {'песок': 'песок', 'каска': 'каску', 'цемент': 'цемент', 'арматура': 'арматуру'}
items_translate = {'песок': 'sand', 'каска': 'helmet', 'цемент': 'cement', 'арматура': 'armature'}
items_translate_reverse = {'brick': 'кирпич', 'armature': 'арматура', 'cement': 'цемент'}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
markup = ReplyKeyboardMarkup([['/start', '/help']], one_time_keyboard=False)
keyboard = ReplyKeyboardMarkup([['/take_brick', '/take_item', '/dodge'],
            ['/throw_brick', '/throw_armature', '/throw_cement'],
            ['/throw_sand', '/repair_helmet']])
some_magic = {}


async def check_and_send(usr):
    names_of_those = rooms[users[usr]['room']]  #  ники людей из той же
    #  комнаты, что и юзер
    if all(list(map(lambda x: users[x]['ready'], names_of_those))):  #  все ли готовы сделать действие?
        msg, end = brain(names_of_those)
        end_str = ''
        if end:
            end_str = '\n\nИгра закончена, вы в комнате ожидания'
            rm = users[usr]['room']
            del rooms[rm]
            if rm in running_games:
                running_games.remove(rm)
        for x in names_of_those:
            inv = users[x]['inventory']
            inv_str = 'Текущий инвентарь: '        #  рассылка ответов по этим юзерам (в some_magic хранятся переменные
                                                   #  для отсылки сообщений
            await some_magic[x].message.reply_text(msg + end_str)
            for i in range(len(inv)):
                inv_str += str(i + 1) + '. ' + inv[i] + ' '
            hp_str = f'\nВаше здоровье: {int(users[x]["hp"])}'
            await some_magic[x].message.reply_text(inv_str + hp_str)
            if end:
                users[x]['start_game'] = 0
                users[x]['room'] = 'wait'


def brain(users1):
    end = False
    all_fr = True
    fin_message = ''
    for user in users1:
        users[user]['last_dodge'] = 0
        act = users[user]['action'].split()
        print(act)
        if act[0] == 'take_brick':
            if act[1] == '-':
                users[user]['inventory'].append('кирпич')
            else:
                users[user]['inventory'][int(act[1]) - 1] = 'кирпич'
            fin_message += f'{user.split(">")[1][:-3]} взял кирпич\n'

        elif 'take_item' in act[0]:
            item = act[0][:-9]
            if act[1] == '-':
                users[user]['inventory'].append(item)
                fin_message += f'{user.split(">")[1][:-3]} взял {items[item]}\n'
            elif act[1] == '*':
                fin_message += f'{user.split(">")[1][:-3]} нашел {items[item]}, но выкинул(\n'
            else:
                users[user]['inventory'][int(act[1]) - 1] = item
                fin_message += f'{user.split(">")[1][:-3]} взял {items[item]}\n'

        elif act[0] == 'throw_armature':
            print(users[user]['inventory'])
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            if users[prey]['frozen'][0] == '0':
                if prey_act[0] == 'dodge':
                    fin_message += f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, но тот увернулся!\n'
                elif prey_act[0] == 'throw_sand':
                    fin_message += (f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, но промазал '
                                    f'из-за песка\n')
                else:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}!\n'
            else:
                fin_message += (f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, однако не пробил'
                                f' цемент.\n')
            users[user]['inventory'].remove('арматура')

        elif act[0] == 'throw_cement':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            print(users[user]['inventory'], prey_act)
            if user == prey:
                lst = list(users[prey]['frozen'])
                lst[2] = '1'
                users[prey]['frozen'] = ''.join(lst)
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в себя! Ну и идиот).\n'
            elif prey_act[0] == 'dodge':
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но тот увернулся!\n'
            elif prey_act[0] == 'throw_sand':
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но промазал '
                                f'из-за песка\n')
            elif prey_act[0] == 'throw_brick' and ' '.join(prey_act[1:]) == user:
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но цемент врезался '
                                f'в кирпич\n')
            elif prey_act[0] == 'throw_cement' and ' '.join(prey_act[1:]) == user:
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но он встретил на '
                                f'пути брата-цемента\n')
            else:
                lst = list(users[prey]['frozen'])
                lst[2] = '1'
                users[prey]['frozen'] = ''.join(lst)
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}!\n'
            users[user]['inventory'].remove('цемент')

        elif act[0] == 'throw_brick':
            print(users[user]['inventory'])
            prey = ' '.join(act[1:])
            print(prey)
            prey_act = users[prey]['action'].split()
            if users[prey]['frozen'][0] == '0':
                if user == prey:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в себя! Ну и нафига?\n'
                elif prey_act[0] == 'dodge':
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но тот увернулся!\n'
                elif prey_act[0] == 'throw_sand':
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но промазал '
                        f'из-за песка\n')
                elif prey_act[0] == 'throw_brick' and ' '.join(prey_act[1:]) == user:
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но кирпич врезался '
                        f'в ДРУГОЙ кирпич (много кирпичей однако)\n')
                elif prey_act[0] == 'throw_cement' and ' '.join(prey_act[1:]) == user:
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но он встретил на '
                        f'пути цемент :О\n')
                elif prey_act[0] == 'throw_armature' and ' '.join(prey_act[1:]) == user:
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но он был разбит '
                        f'летящей арматурой!\n')
                else:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}!\n'
            else:
                fin_message += (
                    f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, однако не пробил'
                    f' цемент.\n')
            users[user]['inventory'].remove('кирпич')
        elif act[0] == 'dodge':
            fin_message += f'{user.split(">")[1][:-3]} увернулся\n'
            users[user]['last_dodge'] = 1
        elif act[0] == 'throw_sand':
            fin_message += f'{user.split(">")[1][:-3]} кинул песок. И исчез...\n'
            users[user]['inventory'].remove('песок')
        elif act[0] == 'repair_helmet':
            users[user]['hp'] += 1
            users[user]['inventory'].remove('каска')
            fin_message += f'{user.split(">")[1][:-3]} починил каску\n'
    survived = sum(list(map(lambda x: 1 if users[x]['hp'] >= 1 else 0, users1)))
    if survived == 0:
        fin_message += ('Последний негритенок посмотел устало\n Он пошел повесился, и никого не стало... \n'
                        ' Ничья: все мертвы\n')
        return fin_message, True
    for user in users1:
        fr = users[user]['frozen'].split()
        print(user, fr)
        fr[0] = fr[1]
        fr[1] = '0'
        users[user]['ready'] = 0
        users[user]['action'] = '- -'
        users[user]['item'] = '-'
        users[user]['frozen'] = ' '.join(fr)
        if fr[0] == '1':
            print(user, fr)
            users[user]['ready'] = 1
        if users[user]['hp'] <= 0:
            print(abs(users[user]['hp'] % 1))
            if round(abs(users[user]['hp'] % 1), 2) != 0.1:
                users[user]['hp'] = -0.1
                users[user]['ready'] = 1
                fin_message += f'{user.split(">")[1][:-3]} умер. Помянем... \n'
        else:
            all_fr = False
            if survived == 1:
                fin_message += f'\n{user.split(">")[1][:-3]} победил! Поздравим его\n'
                end = True
    if all_fr:
        fin_message += 'Вы навсегда будете замурованы... Вы все. Секретная концовка? \n'
        end = True
    return fin_message, end


async def start(update, context):
    user = update.effective_user.mention_html()
    some_magic[user] = update
    users[user] = {'room': "wait", 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': '0 0', 'last_dodge': 0,
                   'start_game': 0, 'item': '-'}
    await update.message.reply_html(
        rf'Привет {user}! Я бот для игры в "Догони меня кирпич!". Узнать правила можно по команде /rules',
        reply_markup=keyboard
    )
    return 1


async def rules(update, context):
    await update.message.reply_text('potom dobavlu')


async def help_command(update, context):
    await update.message.reply_text("Я пока не умею помогать... Я только ваше эхо.")


async def start_game(update, context):
    user = update.effective_user.mention_html()
    room = users[user]['room']
    if room == 'wait':
        await update.message.reply_text('Вы находитесь в комнате ожидания. Для начала игры присоединитесь к другой комнате')
        return 1
    users[user]['start_game'] = 1
    print(list(map(lambda x: users[x]['start_game'], rooms[room])))
    if all(list(map(lambda x: users[x]['start_game'], rooms[room]))):
        running_games.append(room)
        for user1 in rooms[room]:
            users[user1] = {'room': room, 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': '0 0',
                           'last_dodge': 0, 'start_game': 0, 'item': '-'}
            await some_magic[user1].message.reply_text('Игра началась')
    return 1


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

    users[user]['start_game'] = 0
    await update.message.reply_text('Успешно добавлена комната')


async def make_action(update):
    user = update.effective_user.mention_html()
    some_magic[user] = update                    #  переменная для отсылки сообщений
    print(users[user]['frozen'])
    print(users[user]['room'], running_games)
    if users[user]['room'] not in running_games:
        await update.message.reply_text('Игра еще не начата')
        return False
    if users[user]['frozen'][0] == '1':               #  он в цементе?
        print('cement')
        await update.message.reply_text('Пока вы в цементе, вы ничего не можете делать')
        users[user]['ready'] = 1
        return False
    if users[user]['hp'] <= 0:               #  он в цементе?
        await update.message.reply_text('Мертвые не кусаются! Прекратите')
        users[user]['ready'] = 1
        return False
    return True


async def brick(update, context):
    user = update.effective_user.mention_html()
    can_make = await make_action(update)                #  не в цементе ли юзер?
    if can_make:
        users[user]['ready'] = 0
        if 'кирпич' not in users[user]['inventory']:   #  нет ли у юзера кирпича уже (можно держать один за раз)
            users[user]['action'] = 'take_brick -'  #  вместо прочерка будет стоять номер слота, куда будет
            #  взят кирпич или в кого будет кинут предмет (для действия кидания)
            inv = users[user]['inventory']
            if len(inv) >= 3:  #  не переполнен ли инвентарь?
                await update.message.reply_text("Нужно выкинуть что-то. Инвентарь переполнен")
                await update.message.reply_text(f"1. {inv[0]} 2. {inv[1]} 3. {inv[2]}'-' нафиг эти ваши "
                                                f"кирпичи, так обойдусь")
                return 2
            else:
                users[user]['action'] = 'take_brick -'
                users[user]['ready'] = 1                     #  он готов сделать действие
                await update.message.reply_text("Теперь у вас будет кирпич!")
                await check_and_send(user)
        else:
            await update.message.reply_text('У вас уже есть кирпич')
    return 1


async def take_item(update, context):
    user = update.effective_user.mention_html()
    can_make = await make_action(update)                #  не в цементе ли юзер?
    print(can_make)
    if can_make:
        users[user]['ready'] = 0
        print(users[user]['item'])
        if users[user]['item'] == '-':
            item = random.choice(['песок', 'каска', 'цемент', 'арматура'])
            users[user]['item'] = item
        else:
            item = users[user]['item']
        users[user]['action'] = f'{item}take_item -'
        inv = users[user]['inventory']
        if len(inv) >= 3:  #  не переполнен ли инвентарь?
            await update.message.reply_text("Инвентарь переполнен! Надо что-то выкинуть")
            await update.message.reply_text(f"1. {inv[0]} 2. {inv[1]} 3. {inv[2]}\n'-' - выбросить "
                                                f"текущий предмет({item})")
            return 2
        else:
            users[user]['ready'] = 1                     #  он готов сделать действие
            await update.message.reply_text(f"В начале следующего хода вы получите {items[item]}!")
            await check_and_send(user)
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
    can_make = await make_action(update)  # не в цементе ли юзер?
    if can_make:
        users[user]['ready'] = 0
        if items_translate_reverse[item] in users[user]['inventory']:
            users[user]['action'] = f'throw_{item} -'
            await update.message.reply_text("Выберите жертву")
            people = rooms[users[user]['room']]
            await update.message.reply_text('\n'.join([str(x + 1) + '. ' + people[x].split(">")[1][:-3] for x in range(len(people))]))
            return 3
        else:
            await update.message.reply_text('У вас нет этого предмета')
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
            act[1] = people[int(inp) - 1]
            users[user]['action'] = ' '.join(act)
            users[user]['ready'] = 1
            await check_and_send(user)
    else:
        return 3
    return 1


async def dodge(update, context):
    user = update.effective_user.mention_html()
    can_make = await make_action(update)  # не в цементе ли юзер?
    if can_make:
        users[user]['ready'] = 0
        if not users[user]['last_dodge']:
            users[user]['action'] = 'dodge -'
            await update.message.reply_text('Кирпичи, арматуры, цемент вам больше не страшны! Вы БУКВАЛЬНО неуязвимы! '
                                            '(*Только на этот раунд).')
            users[user]['ready'] = 1
            await check_and_send(user)
        else:
            await update.message.reply_text('Вы уже уворачивались в прошлом раунде! В этом нельзя')
    return 1


async def throw_sand(update, context):
    user = update.effective_user.mention_html()
    can_make = await make_action(update)  # не в цементе ли юзер?
    if can_make:
        users[user]['ready'] = 0
        if 'песок' in users[user]['inventory']:
            users[user]['action'] = 'throw_sand -'
            await update.message.reply_text('Песок скроет вас от врагов. Песок милостив...')
            users[user]['ready'] = 1
            await check_and_send(user)
        else:
            await update.message.reply_text('Жулик! У тебя нет песка!')
    return 1


async def repair_helmet(update, context):
    user = update.effective_user.mention_html()
    can_make = await make_action(update)  # не в цементе ли юзер?
    if can_make:
        users[user]['ready'] = 0
        if 'каска' in users[user]['inventory']:
            if users[user]['hp'] <= 1:
                await update.message.reply_text('Каска сломана! Вы больше не можете ее чинить')
            elif users[user]['hp'] >= 5:
                await update.message.reply_text('У вас полностью целая каска. Целое не починишь!')
            else:
                users[user]['action'] = 'repair_helmet -'
                await update.message.reply_text('Ваша каска станет немного прочней')
                users[user]['ready'] = 1
                await check_and_send(user)
        else:
            await update.message.reply_text('У вас нет каски (вообще это крепление для каски, это объясняет, '
                                            'почему вы чините им каску)')
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
                                                            CommandHandler('throw_cement', throw_cement),
                                                            CommandHandler('dodge', dodge),
                                                            CommandHandler('throw_sand', throw_sand),
                                                            CommandHandler('repair_helmet', repair_helmet),
                                                            CommandHandler('start_game', start_game)],
                                                        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, throw_out)],
                                                        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_prey)]
                                                        },
                                                fallbacks=[CommandHandler('stop', stop)]))

    application.run_polling()


if __name__ == '__main__':
    main()
