import logging
from data import db_session
from data.users import User
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.ERROR
)

logger = logging.getLogger(__name__)
markup = ReplyKeyboardMarkup([['/start', '/help']], one_time_keyboard=False)
keyboard = ReplyKeyboardMarkup([['/take_brick', '/take_item', '/dodge'],
            ['/throw_brick', '/throw_armature', '/throw_cement'],
            ['/throw_sand', '/repair_helmet']])
some_magic = {}
application = Application.builder().token(BOT_TOKEN).build()


async def check_and_send(usr):
    names_of_those = rooms[users[usr]['room']]  #  ники людей из той же
    #  комнаты, что и юзер
    if all(list(map(lambda x: users[x]['ready'], names_of_those))):  #  все ли готовы сделать действие?
        msg, end = brain(names_of_those)
        end_str = ''
        midle = ""
        if end:  # игра окончена?
            end_str = '\n\nВы в комнате ожидания'
            rm = users[usr]['room']   # при окончании игры комната удаляется
            del rooms[rm]
            if rm in running_games:
                running_games.remove(rm) # в комнате не идет игра
            m = [(0, []), (0, []), (0, []), (0, []), (0, []), (0, []), (0, []), (0, []), (0, [])]
            db_sess = db_session.create_session()
            for user in db_sess.query(User).filter(User.name.in_(names_of_those)):
                user.dodges += users[user.name]["dodges"]
                if m[5][0] < users[user.name]["dodges"]:
                    m[5] = (users[user.name]["dodges"], [user.name])
                elif m[5][0] == users[user.name]["dodges"]:
                    m[5] = (users[user.name]["dodges"], m[5][1] + [user.name])

                user.fixed += users[user.name]["fixed"]
                if m[4][0] < users[user.name]["fixed"]:
                    m[4] = (users[user.name]["fixed"], [user.name])
                elif m[4][0] == users[user.name]["fixed"]:
                    m[4] = (users[user.name]["fixed"], m[4][1] + [user.name])

                user.hits += users[user.name]["hits"]
                if m[7][0] < users[user.name]["hits"]:
                    m[7] = (users[user.name]["hits"], [user.name])
                elif m[7][0] == users[user.name]["hits"]:
                    m[7] = (users[user.name]["hits"], m[7][1] + [user.name])

                user.kills += users[user.name]["kills"]
                if m[6][0] < users[user.name]["kills"]:
                    m[6] = (users[user.name]["kills"], [user.name])
                elif m[6][0] == users[user.name]["kills"]:
                    m[6] = (users[user.name]["kills"], m[6][1] + [user.name])

                user.thrown_armatures += users[user.name]["throw_armaturs"]
                if m[1][0] < users[user.name]["throw_armaturs"]:
                    m[1] = (users[user.name]["throw_armaturs"], [user.name])
                elif m[1][0] == users[user.name]["throw_armaturs"]:
                    m[1] = (users[user.name]["throw_armaturs"], m[1][1] + [user.name])

                user.thrown_bricks += users[user.name]["throw_bricks"]
                if m[0][0] < users[user.name]["throw_bricks"]:
                    m[0] = (users[user.name]["throw_bricks"], [user.name])
                elif m[0][0] == users[user.name]["throw_bricks"]:
                    m[0] = (users[user.name]["throw_bricks"], m[0][1] + [user.name])

                user.thrown_cements+= users[user.name]["throw_cements"]
                if m[3][0] < users[user.name]["throw_cements"]:
                    m[3] = (users[user.name]["throw_cements"], [user.name])
                elif m[3][0] == users[user.name]["throw_cements"]:
                    m[3] = (users[user.name]["throw_cements"], m[3][1] + [user.name])

                user.thrown_sands += users[user.name]["throw_sands"]
                if m[2][0] < users[user.name]["throw_sands"]:
                    m[2] = (users[user.name]["throw_sands"], [user.name])
                elif m[2][0] == users[user.name]["throw_sands"]:
                    m[2] = (users[user.name]["throw_sands"], m[2][1] + [user.name])

                user.get_items += users[user.name]["get_items"]
                if m[8][0] < users[user.name]["get_items"]:
                    m[8] = (users[user.name]["get_items"], [user.name])
                elif m[8][0] == users[user.name]["get_items"]:
                    m[8] = (users[user.name]["get_items"], m[8][1] + [user.name])

                if users[user.name]["hp"] > 0:
                    user.wins += 1
            db_sess.commit()
            midle = f'''
Итоги игры:
{random.choice(m[0][1]).split(">")[1][:-3]} - прораб
{random.choice(m[1][1]).split(">")[1][:-3]} - железный человек
{random.choice(m[2][1]).split(">")[1][:-3]} - дед
{random.choice(m[3][1]).split(">")[1][:-3]} - асфальтоукладчик
{random.choice(m[4][1]).split(">")[1][:-3]} - фиксик
{random.choice(m[5][1]).split(">")[1][:-3]} - игрок в дарк соулс
{random.choice(m[6][1]).split(">")[1][:-3]} - киборг-убийца
{random.choice(m[7][1]).split(">")[1][:-3]} - соколиный глass
{random.choice(m[8][1]).split(">")[1][:-3]} - мусоросборщик'''
        for x in names_of_those:
            inv = users[x]['inventory']
            inv_str = 'Текущий инвентарь: '        #  рассылка ответов по этим юзерам (в some_magic хранятся переменные
                                                   #  для отсылки сообщений
            await some_magic[x].message.reply_text(msg + midle + end_str)
            for i in range(len(inv)):
                inv_str += str(i + 1) + '. ' + inv[i] + ' '
            hp_str = f'\nВаше здоровье: {int(users[x]["hp"])}'
            await some_magic[x].message.reply_text(inv_str + hp_str)
            if end:
                users[x] = {'room': "wait", 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': '0 0', 'last_dodge': 0,
                            'start_game': 0, 'item': '-', "throw_bricks": 0, "throw_armaturs": 0, "throw_cements": 0, "fixed": 0, "dodges": 0, "throw_sands": 0, "kills": 0, "hits": 0, "get_items": 0}
                with open('static/img/end.png', 'rb') as photo:
                    await some_magic[x].message.reply_photo(photo=photo)


def brain(users1):
    end = False
    all_fr = True
    fin_message = ''
    for user in users1:
        users[user]['last_dodge'] = 0  # разрешение на уворот
        act = users[user]['action'].split() # первый элемент это название действия, второй цель
        if act[0] == 'take_brick':  # обработка действий
            users[user]["get_items"] += 1
            if act[1] == '-':
                users[user]['inventory'].append('кирпич')
            else:
                users[user]['inventory'][int(act[1]) - 1] = 'кирпич' # вместо чего брать
            fin_message += f'{user.split(">")[1][:-3]} взял кирпич\n'

        elif 'take_item' in act[0]:
            item = act[0][:-9]
            users[user]["get_items"] += 1
            if act[1] == '-':  # если есть место в инвентаре
                users[user]['inventory'].append(item)
                fin_message += f'{user.split(">")[1][:-3]} взял {items[item]}\n'
            elif act[1] == '*':  # * если не взял предложенный предмет
                fin_message += f'{user.split(">")[1][:-3]} нашел {items[item]}, но выкинул(\n'
            else:
                users[user]['inventory'][int(act[1]) - 1] = item
                fin_message += f'{user.split(">")[1][:-3]} взял {items[item]}\n'

        elif act[0] == 'throw_armature':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            users[user]["throw_armaturs"] += 1
            if users[prey]['frozen'][0] == '0':  # цель не в цементе
                if prey_act[0] == 'dodge':  # увернулся?
                    fin_message += f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, но тот увернулся!\n'
                elif prey_act[0] == 'throw_sand':  # кинул песок?
                    fin_message += (f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, но промазал '
                                    f'из-за песка\n')
                else:  # арматура долетела
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}!\n'
                    users[user]["hits"] += 1
                    if users[prey]["hp"] == 0:
                        users[user]["kills"] += 1
            else:
                fin_message += (f'{user.split(">")[1][:-3]} кинул арматуру в {prey.split(">")[1][:-3]}, однако не пробил'
                                f' цемент.\n')
            users[user]['inventory'].remove('арматура')

        elif act[0] == 'throw_cement':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            users[user]["throw_cements"] += 1
            if user == prey:  # кинул в себя?
                lst = list(users[prey]['frozen'])
                lst[2] = '1'  # теперь заморожен
                users[prey]['frozen'] = ''.join(lst)
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в себя! Ну и идиот).\n'
            elif prey_act[0] == 'dodge':  # увернулся?
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но тот увернулся!\n'
            elif prey_act[0] == 'throw_sand':  # кинул песок?
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но промазал '
                                f'из-за песка\n')
            elif prey_act[0] == 'throw_brick' and ' '.join(prey_act[1:]) == user:  # цель кинула в нас кирпич
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но цемент врезался '
                                f'в кирпич\n')
            elif prey_act[0] == 'throw_cement' and ' '.join(prey_act[1:]) == user:  # цель кинула в нас цемент
                fin_message += (f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}, но он встретил на '
                                f'пути брата-цемента\n')
            else:
                lst = list(users[prey]['frozen'])
                lst[2] = '1'  # теперь заморожен
                users[prey]['frozen'] = ''.join(lst)
                fin_message += f'{user.split(">")[1][:-3]} кинул цемент в {prey.split(">")[1][:-3]}!\n'
                users[user]["hits"] += 1
            users[user]['inventory'].remove('цемент')

        elif act[0] == 'throw_brick':
            prey = ' '.join(act[1:])
            prey_act = users[prey]['action'].split()
            users[user]["throw_bricks"] += 1
            if users[prey]['frozen'][0] == '0':  # цель в цементе?
                if user == prey:  # кинул в себя?
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в себя! Ну и нафига?\n'
                elif prey_act[0] == 'dodge':  # увернулся?
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но тот увернулся!\n'
                elif prey_act[0] == 'throw_sand':  # кинул песок?
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но промазал '
                        f'из-за песка\n')
                elif prey_act[0] == 'throw_brick' and ' '.join(prey_act[1:]) == user:
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но кирпич врезался '
                        f'в ДРУГОЙ кирпич (много кирпичей однако)\n')
                elif prey_act[0] == 'throw_cement' and ' '.join(prey_act[1:]) == user:  # в нас кинули цемент?
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но он встретил на '
                        f'пути цемент :О\n')
                elif prey_act[0] == 'throw_armature' and ' '.join(prey_act[1:]) == user:  # в нас кинули кирпич?
                    fin_message += (
                        f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, но он был разбит '
                        f'летящей арматурой!\n')
                else:
                    users[prey]['hp'] -= 1
                    fin_message += f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}!\n'
                    users[user]["hits"] += 1
                    if users[prey]["hp"] == 0:
                        users[user]["kills"] += 1
            else:
                fin_message += (
                    f'{user.split(">")[1][:-3]} кинул кирпич в {prey.split(">")[1][:-3]}, однако не пробил'
                    f' цемент.\n')
            users[user]['inventory'].remove('кирпич')
        elif act[0] == 'dodge':
            fin_message += f'{user.split(">")[1][:-3]} увернулся\n'
            users[user]['last_dodge'] = 1
            users[user]["dodges"] = users[user].get("dodges", 0) + 1
        elif act[0] == 'throw_sand':
            fin_message += f'{user.split(">")[1][:-3]} кинул песок. И исчез...\n'
            users[user]['inventory'].remove('песок')
            users[user]["throw_sands"] += 1
        elif act[0] == 'repair_helmet':
            users[user]['hp'] += 1
            users[user]['inventory'].remove('каска')
            users[user]["fixed"] += 1
            fin_message += f'{user.split(">")[1][:-3]} починил каску\n'
    survived = sum(list(map(lambda x: 1 if users[x]['hp'] >= 1 else 0, users1))) # сколько выживших?
    if survived == 0:  # все умерли?
        fin_message += ('Последний негритенок посмотел устало\n Он пошел повесился, и никого не стало... \n'
                        ' Ничья: все мертвы\n')
        end = True
    for user in users1:
        fr = users[user]['frozen'].split()
        fr[0] = fr[1] # замораживаем всех, кто был зацементирован в этом раунде
        fr[1] = '0'
        users[user]['ready'] = 0
        users[user]['action'] = '- -'
        users[user]['item'] = '-'
        users[user]['frozen'] = ' '.join(fr)
        if fr[0] == '1':
            users[user]['ready'] = 1
        if users[user]['hp'] <= 0: # юзер сдох?
            if round(abs(users[user]['hp'] % 1), 2) != 0.1: # он был мертв до этого раунда?
                users[user]['hp'] = -0.1
                users[user]['ready'] = 1
                fin_message += f'{user.split(">")[1][:-3]} умер. Помянем... \n'
        else:
            all_fr = False  # не все в цементе
            if survived == 1:  # один выживший?
                fin_message += f'\n{user.split(">")[1][:-3]} победил! Поздравим его\n'
                end = True  # конец
    if all_fr: # все в цементе?
        fin_message += 'Вы навсегда будете замурованы... Вы все. Секретная концовка? \n'
        end = True  # конец
    return fin_message, end


async def start(update, context):
    user = update.effective_user.mention_html()
    some_magic[user] = update
    users[user] = {'room': "wait", 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': '0 0', 'last_dodge': 0,
                   'start_game': 0, 'item': '-', "throw_bricks": 0, "throw_armaturs": 0, "throw_cements": 0, "fixed": 0, "dodges": 0, "throw_sands": 0, "kills": 0, "hits": 0, "get_items": 0}
    db_sess = db_session.create_session()
    if len(list(db_sess.query(User).filter(User.name == user))) == 0:
        us = User()
        us.name = user
        db_sess.add(us)
        db_sess.commit()
    with open('static/img/start.png', 'rb') as photo:
        await update.message.reply_photo(photo=photo)
    await update.message.reply_html(
        rf'Привет {user}! Я бот для игры в "Догони меня кирпич!". Узнать правила можно по команде /rules',
        reply_markup=keyboard
    )
    return 1


async def rules(update, context):
    with open('rules.txt', 'r', encoding='utf-8') as file:
        await update.message.reply_text(file.read())


async def help_command(update, context):
    with open('help.txt', 'r', encoding='utf-8') as file:
        await update.message.reply_text(file.read())


async def start_game(update, context):
    user = update.effective_user.mention_html()
    room = users[user]['room']
    if room == 'wait':
        await update.message.reply_text('Вы находитесь в комнате ожидания. Для начала игры присоединитесь к другой комнате')
        return 1
    users[user]['start_game'] = 1
    if all(list(map(lambda x: users[x]['start_game'], rooms[room]))):
        running_games.append(room)
        for user1 in rooms[room]:
            users[user] = {'room': "wait", 'hp': 5, 'ready': 0, 'action': '', 'inventory': [], 'frozen': '0 0',
                           'last_dodge': 0,
                           'start_game': 0, 'item': '-', "throw_bricks": 0, "throw_armaturs": 0, "throw_cements": 0,
                           "fixed": 0, "dodges": 0, "throw_sands": 0, "kills": 0, "hits": 0, "get_items": 0}
            users[user1]["room"] = room
            await some_magic[user1].message.reply_text('Игра началась')
    return 1


#  rooms starting
async def join_room(update, context):
    user = update.effective_user.mention_html()
    try:

        #  сменить юзеру комнату или, если он еще не в списке юзеров, добавить его туда
        if context.args[0] in running_games:
            await update.message.reply_text('В комнате уже идет игра')
            return
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
    except IndexError:
        await update.message.reply_text('Не указан номер комнаты')


async def make_action(update):
    user = update.effective_user.mention_html()
    some_magic[user] = update                    #  переменная для отсылки сообщений
    if users[user]['room'] not in running_games:
        await update.message.reply_text('Игра еще не начата')
        return False
    if users[user]['frozen'][0] == '1':               #  он в цементе?
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
    if can_make:
        users[user]['ready'] = 0
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
        if 'Каска' in users[user]['inventory']:
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

async def statistics(update, context):
    user = update.effective_user.mention_html()
    if users[user]["start_game"] == 0:
        db_sess = db_session.create_session()
        us = db_sess.query(User).filter(User.name == user).first()
        if us != None:
            await update.message.reply_text(f'''{us.name.split(">")[1][:-3]}:
Кинуто кирпичей: {us.thrown_bricks} 
Кинуто арматур: {us.thrown_armatures} 
Кинуто песка: {us.thrown_sands}
Кинуто цемента: {us.thrown_cements}
Починено касок: {us.fixed}
Взято предметов: {us.get_items}
Увернулся: {us.dodges}
Убил: {us.kills}
ПопАданий: {us.hits}
Побед: {us.wins}''')
    else:
        await update.message.reply_text("Во время игры статистика не доступна")

def main():
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rules", rules))
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
                                                            CommandHandler('start_game', start_game),
                                                            CommandHandler("rules", rules),
                                                            CommandHandler("statistics", statistics),
                                                           CommandHandler("help", help_command)],
                                                        2: [MessageHandler(filters.TEXT & ~filters.COMMAND, throw_out)],
                                                        3: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_prey)]
                                                        },
                                                fallbacks=[CommandHandler('stop', stop)]))
    db_session.global_init("db/blogs.db")
    application.run_polling()


if __name__ == '__main__':
    main()
