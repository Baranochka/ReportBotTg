import os
import time
import pytz
import telebot
import calendar
import schedule
import datetime
import threading
import traceback
import database as db
import report_excel as rep
from telebot import types
from config import settings

TOKEN = settings.bot.admin_token   # Токен бота из @BotFather
bot = telebot.TeleBot(TOKEN)                                # Основной класс для синхронного бота
condition_users = {}                                        # Список состояний пользователя

# Функция логирования ошибок
def log_errors():
    def decorator(handler_func):
        def wrapper(message):
            try:
                return handler_func(message)
            except Exception as e:
                # with open('errors.log', 'a') as f:
                #     f.write(f"[{datetime.datetime.now()}] Ошибка в {handler_func.__name__}: {e}\n")
                with open('shared/errors.log', 'a', encoding='utf-8') as f:
                    f.write(f"{'='*120}\n")
                    f.write(f"[{datetime.datetime.now()}]\n")
                    f.write(f"{traceback.format_exc()}\n")
                    # f.write(f"{'='*60}\n")
                raise
        return wrapper
    return decorator


@bot.message_handler(commands=['start'])
@log_errors()
# Функция обработки сообщения /start
def send_welcome(message):
    if check_users(message.chat.id):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  
        btn1 = types.KeyboardButton("Скачать отчёт")
        btn2 = types.KeyboardButton("Список сотрудников")
        btn3 = types.KeyboardButton("Просмотреть информацию")
        btn4 = types.KeyboardButton("Удалить сотрудника")
        markup.add(btn1, btn2, btn3, btn4)
        bot.send_message(message.chat.id, 'Welcome to MalahitReportAdminBot!', reply_markup=markup)
        bot.send_message(message.chat.id, '/download - Скачать отчет со всеми сотрудниками\n/show - Показать список сотрудников\n/info - Просмотреть информацию по сотрудникам\n/delete - Удалить сотрудника\n/help - Показать список команд')
        condition_users[message.chat.id] = None
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return
        
@bot.message_handler(commands=['help'])
@log_errors()
# Функция обработки сообщения /help
def command_help(message):
    if check_users(message.chat.id):
        bot.send_message(message.chat.id, '/download - Скачать отчет со всеми сотрудниками\n/show - Показать список сотрудников\n/info - Просмотреть информацию по сотрудникам\n/delete - Удалить сотрудника\n/help - Показать список команд')
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return        
        
        
@bot.message_handler(commands=['delete'])
@log_errors()
# Функция обработки сообщения /delete
def command_delete(message):
    if check_users(message.chat.id):
        condition_users[message.chat.id] = 'delete'
        bot.send_message(message.chat.id, 'Введите Фамилию Имя')
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return
    
@bot.message_handler(commands=['download'])
@log_errors()
# Функция обработки сообщения /download
def command_download(message):
    if check_users(message.chat.id):
        download_file(message)
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return

@bot.message_handler(commands=['show'])
@log_errors()
# Функция обработки сообщения /show
def command_show(message):
    if check_users(message.chat.id):
        show_users(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return

@bot.message_handler(commands=['info'])
@log_errors()
# Функция обработки сообщения /info
def command_info(message):
    if check_users(message.chat.id):
        show_info(message.chat.id)
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return

@bot.message_handler(func=lambda message: True)
@log_errors()
# Функция обработки сообщения 
def answer(message):
    if check_users(message.chat.id):
        if message.text == "Скачать отчёт":
            download_file(message)
        elif message.text == "Список сотрудников":
            show_users(message.chat.id)
        elif message.text == "Удалить сотрудника":
            condition_users[message.chat.id] = 'delete'
            bot.send_message(message.chat.id, 'Введите Фамилию Имя')
        elif message.text == "Просмотреть информацию":
            show_info(message.chat.id)
        elif condition_users[message.chat.id] == 'delete':
            user = db.select("users", "chat_id", "user_name", (message.text,))
            if user != []:
                db.delete("users", "chat_id", (user[0][0],))
                for i in range(1,6):
                    db.delete(f"week_{i}", "chat_id", (user[0][0],))
                user = db.select("users", "chat_id", "user_name", (message.text,))
                if user == []:
                    bot.send_message(message.chat.id, f'Пользователь {message.text} удалён')
                else:
                    bot.send_message(message.chat.id, f'Пользователь {message.text} не удалён')
            else:
                bot.send_message(message.chat.id, f'Пользователь {message.text} не найден')
            condition_users[message.chat.id] = None
                       
    else:
        bot.send_message(message.chat.id, 'Access denied')
        return

# Функция получения номера недели и дня
def week_number_of_month():
    date_value = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")).date()
    current_week = date_value.isocalendar()[1]
    first_day_week = date_value.replace(day=1).isocalendar()[1]
    week_number = current_week - first_day_week + 1
    weekday_number = date_value.weekday() + 1
    return week_number, weekday_number

# Проверка является пользователь админом
def check_users(chat_id):
    user = db.select("admin", "user_name", "chat_id", (chat_id,))
    if user == []:
        return False
    else:
        return True

# Отправка сообщения с информацией о пользователях
def show_info(chat_id):
    rows = db.select_all("users")
    bot.send_message(chat_id, f'Информация:')
    for us in rows:
        bot.send_message(chat_id, text =(f"""Пользователь: <b><i>{us[1]}</i></b>
Дата последнего заполнения: <b><i>{datetime.datetime.fromisoformat(us[2]).strftime("%d-%m-%Y %H:%M")}</i></b>
Номер недели заполнения: <b><i>{us[3]}</i></b>
Номер дня заполнения: <b><i>{us[4]}</i></b>
Дата дня заполнения: <b><i>{us[5]}</i></b>
Статус заполнения: <b><i>{"Заполнен" if us[6] else "Не заполнен"}</i></b>"""), parse_mode='HTML')

# Отправка сообщения со списком пользователей
def show_users(chat_id):
    user = db.select_all("users")
    for i , us in enumerate(user):
        bot.send_message(chat_id, f'{i+1}. {us[1]}')
    return user

# Отправка сообщения с файлом отчёта
def download_file(message):
    file = rep.ReportExcel()
    doc = open(f"shared/{file.name_file}", 'rb')
    bot.send_document(message.chat.id, doc)
    doc.close()
    if os.path.exists(f"shared/{file.name_file}"):   
        os.remove(f"shared/{file.name_file}")        
        print("Файл удалён")
    else:
        print("Файл не найден")

# Отправка сообщения с файлом отчёта 1 числа каждого месяца
def download_file_update(chat_id):
    file = rep.ReportExcel()
    doc = open(f"shared/{file.name_file}", 'rb')
    bot.send_document(chat_id, doc)
    doc.close()

# Обновление базы данных 1 числа каждого месяца
def update_db():
    today = datetime.date.today()
    if today.day == 1: 
        data = db.select_all("users")
        print(data)
        users_admin = db.select_all("admin")
        print(users_admin)
        for us in users_admin:
            download_file_update(us[0])
        for i in range(1,6):
            db.delete_without_where(f"week_{i}")
            for user in data: 
                db.insert(f"week_{i}", "chat_id, user_name", "?,?", (user[0], user[1]))
        db.delete("list_date", "cid", ("1",))
        db.insert("list_date", "cid", "?", ("1"))
        now = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg"))
        days_in_month = calendar.monthrange(now.year, now.month)[1] 
        index_week, index_day = week_number_of_month()
        for i in range(0,days_in_month):
            date = (datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")) + datetime.timedelta(days=i)).strftime("%d.%m.%Y")
            db.update("list_date", f"date_{index_week}_{index_day} = ?", "cid", (date, "1"))
            if index_day == 7:
                index_day = 1
                index_week += 1
            else :
                index_day += 1

# Функция планировщика
def schedule_checker():
    schedule.every().day.at("17:58","Asia/Yekaterinburg").do(update_db)
    while True:
        schedule.run_pending()
        time.sleep(1)

# Запуск планировщика в отдельном потоке
threading.Thread(target=schedule_checker, daemon=True).start()
# Бесконечный цикл поллинга с обработкой исключений
bot.infinity_polling()
