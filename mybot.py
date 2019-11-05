import logging
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import apiai
import json

updater = Updater(token=TG_TOKEN, base_url="https://telegg.ru/orig/bot")

dispatcher = updater.dispatcher


def startCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Привет, давай пообщаемся?')


def textMessage(bot, update):

    request = apiai.ApiAI(DF_TOKEN).text_request()
    request.lang = 'ru'
    request.session_id = 'MMBot'
    request.query = update.message.text
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    response = responseJson['result']['fulfillment']['speech']

    #Здесь может быть отправка распознанного запроса к базе вопрос-ответ.

    if response:
        bot.send_message(chat_id=update.message.chat_id, text=response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Я Вас не совсем понял!')


start_command_handler = CommandHandler('start', startCommand)
text_message_handler = MessageHandler(Filters.text, textMessage)

dispatcher.add_handler(start_command_handler)
dispatcher.add_handler(text_message_handler)

updater.start_polling(clean=True)
updater.idle()
