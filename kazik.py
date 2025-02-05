from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import random

user_balances = {}
user_bets = {}
user_stats = {}
user_loans = {}
players = {}
active_crash_games = {}
active_duels = {}

START_BALANCE = 1000


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    username = update.message.from_user.username or f"User_{user_id}"
    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE
        players[user_id] = username
    await update.message.reply_text(
        f"🎰 Добро пожаловать в Казино!\n"
        f"💰 Ваш баланс: {user_balances[user_id]}$\n"
        "Доступные команды:\n"
        "/balance - Проверить баланс\n"
        "/casino - Играть в казино\n"
        "/russian_roulette - Играть в русскую рулетку\n"
        "/hack - Взлом казино\n"
        "/profile - Профиль игрока\n"
        "/bet - Сделать ставку на событие\n"
        "/deposit - Пополнить баланс\n"
        "/loan - Взять кредит\n"
        "/repay - Погасить кредит\n"
        "/crime - Совершить преступление\n"
        "/leaderboard - Таблица лидеров\n"
        "/duel - Дуэль\n"
    )


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not user_balances:
        await update.message.reply_text("📉 В казино пока нет игроков.")
        return

    sorted_players = sorted(user_balances.items(), key=lambda x: x[1], reverse=True)[:5]
    leaderboard_text = "🏆 Топ игроков:\n"

    for i, (user_id, balance) in enumerate(sorted_players, start=1):
        username = players.get(user_id, "Аноним")
        leaderboard_text += f"{i}. {username} - {balance}$\n"

    await update.message.reply_text(leaderboard_text)

active_duels = {}

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создание дуэли"""
    user_id = update.message.from_user.id
    args = context.args

    if len(args) < 2:
        await update.message.reply_text("❌ Используйте команду так: `/duel @username <ставка>`")
        return

    try:
        opponent_username = args[0].strip("@")
        bet = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму ставки!")
        return

    if bet <= 0:
        await update.message.reply_text("❌ Ставка должна быть больше 0!")
        return

    if user_id not in user_balances or user_balances[user_id] < bet:
        await update.message.reply_text("❌ У вас недостаточно денег для дуэли!")
        return


    opponent_id = next((uid for uid, uname in players.items() if uname == opponent_username), None)
    if opponent_id is None:
        await update.message.reply_text("❌ Игрок не найден!")
        return

    if opponent_id == user_id:
        await update.message.reply_text("❌ Нельзя вызвать себя на дуэль!")
        return

    if opponent_id in active_duels:
        await update.message.reply_text("❌ Этот игрок уже участвует в дуэли!")
        return

    active_duels[opponent_id] = (user_id, bet)
    await update.message.reply_text(f"⚔️ Вы вызвали @{opponent_username} на дуэль на {bet}$! Ждем его ответа...")
    await context.bot.send_message(opponent_id, f"⚔️ @{update.message.from_user.username} вызвал вас на дуэль на {bet}$! Введите /accept для принятия.")

async def accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Принятие дуэли"""
    user_id = update.message.from_user.id

    if user_id not in active_duels:
        await update.message.reply_text("❌ У вас нет активных вызовов на дуэль!")
        return

    opponent_id, bet = active_duels[user_id]

    if user_id not in user_balances or user_balances[user_id] < bet:
        await update.message.reply_text("❌ У вас недостаточно денег для принятия дуэли!")
        return


    user_balances[user_id] -= bet
    user_balances[opponent_id] -= bet

    await update.message.reply_text("🎲 Дуэль началась! Ожидаем результат...")
    await context.bot.send_message(opponent_id, "🎲 Дуэль началась! Ожидаем результат...")

    await asyncio.sleep(3)


    winner = random.choice([user_id, opponent_id])
    loser = opponent_id if winner == user_id else user_id

    winnings = int(bet * 2 * 0.95)
    user_balances[winner] += winnings

    await context.bot.send_message(winner, f"🎉 Вы победили в дуэли и получили {winnings}$! 💰")
    await context.bot.send_message(loser, "💀 Вы проиграли дуэль...")

    del active_duels[user_id]


async def crash(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE

    if len(context.args) == 0:
        await update.message.reply_text("📈 Используйте: `/crash <ставка>`")
        return

    try:
        bet = int(context.args[0])
        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть больше 0!")
            return
        if bet > user_balances[user_id]:
            await update.message.reply_text("❌ У вас недостаточно средств!")
            return
    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму!")
        return

    user_balances[user_id] -= bet
    await update.message.reply_text(
        f"📈 Вы поставили {bet}$, коэффициент растёт! Напишите `/cashout`, чтобы зафиксировать выигрыш.")

    active_crash_games[user_id] = {"bet": bet, "multiplier": 1.0, "active": True}

    while active_crash_games[user_id]["active"]:
        await asyncio.sleep(1)
        active_crash_games[user_id]["multiplier"] += round(random.uniform(0.1, 0.5), 2)

        if random.randint(1, 100) < 10:
            await update.message.reply_text(
                f"💥 Крэш! Коэффициент: {active_crash_games[user_id]['multiplier']:.2f}x. Вы проиграли {bet}$!")
            del active_crash_games[user_id]
            return

        await update.message.reply_text(f"📈 Текущий коэффициент: {active_crash_games[user_id]['multiplier']:.2f}x")

async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in active_crash_games or not active_crash_games[user_id]["active"]:
        await update.message.reply_text("❌ У вас нет активных игр в Crash!")
        return

    winnings = int(active_crash_games[user_id]["bet"] * active_crash_games[user_id]["multiplier"])
    user_balances[user_id] += winnings
    await update.message.reply_text(
        f"🎉 Вы зафиксировали выигрыш на {active_crash_games[user_id]['multiplier']:.2f}x и получили {winnings}$!")

    del active_crash_games[user_id]


async def rob(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if len(context.args) == 0:
        await update.message.reply_text("🏴‍☠️ Используйте: `/rob @username`")
        return

    target_username = context.args[0].strip("@")
    target_id = next((uid for uid, uname in players.items() if uname == target_username), None)

    if target_id is None or target_id not in user_balances:
        await update.message.reply_text("❌ Игрок не найден!")
        return

    if target_id == user_id:
        await update.message.reply_text("❌ Нельзя ограбить самого себя!")
        return

    if user_balances[target_id] < 100:
        await update.message.reply_text("❌ У игрока слишком мало денег для ограбления!")
        return

    if random.randint(1, 100) <= 50:
        stolen_amount = random.randint(int(user_balances[target_id] * 0.2), int(user_balances[target_id] * 0.5))
        user_balances[user_id] += stolen_amount
        user_balances[target_id] -= stolen_amount

        await update.message.reply_text(f"🏴‍☠️ Вы успешно ограбили @{target_username} и украли {stolen_amount}$!")
        await context.bot.send_message(target_id, f"🚔 Вас ограбили! Вы потеряли {stolen_amount}$!")
    else:
        fine = random.randint(100, 500)
        user_balances[user_id] -= fine
        await update.message.reply_text(f"🚔 Вас поймали! Штраф {fine}$.")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)
    await update.message.reply_text(f"💰 Ваш текущий баланс: {balance}$")


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    balance = user_balances.get(user_id, START_BALANCE)

    if user_id not in user_stats:
        user_stats[user_id] = {"wins": 0, "losses": 0}

    wins = user_stats[user_id]["wins"]
    losses = user_stats[user_id]["losses"]
    vip_status = "VIP-игрок 🏆" if balance > 10000 else "Обычный игрок"

    await update.message.reply_text(
        f"🆔 *Ваш профиль*\n"
        f"💰 *Баланс:* {balance}$\n"
        f"🎰 *Побед:* {wins} | ❌ *Поражений:* {losses}\n"
        f"🎖 *Статус:* {vip_status}",
        parse_mode="Markdown"
    )

async def hack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if user_id not in user_stats:
        user_stats[user_id] = {"wins": 0, "losses": 0}

    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE

    if len(context.args) == 0:
        await update.message.reply_text("💻 Использование: `/hack <ставка>`")
        return

    try:
        bet = int(context.args[0])
        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть больше 0!")
            return

        if bet > user_balances[user_id]:
            await update.message.reply_text("❌ У вас недостаточно средств!")
            return

        await update.message.reply_text("👨‍💻 Взлом казино начался...")

        from asyncio import sleep
        await sleep(2)

        success = random.randint(1, 100) <= 10  # 10% шанс на успех
        if success:
            winnings = bet * 5
            user_balances[user_id] += winnings
            user_stats[user_id]["wins"] += 1
            await update.message.reply_text(f"✅ Взлом успешен! Вы получили {winnings}$!\n💰 Баланс: {user_balances[user_id]}$")
        else:
            loss = bet * 2
            user_balances[user_id] -= loss
            user_stats[user_id]["losses"] += 1
            await update.message.reply_text(f"❌ Взлом не удался! -{loss}$\n💰 Баланс: {user_balances[user_id]}$")

    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму ставки!")

CRIMES = [
    ("bank", "🏦 Ограбление банка", 5000, 30),
    ("car", "🚗 Кража машины", 3000, 40),
    ("money", "💵 Подделка денег", 2000, 50),
    ("robbery", "🔪 Грабеж в переулке", 1000, 60),
    ("casino", "🎰 Ограбление казино", 7000, 20)
]
async def crime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton(crime[1], callback_data=crime[0])] for crime in CRIMES
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🚔 Выберите преступление:", reply_markup=reply_markup)

async def commit_crime(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    crime_id = query.data

    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE
    if user_id not in user_stats:
        user_stats[user_id] = {"wins": 0, "losses": 0}

    selected_crime = next((crime for crime in CRIMES if crime[0] == crime_id), None)
    if not selected_crime:
        await query.message.reply_text("❌ Ошибка! Преступление не найдено.")
        return

    crime_name, reward, success_chance = selected_crime[1:]

    await query.message.edit_text(f"🚔 Попытка {crime_name}...")

    await asyncio.sleep(3)

    if random.randint(1, 100) <= success_chance:
        user_balances[user_id] += reward
        user_stats[user_id]["wins"] += 1
        await query.message.reply_text(f"✅ Успешно! Вы получили {reward}$!\n💰 Баланс: {user_balances[user_id]}$")
    else:
        loss = reward // 2
        user_balances[user_id] -= loss
        user_stats[user_id]["losses"] += 1
        await query.message.reply_text(f"❌ Вас поймали! Штраф: {loss}$\n💰 Баланс: {user_balances[user_id]}$")

async def bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if len(context.args) < 2:
        await update.message.reply_text("❌ Используйте формат: `/bet [событие] [ставка]`")
        return

    event = " ".join(context.args[:-1])
    try:
        amount = int(context.args[-1])
        if amount <= 0:
            await update.message.reply_text("❌ Ставка должна быть больше 0!")
            return
    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму ставки!")
        return

    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE

    if user_id not in user_stats:
        user_stats[user_id] = {"wins": 0, "losses": 0}  # ✅ Добавляем игрока в stats

    if amount > user_balances[user_id]:
        await update.message.reply_text("❌ У вас недостаточно средств!")
        return

    user_balances[user_id] -= amount
    await update.message.reply_text(f"🎯 Вы сделали ставку `{amount}$` на: {event}\n⌛ Ожидаем результат...")

    await asyncio.sleep(5)

    outcome = random.choice(["win", "lose"])
    if outcome == "win":
        winnings = amount * 2
        user_balances[user_id] += winnings
        user_stats[user_id]["wins"] += 1
        await update.message.reply_text(
            f"🏆 Результат: {event} случилось!\n"
            f"🎉 Вы выиграли {winnings}$!\n"
            f"💰 Баланс: {user_balances[user_id]}$"
        )
    else:
        user_stats[user_id]["losses"] += 1
        await update.message.reply_text(
            f"❌ Результат: {event} **не** случилось...\n"
            f"💸 Вы потеряли {amount}$\n"
            f"💰 Баланс: {user_balances[user_id]}$"
        )

async def casino(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("🎲 Рулетка", callback_data="roulette")],
        [InlineKeyboardButton("🃏 Блэкджек", callback_data="blackjack")],
        [InlineKeyboardButton("🎲 Кости", callback_data="dice")],
        [InlineKeyboardButton("🃏 Покер", callback_data="poker")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите игру:", reply_markup=reply_markup)


async def request_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    user_id = query.from_user.id
    game = query.data
    context.user_data["game"] = game
    await query.message.reply_text("💵 Введите сумму ставки:")


async def set_bet(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    game = context.user_data.get("game")

    if user_id not in user_stats:
        user_stats[user_id] = {"wins": 0, "losses": 0}

    if not game:
        await update.message.reply_text("❌ Сначала выберите игру с помощью /casino")
        return

    if user_id not in user_balances:
        user_balances[user_id] = START_BALANCE

    try:
        bet = int(update.message.text)
        if bet <= 0:
            await update.message.reply_text("❌ Ставка должна быть больше 0!")
            return

        balance = user_balances.get(user_id, START_BALANCE)
        if bet > balance:
            await update.message.reply_text("❌ Недостаточно средств!")
            return

        user_bets[user_id] = bet
        user_balances[user_id] -= bet

        if game == "russian_roulette":
            await play_russian_roulette(update, context)
        if game == "roulette":
            await roulette(update, context)
        elif game == "blackjack":
            await blackjack(update, context)
        elif game == "dice":
            await dice(update, context)
        elif game == "poker":
            await poker(update, context)

    except ValueError:
        await update.message.reply_text("❌ Введите корректную сумму ставки!")


async def roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    bet = user_bets.get(user_id, 100)
    winning_number = random.randint(0, 36)
    user_number = random.randint(0, 36)

    if winning_number == user_number:
        winnings = bet * 5
        user_balances[user_id] += winnings
        await update.message.reply_text(
            f"🎉 Выпало {winning_number}, вы угадали! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")
    else:
        await update.message.reply_text(
            f"😢 Выпало {winning_number}, вы поставили {user_number}. -{bet}$\n💰 Баланс: {user_balances[user_id]}$")


async def blackjack(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    bet = user_bets.get(user_id, 100)
    user_cards = [random.randint(1, 11) for _ in range(2)]
    dealer_cards = [random.randint(1, 11) for _ in range(2)]
    user_total = sum(user_cards)
    dealer_total = sum(dealer_cards)

    await update.message.reply_text(
        f"🃏 Ваши карты: {user_cards} (сумма: {user_total})\n"
        f"🃏 Карты дилера: {dealer_cards} (сумма: {dealer_total})"
    )

    if user_total > 21:
        await update.message.reply_text(f"😢 Перебор! -{bet}$\n💰 Баланс: {user_balances[user_id]}$")
    elif dealer_total > 21 or user_total > dealer_total:
        winnings = bet * 2
        user_balances[user_id] += winnings
        await update.message.reply_text(f"🎉 Вы выиграли! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")
    elif user_total == dealer_total:
        user_balances[user_id] += bet
        await update.message.reply_text(f"🤝 Ничья! Ставка возвращена.\n💰 Баланс: {user_balances[user_id]}$")
    else:
        await update.message.reply_text(f"😢 Вы проиграли! -{bet}$\n💰 Баланс: {user_balances[user_id]}$")

async def poker(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    bet = user_bets.get(user_id, 100)

    hands = ["Пара", "Две пары", "Тройка", "Флеш", "Стрит", "Фулл-хаус", "Каре", "Стрит-флеш", "Роял-флеш"]
    player_hand = random.choice(hands)
    bot_hand = random.choice(hands)

    await update.message.reply_text(f"🃏 Ваша комбинация: {player_hand}\n🤖 Комбинация бота: {bot_hand}")

    if hands.index(player_hand) > hands.index(bot_hand):
        winnings = bet * 2
        user_balances[user_id] += winnings
        await update.message.reply_text(f"🎉 Вы выиграли! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")
    elif hands.index(player_hand) < hands.index(bot_hand):
        await update.message.reply_text(f"😢 Вы проиграли! -{bet}$\n💰 Баланс: {user_balances[user_id]}$")
    else:
        user_balances[user_id] += bet
        await update.message.reply_text(f"🤝 Ничья! Ставка возвращена.\n💰 Баланс: {user_balances[user_id]}$")


async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    bet = user_bets.get(user_id, 100)

    player_throw = random.randint(1, 6)
    bot_throw = random.randint(1, 6)

    await update.message.reply_text(f"🎲 Вы выбросили {player_throw}, бот выбросил {bot_throw}")

    if player_throw > bot_throw:
        winnings = bet * 2
        user_balances[user_id] += winnings
        await update.message.reply_text(f"🎉 Вы победили! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$")
    elif player_throw < bot_throw:
        await update.message.reply_text(f"😢 Вы проиграли! -{bet}$\n💰 Баланс: {user_balances[user_id]}$")
    else:
        user_balances[user_id] += bet
        await update.message.reply_text(f"🤝 Ничья! Ставка возвращена.\n💰 Баланс: {user_balances[user_id]}$")

async def russian_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    context.user_data["game"] = "russian_roulette"
    await update.message.reply_text("🔫 Введите сумму ставки для игры в русскую рулетку:")


async def play_russian_roulette(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    bet = user_bets.get(user_id, 100)

    bullet_position = random.randint(1, 6)
    trigger_pull = random.randint(1, 6)

    await update.message.reply_text("🔫 Вы подносите револьвер к виску и нажимаете на курок...")

    if bullet_position == trigger_pull:
        user_balances[user_id] -= bet
        await update.message.reply_text(f"💥 Бах! Вы проиграли {bet}$...\n💰 Баланс: {user_balances[user_id]}$")
    else:
        winnings = bet * 3
        user_balances[user_id] += winnings
        await update.message.reply_text(
            f"😅 Щелк! Вам повезло, барабан пуст! +{winnings}$\n💰 Баланс: {user_balances[user_id]}$"
        )

async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if not context.args:
        await update.message.reply_text("💰 Используйте команду так: `/deposit 500`")
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Сумма пополнения должна быть больше 0!")
            return

        user_balances[user_id] += amount
        await update.message.reply_text(
            f"✅ Вы пополнили баланс на {amount}$\n💰 Новый баланс: {user_balances[user_id]}$")
    except ValueError:
        await update.message.reply_text("❌ Введите корректное число!")


async def loan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if len(context.args) == 0:
        await update.message.reply_text("🏦 Используйте: `/loan <сумма>`")
        return

    try:
        amount = int(context.args[0])
        if amount <= 0:
            await update.message.reply_text("❌ Введите положительное число!")
            return

        if user_id in user_loans:
            await update.message.reply_text("❌ У вас уже есть активный кредит!")
            return

        user_loans[user_id] = amount * 1.5
        user_balances[user_id] += amount

        await update.message.reply_text(f"🏦 Вы взяли кредит {amount}$! Вам нужно вернуть {user_loans[user_id]}$.")

    except ValueError:
        await update.message.reply_text("❌ Введите корректное число!")

async def repay(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id

    if user_id not in user_loans:
        await update.message.reply_text("✅ У вас нет активных кредитов!")
        return

    if user_balances[user_id] < user_loans[user_id]:
        await update.message.reply_text("❌ У вас недостаточно денег для погашения кредита!")
        return

    user_balances[user_id] -= user_loans[user_id]
    del user_loans[user_id]

    await update.message.reply_text("✅ Вы успешно погасили свой кредит! Теперь вы свободны от долгов.")

import asyncio
from telegram import BotCommand


async def set_bot_commands(app):
    commands = [
        BotCommand("start", "📜 Open menu"),
        BotCommand("balance", "💰 Show your balance"),
        BotCommand("casino", "🎰 Play casino games"),
        BotCommand("deposit", "💵 Add money to your balance"),
        BotCommand("russian_roulette", "🔫 Play Russian roulette"),
        BotCommand("profile", "🆔 View your profile"),
        BotCommand("hack", "💻 Try to hack the casino"),
        BotCommand("bet", "💵 Place a bet on a game"),
        BotCommand("loan", "🏦 Take a loan"),
        BotCommand("repay", "💵 Repay your loan"),
        BotCommand("crime", "🚔 Commit crimes"),
        BotCommand("crash", "📈 Play Crash"),
        BotCommand("cashout", "💸 Withdraw from Crash"),
        BotCommand("rob", "🏴‍☠️ Rob another player")
    ]
    await app.bot.set_my_commands(commands)


def main():
    TOKEN = "7771538325:AAFS1STLG3C47o7-Nk6_htSV9e51A9A_1q0"
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("casino", casino))
    app.add_handler(CommandHandler("deposit", deposit))
    app.add_handler(CommandHandler("russian_roulette", russian_roulette))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("hack", hack))
    app.add_handler(CommandHandler("bet", bet))
    app.add_handler(CommandHandler("loan", loan))
    app.add_handler(CommandHandler("repay", repay))
    app.add_handler(CommandHandler("crime", crime))
    app.add_handler(CallbackQueryHandler(commit_crime, pattern="^(bank|car|money|robbery|casino)$"))
    app.add_handler(CommandHandler("balance", leaderboard))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("duel", duel))
    app.add_handler(CommandHandler("accept", accept))
    app.add_handler(CommandHandler("crash", crash))
    app.add_handler(CommandHandler("cashout", cashout))
    app.add_handler(CommandHandler("rob", rob))

    app.add_handler(CallbackQueryHandler(request_bet, pattern="^(roulette|blackjack|dice|poker)$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_bet))

    app.run_polling()


if __name__ == "__main__":
    main()