import os

import re

import requests
import subprocess
import psycopg2
from psycopg2 import Error
import logging
import paramiko
from telegram import Update, ForceReply
from dotenv import load_dotenv, find_dotenv
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, CallbackContext


load_dotenv(find_dotenv())
updater = Updater(os.getenv('TOKEN'), use_context=True)

logging.basicConfig(filename='logfile.txt', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)



def start(update: Update, context):
    user = update.effective_user
    update.message.reply_text(f'Привет {user.full_name}!')


def echo(update: Update, context):
    update.message.reply_text(update.message.text)

def findPhoneNumbersCommand(update: Update, context):
    update.message.reply_text('Введите текст для поиска телефонных номеров')
    return 'findPhoneNumbers'
def findPhoneNumbers(update: Update, context):
    user_input = update.message.text
    global phoneNumbers
    #phoneNumRegex = re.compile(r'8 \(\d{3}\) \d{3}-\d{2}-\d{2}') # 8 (000) 000-00-00
    phoneNumRegex = re.compile(r'8[\- ]?\(?\d{3}\)?[\- ]?\d{3}[\- ]?\d{2}[\- ]?\d{2}|\+7[\- ]?\(?\d{3}\)?[\- ]?\d{3}[\- ]?\d{2}[\- ]?\d{2}')
    phoneNumberList = phoneNumRegex.findall(user_input)
    phoneNumberList = list(set(phoneNumberList))
    if not phoneNumberList:
        update.message.reply_text('Телефонные номера не найдены')
        return ConversationHandler.END
    phoneNumbers = ''
    phoneNumbers_prety = ''
    for i in range(len(phoneNumberList)):
        phoneNumbers += f'{phoneNumberList[i]}\n'
    for i in range(len(phoneNumberList)):
        phoneNumbers_prety += f"{i + 1}. {phoneNumberList[i]}\n"
    update.message.reply_text(phoneNumbers_prety)
    update.message.reply_text("Записать найденные телефоны в базу данных? [Д/н]")
    return 'save_phones'

def save_phones(update: Update, context):
    answer = update.message.text
    if (answer == 'Д'):
        addPhones()
        update.message.reply_text("Телефоны добавлены")
        return ConversationHandler.END
    else:
        update.message.reply_text("Нет так нет")
        return ConversationHandler.END

def addPhones():
    try:    
        connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'),database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        phones_split = phoneNumbers.split("\n")
        for phone in phones_split:
            cursor.execute(f"INSERT INTO phones (phone) VALUES('{phone}')")
        connection.commit()
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с POSTGRESQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()

def findEmailAddressCommand(update: Update, context):
    update.message.reply_text("Введите текст для поиска email адресов")
    return 'findEmailAddress'

def findEmailAddress(update: Update, context):
    global emails
    user_input = update.message.text
    emailRegex = re.compile(r'\w+@+\w+.+\w+') # какойтотекст@какойтотекст.какойтотекст

    emailList = emailRegex.findall(user_input)
    emailList = list(set(emailList))
    if not emailList:
        update.message.reply_text('Email не найден')
        return ConversationHandler.END
    emails = ''
    emails_prety = ''
    for i in range(len(emailList)):
        emails += f'{emailList[i]}\n'
    for i in range(len(emailList)):
        emails_prety += f"{i+1}. {emailList[i]}\n"
    update.message.reply_text(emails_prety)
    update.message.reply_text("Записать найденные email адреса в базу данных? [Д/н]")
    return 'save_emails'

def save_emails(update: Update, context):
    answer = update.message.text
    if (answer == 'Д'):
        addEmails()
        update.message.reply_text("Адреса добавлены")
        return ConversationHandler.END
    else:
        update.message.reply_text("нет так нет")
        return ConversationHandler.END

def addEmails():
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        emails_split = emails.split("\n")
        for email in emails_split:
            cursor.execute(f"INSERT INTO emails (email) VALUES('{email}')")
        connection.commit()
        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с POSTGRESQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
def verifyPassword(update: Update, context):
    password = update.message.text

    passwordRegex = re.compile(r"(?=.*[0-9])(?=.*[!@#$%^&*\(\)])(?=.*[a-z])(?=.*[A-Z])[0-9a-zA-Z!@#$%^&*\(\)]{8,}")

    if re.match(passwordRegex, password):
        update.message.reply_text("Пароль сложный")
        return ConversationHandler.END
    else:
        update.message.reply_text("Пароль легкий")
        return ConversationHandler.END

def verifyPasswordCommand(update: Update, context):
    update.message.reply_text("Введите пароль для проверки")
    return 'verifyPassword'


def connectToRemote():
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    return client



def get_repl_logs(update: Update, context):
    command = "cat /tmp/postgresql.log | tail -n 15"
    res = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0 or res.stderr.decode() != "":
        update.message.reply_text("Can not open log file!")
    else:
        update.message.reply_text(res.stdout.decode().strip('\n'))


def get_emails(update: Update, context):
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'),database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute("SELECT email FROM emails")
        data = cursor.fetchall()
        sum_data = ""
        for row in data:
            sum_data = sum_data + ''.join(row) + "\n"
        #sum_data.replace("(", "").replace(")", "")
        update.message.reply_text(sum_data)

        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с POSTGRESQL: %s", error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            return ConversationHandler.END


def get_phone_numbers(update: Update, context):
    try:
        connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'),database=os.getenv('DB_DATABASE'))
        cursor = connection.cursor()
        cursor.execute("SELECT phone FROM phones")
        data = cursor.fetchall()
        sum_data = ""
        for row in data:
            sum_data = sum_data + ''.join(row) + "\n"
        sum_data.replace("(", "").replace(")", "")
        update.message.reply_text(sum_data)

        logging.info("Команда успешно выполнена")
    except (Exception, Error) as error:
        logging.error("Ошибка при работе с POSTGRESQL: %s", error)
        update.message.reply_text(error)
    finally:
        if connection is not None:
            cursor.close()
            connection.close()
            return ConversationHandler.END

def connectToKali():
    host = os.getenv('RM_HOST')
    port = os.getenv('RM_PORT')
    username = os.getenv('RM_USER')
    password = os.getenv('RM_PASSWORD')

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(hostname=host, username=username, password=password, port=port)
    return client


def get_release(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('uname -r')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_uname(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('uname -r')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_release(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('uname -r')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_uptime(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('uptime -p')
    data = stdout.read() + stderr.read()
    client.close()
    data = str(data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]
    update.message.reply_text(data)
    return ConversationHandler.END

def get_df(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('df')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_free(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('free')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_mpstat(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('mpstat')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_w(update: Update, context):
    client = connectToRemote()
    print("Поехали")
    stdin, stdout, stderr = client.exec_command('w')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_auths(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('last | head')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_critical(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('journalctl --system -p info | tail -n 5')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_ps(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('ps | head')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_ss(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('ss | head')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_apt_list(update: Update, context):
    client = connectToRemote()
    stdin, stdout, stderr = client.exec_command('apt list | head')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END

def get_services(update: Update, context):
    client = connectToRemote()
    passwd = os.getenv('RM_PASSWORD')
    stdin, stdout, stderr = client.exec_command(f'echo {passwd} | sudo -S service --status-all | head')
    data = stdout.read() + stderr.read()
    client.close()
    decoded_data = data.decode('utf-8')
    decoded_data = str(decoded_data).replace('\\n', '\n').replace('\\t', '\t')[2:-1]

    update.message.reply_text(decoded_data)
    return ConversationHandler.END
def helpCommand(update: Update, context):
    help_text = "Этот бот повторяет твои сообщения. Также имеет команды:\n" \
                "/findPhoneNumbers\n" \
                "/findEmailAddress\n" \
                "/verify_password\n" \
                "/get_w\n" \
                "/get_release\n" \
                "/get_uptime\n" \
                "/get_df\n" \
                "/get_free\n" \
                "/get_mpstat\n" \
                "/get_auths\n" \
                "/get_critical\n" \
                "/get_ps\n" \
                "/get_ss\n" \
                "/get_apt_list\n" \
                "/get_services\n" \
                "/get_repl_logs\n" \
                "/get_emails\n" \
                "/get_phone_numbers"
    update.message.reply_text(help_text)
    return ConversationHandler.END


def test(update: Update, context):
    connection = psycopg2.connect(user=os.getenv('DB_USER'), password=os.getenv('DB_PASSWORD'), host=os.getenv('DB_HOST'), port=os.getenv('DB_PORT'), database=os.getenv('DB_DATABASE'))
    cursor = connection.cursor()
    update.message.reply_text("Подключено")
    cursor.close()
    connection.close()
def main():


    dp = updater.dispatcher

    convHandlerFindNumbers = ConversationHandler(
        entry_points=[CommandHandler('findPhoneNumbers', findPhoneNumbersCommand)],
        states={
            'findPhoneNumbers': [MessageHandler(Filters.text & ~Filters.command, findPhoneNumbers)],
            'save_phones': [MessageHandler(Filters.text & ~Filters.command, save_phones)]
        },
        fallbacks=[]
    )

    convHandlerEmailAddress = ConversationHandler(
        entry_points=[CommandHandler('findEmailAddress', findEmailAddressCommand)],
        states={
            'findEmailAddress': [MessageHandler(Filters.text & ~Filters.command, findEmailAddress)],
            'save_emails': [MessageHandler(Filters.text & ~Filters.command, save_emails)]
        },
        fallbacks=[]
    )

    convHandlerVerifyPassword = ConversationHandler(
        entry_points=[CommandHandler('verify_password', verifyPasswordCommand)],
        states={
            'verifyPassword': [MessageHandler(Filters.text & ~Filters.command, verifyPassword)],
        },
        fallbacks=[]
    )

    getWHander = CommandHandler('get_w', get_w)
    dp.add_handler(getWHander)
    get_releaseHander = CommandHandler('get_release', get_release)
    dp.add_handler(get_releaseHander)
    get_uptimeHander = CommandHandler('get_uptime', get_uptime)
    dp.add_handler(get_uptimeHander)
    get_dfHander = CommandHandler('get_df', get_df)
    dp.add_handler(get_dfHander)
    get_freeHander = CommandHandler('get_free', get_free)
    dp.add_handler(get_freeHander)
    get_mpstatHander = CommandHandler('get_mpstat', get_mpstat)
    dp.add_handler(get_mpstatHander)
    get_authsHander = CommandHandler('get_auths', get_auths)
    dp.add_handler(get_authsHander)
    get_criticalHander = CommandHandler('get_critical', get_critical)
    dp.add_handler(get_criticalHander)
    get_psHander = CommandHandler('get_ps', get_ps)
    dp.add_handler(get_psHander)
    get_ssHander = CommandHandler('get_ss', get_ss)
    dp.add_handler(get_ssHander)
    get_apt_listHander = CommandHandler('get_apt_list', get_apt_list)
    dp.add_handler(get_apt_listHander)
    get_servicesHander = CommandHandler('get_services', get_services)
    dp.add_handler(get_servicesHander)

    get_repl_logsHandler = CommandHandler('get_repl_logs', get_repl_logs)
    dp.add_handler(get_repl_logsHandler)
    get_emailsHandler = CommandHandler('get_emails', get_emails)
    dp.add_handler(get_emailsHandler)
    get_phone_numbersHandler = CommandHandler('get_phone_numbers', get_phone_numbers)
    dp.add_handler(get_phone_numbersHandler)

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", helpCommand))

    get_test = CommandHandler('get_test', test)
    dp.add_handler(get_test)

    dp.add_handler(convHandlerFindNumbers)
    dp.add_handler(convHandlerEmailAddress)
    dp.add_handler(convHandlerVerifyPassword)
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, echo))

    updater.start_polling()

    updater.idle()

if __name__ == '__main__':
    main()
