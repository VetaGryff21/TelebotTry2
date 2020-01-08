import logging
import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import apiai
import json

ACCESS_TO_HEROKU_DB = 'postgresql://{}:{}@{}:5432/{}'.format(USERDB, PSWDB, HOSTDB, NAMEDB)

updater = Updater(token=TG_TOKEN, base_url="https://telegg.ru/orig/bot")

dispatcher = updater.dispatcher

GLOBAL_LIST = []
def startCommand(bot, update):
    bot.send_message(chat_id=update.message.chat_id, text='Привет, давай пообщаемся?')


def textMessage(bot, update):

    request = apiai.ApiAI(DF_TOKEN).text_request()
    request.lang = 'ru'
    request.session_id = 'MMBot'
    request.query = update.message.text
    responseJson = json.loads(request.getresponse().read().decode('utf-8'))
    response = responseJson['result']['fulfillment']['speech']

    if response:
        bot.send_message(chat_id=update.message.chat_id, text=response)
    else:
        bot.send_message(chat_id=update.message.chat_id, text='Я Вас не совсем понял!')


def getResult(sch):
    wdays = [[], [], [], [], [], []]
    k=0
    while len(sch) > k:
        l=0
        while l < 6:
            wd_l = weekday_list(sch, k)
            if not (wd_l[l] is None):
                wdays[l].append('{}. '.format(k+1) + sch[k].time + ' ' + wd_l[l])
            l = l + 1
        k=k+1
    l=0
    ans_l = []
    ans = ''
    while l < len(wdays):
        k=0
        while k < len(wdays[l]):
            ans = ans + wdays[l][k] + '; '
            k = k + 1
        ans_l.append(ans)
        l = l + 1
        ans = ''

    return ans_l

def getInfoFromDB(num_of_group, weekdays : list):
    engine = create_engine(ACCESS_TO_HEROKU_DB)
    base = declarative_base()

    class schedule(base):
        __tablename__ = '{}'.format(num_of_group)
        id = Column(Integer, primary_key=True)
        time = Column(String)
        monday = Column(String)
        tuesday = Column(String)
        wednesday = Column(String)
        thursday = Column(String)
        friday = Column(String)
        saturday = Column(String)

    base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()

    sch = session.query(*[schedule]).all()
    days = get_result_shedule(sch)

    days_of_week =['понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота']
    week_dict = {'понедельник': 0, 'вторник': 1, 'среда': 2, 'четверг': 3, 'пятница': 4, 'суббота': 5}
    if len(weekdays)==0 or len(weekdays)==6:
        weekdays = days_of_week
    k = 0
    ans = ''
    while k < len(weekdays):
        ans = ans + str(weekdays[k]) + ': ' + days[week_dict[weekdays[k]]] + '\n'
        k = k + 1

    return ans

def getParamResponse(response_dialog_flow):
    specifically = response_dialog_flow['result']['parameters']['specifically']
    num = response_dialog_flow['result']['parameters']['number']
    whom = response_dialog_flow['result']['parameters']['whom']
    wd = response_dialog_flow['result']['parameters']['weekday']
    wd1 = response_dialog_flow['result']['parameters']['weekday1']
    wd2 = response_dialog_flow['result']['parameters']['weekday2']
    wd3 = response_dialog_flow['result']['parameters']['weekday3']
    wd4 = response_dialog_flow['result']['parameters']['weekday4']
    wd5 = response_dialog_flow['result']['parameters']['weekday5']
    wds_fir = [wd, wd1, wd2, wd3, wd4, wd5]
    wds = [i for i in wds_fir if i !='']
    return [specifically, num, whom, wds]

def makeAnswer(bot: Bot, update: Update):
    global GLOBAL_LIST
    text = update.message.text
    response_dialog_flow = send_message_dflow(text)

    if (response_dialog_flow['result']['action'] == 'question_along_a_schedule' and
        response_dialog_flow['result']['parameters']['specifically'] != '' and
        response_dialog_flow['result']['parameters']['whom'] != '') or GLOBAL_LIST != []:

        if GLOBAL_LIST == []:
            par_df = get_par_df(response_dialog_flow)
            specifically, num, whom, weekdays = par_df[0], par_df[1], par_df[2], par_df[3]
            if whom != 'деканат' and num == '':
                GLOBAL_LIST = par_df
                bot_answer = 'напиши номер группы - 6 цифр'
            else:
                table_name = whom + '_' + num
                bot_answer = get_info_from_db(table_name, weekdays)

        else:
            specifically, num, whom, weekdays = GLOBAL_LIST[0], GLOBAL_LIST[1], GLOBAL_LIST[2], GLOBAL_LIST[3]
            num = response_dialog_flow['result']['parameters']['number']
            if len(num) == 6:
                GLOBAL_LIST = []
                table_name = whom + '_' + num
                bot_answer = get_info_from_db(table_name, weekdays)
            else:
                bot_answer = response_dialog_flow['result']['fulfillment']['speech']

    else:
        bot_answer = response_dialog_flow['result']['fulfillment']['speech']

    send_message(bot, update, bot_answer)


start_command_handler = CommandHandler('start', startCommand)
text_message_handler = MessageHandler(Filters.text, textMessage)

dispatcher.add_handler(start_command_handler)
dispatcher.add_handler(text_message_handler)

updater.start_polling(clean=True)
updater.idle()
