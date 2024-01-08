import logging
import telebot
import datetime
import os
from telebot import types
import pandas as pd
import pickle
from model import predict, save_excel, predict_excel

TOKEN_DEV = '6727865891:AAF_G_BcdM6jjRWmOd1Bw8wLS064iCze4Hk'
bot = telebot.TeleBot(TOKEN_DEV)
logger = telebot.logger
logger.setLevel(logging.DEBUG)

@bot.message_handler(commands=['start'])
def start(message):
    msg = bot.send_message(message.chat.id,
                           f'''Привет, {message.from_user.username}! Я бот, который предсказывает окклюзию лучевой артерии.''')
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    btn1 = types.KeyboardButton(text='Да')
    btn2 = types.KeyboardButton(text='Нет')
    markup.add(btn1, btn2)
    msg = bot.send_message(message.chat.id,
                           f'''Вводился ли антикоагулянт, кроме гепарина? (Да/Нет)''',
                           reply_markup=markup)
    bot.register_next_step_handler(message, enter_anticoag)
    # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    # btn1 = types.KeyboardButton(text='1')
    # btn2 = types.KeyboardButton(text='2')
    # markup.add(btn1, btn2)
    # msg = bot.send_message(message.chat.id,
    #                        f'''Что выберете? (1/2)''')
    # bot.register_next_step_handler(msg, razvilka)
# def razvilka(message):
#     markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
#     btn1 = types.KeyboardButton(text='Да')
#     btn2 = types.KeyboardButton(text='Нет')
#     markup.add(btn1, btn2)
#     msg = bot.send_message(message.chat.id,
#                                    f'''Вводился ли антикоагулянт, кроме гепарина? (Да/Нет)''',
#                                   reply_markup=markup)
#     bot.register_next_step_handler(message, enter_anticoag)
#     # elif message.text == '2':
#     #     msg = bot.send_message(message.chat.id,
#     #                            f'''Введите эксель файл, где обязательно должна присутствовать шапка с колонками Patient Number,Sex,Smg,DM,AH,Age,Ht,Wt''')
#     #     bot.register_next_step_handler(message, handle_excel_file)
def handle_excel_file(message):
    input_file_path = 'output/downloaded_excel.xlsx'
    result_file_path = 'output/predictions.xlsx'

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    with open(input_file_path, 'wb') as input_file:
        input_file.write(downloaded_file)

    predict_excel(input_file_path, result_file_path, 'mode.txt')

    bot.send_message(message.chat.id, "Результат с предсказаниями (колонка prob):")

    with open(result_file_path, 'rb') as result_file:
        msg = bot.send_document(message.chat.id, result_file)

    os.remove(input_file_path)
    os.remove(result_file_path)

    bot.register_next_step_handler(msg, rerun)
    return

def rerun(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    btn1 = types.KeyboardButton(text='Да')
    btn2 = types.KeyboardButton(text='Нет')
    markup.add(btn1, btn2)
    msg = bot.send_message(message.chat.id,
                           f'''Вводился ли антикоагулянт, кроме гепарина? (Да/Нет)''',
                           reply_markup=markup)
    bot.register_next_step_handler(message, enter_anticoag)

def enter_anticoag(message):
    global anticoag
    if message.text == 'Да':
        anticoag = 1
    elif message.text == 'Нет':
        anticoag = 0
    elif message.text == 'Заново':
        bot.register_next_step_handler(message, rerun)
    else:
        msg = bot.send_message(message.chat.id, 'Некорректное значение')
        bot.register_next_step_handler(msg, enter_anticoag)
    if anticoag == 1:
        msg = bot.send_message(message.chat.id,
                               'Извините, данный пациент не может участвовать в исследовании')
        rerun(message)
        return
    elif message.text == 'Заново':
        bot.register_next_step_handler(message, rerun)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='0')
        btn2 = types.KeyboardButton(text='1')
        btn3 = types.KeyboardButton(text='Заново')
        markup.add(btn1, btn2, btn3)
        msg = bot.send_message(message.chat.id,
                               'Введите Тест Барбо до процедуры (При паттернах А, В, С - "0", при паттерне D - "1")',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_test)



def enter_test(message):
    global testB
    if message.text == '0':
        testB = 0
    elif message.text == '1':
        testB = 1
    elif message.text == 'Заново':
        rerun(message)
        return
    else:
        msg = bot.send_message(message.chat.id, 'Некорректное значение')
        bot.register_next_step_handler(msg, enter_test)
        return
    if testB == 1:
        msg = bot.send_message(message.chat.id,
                               'Извините, данный пациент не может участвовать в исследовании')
        rerun(message)
        return
    elif message.text == 'Заново':
        bot.register_next_step_handler(message, rerun)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='Заново')
        markup.add(btn1)
        msg = bot.send_message(message.chat.id,
                               'Введите номер пациента',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, index_pacient)


def index_pacient(message):
    global ind_patient
    try:
        if message.text == 'Заново':
            rerun(message)
            return
        ind_patient = int(message.text)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='М')
        btn2 = types.KeyboardButton(text='Ж')
        btn3 = types.KeyboardButton(text='Заново')
        markup.add(btn1, btn2, btn3)
        msg = bot.send_message(message.chat.id,
                               'Введите пол пациента М/Ж',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_sex)
    except:
        if message.text == 'Заново':
            rerun(message)
            return
        msg = bot.send_message(message.chat.id,
                               'Некорректное значение')
        bot.register_next_step_handler(msg, index_pacient)

def enter_sex(message):
    global SEX

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    btn1 = types.KeyboardButton(text='Заново')
    markup.add(btn1)
    if message.text == 'М':
        SEX = 1
        msg = bot.send_message(message.chat.id,
                               'Введите рост пациента в см.',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_ht)
    elif message.text == 'Ж':
        SEX = 2
        msg = bot.send_message(message.chat.id,
                               'Введите рост пациента в см.',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_ht)
    elif message.text == 'Заново':
        rerun(message)
    else:
        if message.text == 'Заново':
            rerun(message)
        msg = bot.send_message(message.chat.id,
                               'Некорректное значение')
        bot.register_next_step_handler(msg, enter_sex)

def enter_ht(message):
    global HT
    try:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='Заново')
        markup.add(btn1)
        if message.text == 'Заново':
            rerun(message)
            return
        elif 140 < int(message.text) < 220:
            msg = bot.send_message(message.chat.id,
                                   'Введите вес пациента в кг.',
                                   reply_markup=markup)
            HT = message.text
            bot.register_next_step_handler(msg, enter_wt)
        else:
            msg = bot.send_message(message.chat.id,
                                   'Некорректное значение')
            bot.register_next_step_handler(msg, enter_ht)
    except:
        if message.text == 'Заново':
            rerun(message)
            return
        msg = bot.send_message(message.chat.id,
                               'Некорректное значение')
        bot.register_next_step_handler(msg, enter_ht)


def enter_wt(message):
    global WT
    try:
        if message.text == 'Заново':
            rerun(message)
            return
        elif 20 < int(message.text) < 300:
            WT = message.text
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
            btn1 = types.KeyboardButton(text='Да')
            btn2 = types.KeyboardButton(text='Нет')
            btn3 = types.KeyboardButton(text='Заново')
            markup.add(btn1, btn2, btn3)
            msg = bot.send_message(message.chat.id, 'Курение. Введите Да/Нет.', reply_markup=markup)
            bot.register_next_step_handler(msg, enter_smg)
        else:
            msg = bot.send_message(message.chat.id, 'Некорректное значение')
            bot.register_next_step_handler(msg, enter_wt)
    except ValueError:
        if message.text == 'Заново':
            rerun(message)
            return
        msg = bot.send_message(message.chat.id, 'Некорректное значение')
        bot.register_next_step_handler(msg, enter_wt)



def enter_smg(message):
    global SMG
    if message.text == 'Да':
        SMG = 1
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='Да')
        btn2 = types.KeyboardButton(text='Нет')
        btn3 = types.KeyboardButton(text='Заново')
        markup.add(btn1, btn2, btn3)
        msg = bot.send_message(message.chat.id,
                               'Сахарный диабет 2 типа. Да/нет.',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_dm)
    elif message.text == 'Нет':
        SMG = 0
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='Да')
        btn2 = types.KeyboardButton(text='Нет')
        btn3 = types.KeyboardButton(text='Заново')
        markup.add(btn1, btn2, btn3)
        msg = bot.send_message(message.chat.id,
                               'Сахарный диабет 2 типа. Да/нет.',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_dm)
    elif message.text == 'Заново':
        rerun(message)
    else:
        if message.text == 'Заново':
            rerun(message)
        msg = bot.send_message(message.chat.id,
                               'Некорректное значение')
        bot.register_next_step_handler(msg, enter_smg)



def enter_dm(message):
    global DM
    if message.text == 'Да':
        DM = 1
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='Да')
        btn2 = types.KeyboardButton(text='Нет')
        btn3 = types.KeyboardButton(text='Заново')
        markup.add(btn1, btn2, btn3)
        msg = bot.send_message(message.chat.id,
                               'Артериальная гипертензия. Введите да/нет.',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_ah)
    elif message.text == 'Нет':
        DM = 0
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
        btn1 = types.KeyboardButton(text='Да')
        btn2 = types.KeyboardButton(text='Нет')
        btn3 = types.KeyboardButton(text='Заново')
        markup.add(btn1, btn2,btn3)
        msg = bot.send_message(message.chat.id,
                               'Артериальная гипертензия. Введите да/нет.',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_ah)
    elif message.text == 'Заново':
        rerun(message)
    else:
        if message.text == 'Заново':
            rerun(message)
        msg = bot.send_message(message.chat.id,
                               'Некорректное значение')
        bot.register_next_step_handler(msg, enter_dm)


def enter_ah(message):
    global AH
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    btn1 = types.KeyboardButton(text='Заново')
    markup.add(btn1)
    if message.text == 'Да':
        AH = 1
        msg = bot.send_message(message.chat.id,
                               'Введите возраст пациента',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_age)
    elif message.text == 'Нет':
        AH = 0
        msg = bot.send_message(message.chat.id,
                               'Введите возраст пациента',
                               reply_markup=markup)
        bot.register_next_step_handler(msg, enter_age)
    elif message.text == 'Заново':
        rerun(message)
    else:
        if message.text == 'Заново':
            rerun(message)
        msg = bot.send_message(message.chat.id,
                               'Некорректное значение')
        bot.register_next_step_handler(msg, enter_ah)



def enter_age(message):
    global AGE
    try:
        if message.text == 'Заново':
            rerun(message)
        elif 0 < int(message.text) < 100:
            AGE = message.text
            info(message)
        else:
            msg = bot.send_message(message.chat.id,
                                   f'''Некорректное значение''')
            bot.register_next_step_handler(msg, enter_age)
    except ValueError:
        if message.text == 'Заново':
            rerun(message)
        msg = bot.send_message(message.chat.id,
                               f'''Некорректное значение''')
        bot.register_next_step_handler(msg, enter_age)


def info(message):
    res = predict('mode.txt', int(SEX), float(WT)*10000 / float(HT) / float(HT), int(SMG), int(DM), int(AH), int(AGE),
                  int(HT), int(WT))
    msg = bot.send_message(message.chat.id,
                           f'''Вероятность окклюзии равна {round(res,2)}''')
    data = {
        'Patient Number': ind_patient,
        'Sex': int(SEX),
        'BMI': float(WT) * 10000/ float(HT) / float(HT),
        'Smg': int(SMG),
        'DM': int(DM),
        'AH': int(AH),
        ' ': int(AGE),
        'Ht': int(HT),
        'Wt': int(WT),
        'Prob': int(res)
    }
    save_excel(data)
    rerun(message)

    return

bot.infinity_polling(timeout=10, long_polling_timeout = 10)
