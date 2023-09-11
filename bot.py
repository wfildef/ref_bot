#импорт библиотек
import telebot
from telebot import types
import time

#импорт конфига и функций для работы с БД
import config
from sqliteTools import execute_query_one_component, execute_query_two_component

#подключения бота 
bot = telebot.TeleBot(config.botToken)

#стартовое сообщение с просьбой подписки
@bot.message_handler(commands=['start'])
def start_message(message):
    existUser = execute_query_one_component("SELECT EXISTS(SELECT userid FROM users WHERE userid = ?)", message.chat.id)[0][0]

    if existUser == 0:
        addUser = "INSERT INTO users (userid, daysSinceJoin, balance, countPartners, wasReward, existSubscribe) VALUES (?, 0, 0, 0, 0, 0)"
        execute_query_one_component(addUser, message.chat.id)

        if " " in message.text:
            referrer_candidate = message.text.split()[1]
            addRefInfo(message.chat.id, referrer_candidate)

        else:
            addRefInfo(message.chat.id, 0)

    linkForSub = execute_query_one_component("SELECT linkForSubscribe FROM channelData", "None")[0][0]

    markup = types.InlineKeyboardMarkup()
    buttons = [types.InlineKeyboardButton("Подписаться", url = linkForSub), types.InlineKeyboardButton("Проверить подписку", callback_data="CheckSubscribe")]
    markup.add(buttons[0], buttons[1])

    bot.send_message(message.chat.id, "Привет! Чтобы пользоваться ботом, подпишись на канал:", reply_markup=markup)  
    
@bot.message_handler(commands=['update'])
def updateLink(message):
    if message.chat.id == config.adminID:
        resetSubcribe(message)

#обработка команд из меню
@bot.message_handler(content_types=['text'])
def sendInfo(message):
    id = message.chat.id

    statusSubscribe = getSubcribeStatus(message)

    if not statusSubscribe:
        start_message(message)

    elif statusSubscribe:
        if message.text == "👥Партнеры":
            refMsg = getMessage("messages/refInfo.txt")

            bot.send_message(id, refMsg.format(countPartners = getUserCountPartners(id),
                                               balance = getUserBalance(id),
                                               botName = config.botName,
                                               userid = message.chat.id,    
                                               reward = config.reward), parse_mode="HTML")

        elif message.text == "🖥Профиль":
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("💵Вывести", callback_data="conclusion"))
            
            profileMsg = getMessage("messages/profile.txt")
            profileMsg = profileMsg.format(countDays = getUserCountDays(id),
                                           userid = id,
                                           balance = getUserBalance(id))
    
            bot.send_message(id, profileMsg,reply_markup=markup, parse_mode="HTML")

        elif message.text == "ℹ️О боте":
            markup = types.InlineKeyboardMarkup()

            buttons = [types.InlineKeyboardButton("💬Чат", url=config.chatLink), 
            types.InlineKeyboardButton("💳Выплаты", url=config.paymentsLink),
            types.InlineKeyboardButton("🧑‍💻Администратор", url=config.adminLink),
            types.InlineKeyboardButton("🚀Хочу такого-же бота", url=config.developerLink)]

            for button in buttons:
                markup.add(button)

            bot.send_message(id, "📚 Информация о нашем боте", reply_markup=markup)

    checkDate(message)

#обработка даты из Inline кнопок
@bot.callback_query_handler(func=lambda callback:True)
def inlin(callback):
    if callback.data == 'CheckSubscribe':
        existUserInChannel = getSubcribeStatus(callback.message)

        if existUserInChannel:
            bot.answer_callback_query(callback.id, text='Вы подписались. Можете пользоваться!', show_alert=True)

            refID = execute_query_one_component("SELECT refid FROM users WHERE userid = ?", callback.message.chat.id)[0][0]
            statusReward = execute_query_one_component("SELECT wasReward FROM users WHERE userid = ?", callback.message.chat.id)[0][0]

            if refID != 0 and statusReward == 0:
                addRewardForRef = "UPDATE users SET balance = balance + ? WHERE userid = ?"
                execute_query_two_component(addRewardForRef, config.reward, refID)

                addCountPartners = "UPDATE users SET countPartners = countPartners + 1 WHERE userid = ?"
                execute_query_one_component(addCountPartners, refID)

                changeStatusReward = "UPDATE users SET wasReward = 1 WHERE userid = ?"
                execute_query_one_component(changeStatusReward, callback.message.chat.id)

            sendMenu(callback.message.chat.id)
        else:
            bot.answer_callback_query(callback.id, text='Вы не подписались!', show_alert=True)

    if callback.data == 'conclusion':
        conclusionMsg = getMessage("messages/conclusion.txt")
        bot.edit_message_text(chat_id=callback.message.chat.id, message_id=callback.message.message_id, text=conclusionMsg)

#отправка меню бота пользователю
def sendMenu(chatID):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)

    buttons = [types.KeyboardButton("🖥Профиль"),
               types.KeyboardButton("👥Партнеры"),
               types.KeyboardButton("ℹ️О боте")]

    markup.add(buttons[0], buttons[1])
    markup.add(buttons[2])

    bot.send_message(chatID, "Воспользуйтесь нашим меню: ", reply_markup=markup)

#получение шаблона для отправки сообщения
def getMessage(path):
    message = ""
    with open(path, encoding = "utf-8") as file:
        while True:
            line = file.readline()

            if not line:
                break
            message+=line
        return message

#получение баланса пользователя
def getUserBalance(userid):
    query = "SELECT balance FROM users WHERE userid = ?"
    balance = execute_query_one_component(query, userid)[0][0]
    return balance
    
#получение количества приглашенных пользователем юзеров
def getUserCountPartners(userid):
    query = "SELECT countPartners FROM users WHERE userid = ?"
    countPartners = execute_query_one_component(query, userid)[0][0]
    return countPartners

#получение количества дней пользователя, проведенных в боте
def getUserCountDays(userid):
    query = "SELECT daysSinceJoin FROM users WHERE userid = ?"
    countDays = execute_query_one_component(query, userid)[0][0]
    return countDays

#проверка, наступил ли новый день
def checkDate(message):
    query = "SELECT currentDay FROM dates"
    dateInTable = execute_query_one_component(query, "None")[0][0]
    
    tconv = lambda x: time.strftime("%d", time.localtime(x))
    currentDay = int(tconv(message.date))

    if currentDay != dateInTable:
        execute_query_one_component("UPDATE dates SET currentDay = ?", currentDay)
        execute_query_one_component("UPDATE users SET daysSinceJoin = daysSinceJoin +  1", "None")

#добавление реферала к пользователю
def addRefInfo(id, refInfo):
    execute_query_two_component("UPDATE users SET refid = ? WHERE userid = ?", refInfo, id)

#обновление ссылки на канал для подписки
def updateLink(message):
    try:
        execute_query_two_component("UPDATE channelData SET linkForSubscribe = ?, channelID = ?", 
                                                message.text.split(";")[0],
                                                message.text.split(";")[1])

        bot.send_message(message.chat.id, "Данные успешно обновлены!")
        sendMenu(message.chat.id)
    except:
        bot.send_message(message.chat.id, "Неверный формат данных!")

#получение статуса подписки пользователя
def getSubcribeStatus(message):
    try:
        channelID = execute_query_one_component("SELECT channelID FROM channelData", "None")[0][0]
        response = bot.get_chat_member(channelID, message.chat.id)

        if response.status == 'left':
            changeStatusSubscribe = "UPDATE users SET existSubscribe = 0 WHERE userid = ?"
            execute_query_one_component(changeStatusSubscribe, message.chat.id)
            return False

        else:
            changeStatusSubscribe = "UPDATE users SET existSubscribe = 1 WHERE userid = ?"
            execute_query_one_component(changeStatusSubscribe, message.chat.id)
            return True

    except:
        print("Бот не нашёл данный канал. Ошибка в ID, либо бота нет в администраторах!")
        changeStatusSubscribe = "UPDATE users SET existSubscribe = 0 WHERE userid = ?"
        execute_query_one_component(changeStatusSubscribe, message.chat.id)
        return False

#сброс и запрос новой ссылки для подписки
def resetSubcribe(message):
    execute_query_one_component("UPDATE users SET existSubscribe = 0", "None")
    bot.send_message(message.chat.id, "Отправьте новую ссылку и айди чата в формате: https://example.com;-1929202002")
    bot.register_next_step_handler(message, updateLink)


#бесконечное ожидание сообщений от пользователя
bot.polling(none_stop=True, interval=0) 

