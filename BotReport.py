import pytz
import telebot
import schedule
import datetime
import threading
import traceback
import database as db
from telebot import types
from config import settings

TOKEN = settings.bot.token    # Токен бота из @BotFather
bot = telebot.TeleBot(TOKEN)                                # Основной класс для синхронного бота
condition_users = {}                                        # Список состояний пользователя
cond_users_comm = {}                                        # Список состояний пользователя при написании комментариев
MAX_NUM_ELEM = 12                                           # Максимальное значение елементов 
name_sql_values = [ 'val_orig_calls',       #0 Исходные звонки
                    'posting_mailing',      #1 Расклейка, рассылка, раскидка
                    'meetings',             #2 Встречи
                    'stories_post',         #3 Сторис,пост
                    'agent_doc',            #4 Агентский договор
                    'deposit_booking',      #5 Задаток/Бронь
                    'closed_deals',         #6 Закрытые сделки
                    'termination_ad',       #7 Расторжение АД
                    'incoming_call',        #8 Входящий по объекту
                    'showing_sale',         #9 Показ (продажа)
                    'showing_selection',    #10 Показ (подбор)
                    'report_owner'          #11 Отчёт собственнику
                    ]
name_report_indicator = [   'Исходные звонки', 
                            'Расклейка, рассылка, раскидка', 
                            'Встречи',
                            'Сторис,пост', 
                            'Агентский договор',
                            'Задаток/Бронь',
                            'Закрытые сделки', 
                            'Расторжение АД',
                            'Входящий по объекту', 
                            'Показ (продажа)', 
                            'Показ (подбор)',
                            'Отчёт собственнику' 
                            ]

markup = types.InlineKeyboardMarkup()
btn = types.InlineKeyboardButton("Начать", callback_data="btn_click")
markup.add(btn)

markup_btn_comment = types.InlineKeyboardMarkup() 
btn1 = types.InlineKeyboardButton("Да", callback_data="btn_yes")
btn2 = types.InlineKeyboardButton("Нет", callback_data="btn_not")
markup_btn_comment.row(btn1, btn2)

# Функция логирования ошибок
def log_errors():
    def decorator(handler_func):
        def wrapper(message):
            try:
                return handler_func(message)
            except Exception as e:
                # Логируем ошибку
                # with open('errors.log', 'a') as f:
                #     f.write(f"[{datetime.datetime.now()}] Ошибка в {handler_func.__name__}: {e}\n")
                with open('shared/errors.log', 'a', encoding='utf-8') as f:
                    f.write(f"{'='*120}\n")
                    f.write(f"[{datetime.datetime.now()}]\n")
                    f.write(f"{traceback.format_exc()}\n")
                    # f.write(f"{'='*60}\n")
                # Пересылаем ошибку дальше
                raise
        return wrapper
    return decorator


@bot.message_handler(commands=['start'])
@log_errors()
# Функция обработки сообщения /start
def send_welcome(message):
    if check_users(message.chat.id) == False:
        bot.send_message(message.chat.id, 'Welcome to MalahitReportBot!')
        bot.send_message(message.chat.id, 'Введите фамилию и имя \nПример: Иванов Иван')
        condition_users[message.chat.id] = 'registation'
    else:
        bot.send_message(message.chat.id, "Вы уже были зарегистрированы! \nУведомление о создании отчёта будет приходить с пн-пт в 18:00")
        condition_users[message.chat.id] = None

@bot.message_handler(commands=['send'])
@log_errors()
# Функция обработки сообщения /send
def button_click(message):
    update_date_day_filling()
    send_daily_message()

@bot.message_handler(commands=['run'])
@log_errors()
# Функция обработки сообщения /run
def button_click(message):
    begin_filling_report(message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == "btn_click")
@log_errors()
# Функция обработки нажатия кнопки "Начать"
def button_click(call):
    begin_filling_report(call.message.chat.id)


@bot.callback_query_handler(func=lambda call: call.data == "btn_yes")
@log_errors()
# Функция обработки нажатия кнопки "Да"
def button_click_yes(call):
    bot.send_message(call.message.chat.id, "Комментарий:", parse_mode = "HTML")
    cond_users_comm[call.message.chat.id] = 'comment'


@bot.callback_query_handler(func=lambda call: call.data == "btn_not")
@log_errors()
# Функция обработки нажатия кнопки "Нет"
def button_click_not(call):
    if condition_users.get(call.message.chat.id) != None and condition_users.get(call.message.chat.id) >= 0 and condition_users.get(call.message.chat.id) < MAX_NUM_ELEM - 1:
        bot.send_message(call.message.chat.id, f"Введите значение для показателя отчёта <b><i>{name_report_indicator[condition_users.get(call.message.chat.id)+1]}</i></b>:", parse_mode = "HTML")
        cond_users_comm[call.message.chat.id] = 'number'
        condition_users[call.message.chat.id] +=1
    elif condition_users.get(call.message.chat.id) != None and condition_users.get(call.message.chat.id) == MAX_NUM_ELEM - 1:
        condition_users[call.message.chat.id] = None
        cond_users_comm[call.message.chat.id] = None
        update_datetime_last_filling(call.message.chat.id)
        bot.send_message(call.message.chat.id, "Молодец! Отчёт отправлен!")  
        bot.send_message(call.message.chat.id, "Чтобы заполнить отчёт заново, введите /run или нажмите Начать", reply_markup=markup)      
    
@bot.message_handler(regexp="^[0-9]+$")
@log_errors()
# Функция обработки сообщения состоящее из чисел
def input_value(message):
    if cond_users_comm.get(message.chat.id) == 'choose_btn' :
        bot.send_message(message.chat.id, "Пожалуйста, выберите кнопку Да или Нет!\nВы хотите оставить комментарий?", reply_markup=markup_btn_comment)
    elif condition_users.get(message.chat.id) != None and condition_users.get(message.chat.id) >= 0 and condition_users.get(message.chat.id) < MAX_NUM_ELEM:
        
        index_week, index_day = week_number_of_month()
        
        d = db.select("users", "num_week_filling, num_day_filling, num_date_filling", "chat_id", (message.chat.id,))[0]
    
        index_week = d[0]
        index_day = d[1]
        index_date = d[2]
        db.update(f"week_{index_week}",f"{name_sql_values[condition_users.get(message.chat.id)]}_{index_day} = ?", "chat_id", (message.text, message.chat.id))
        
        cond_users_comm[message.chat.id] = 'choose_btn'
        bot.send_message(message.chat.id, "Вы хотите оставить комментарий?", reply_markup=markup_btn_comment)
    elif condition_users.get(message.chat.id) == None :
        bot.send_message(message.chat.id, "Для начала заполнения отчёта введите /run или нажмите Начать", reply_markup=markup)
        
@bot.message_handler(func=lambda message: True)
@log_errors()
# Функция обработки сообщения состоящее из слов
def write_comment(message):
    if condition_users.get(message.chat.id) == 'registation':
        user = db.select("users", "user_name", "chat_id", (message.chat.id,))
        if user == []:
            index_week, index_day = week_number_of_month()
            index_date = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")).strftime("%d.%m.%Y")
            db.insert("users", "chat_id, user_name, num_week_filling, num_day_filling, num_date_filling", "?, ?, ?, ?, ?", (message.chat.id, message.text, index_week, index_day, index_date))
            for i in range(1,6):
                db.insert(f"week_{i}", "chat_id, user_name", "?, ?", (message.chat.id, message.text))
            bot.send_message(message.chat.id, "Вы зарегистрированы! \nУведомление о создании отчёта будет приходить с пн-пт в 18:00", reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "Вы уже были зарегистрированы! \nУведомление о создании отчёта будет приходить с пн-пт в 18:00")
        condition_users[message.chat.id] = None
        return
    elif condition_users.get(message.chat.id) == None :
        bot.send_message(message.chat.id, "Для начала заполнения отчёта введите /run или нажмите Начать", reply_markup=markup)
    elif condition_users.get(message.chat.id) != None and cond_users_comm.get(message.chat.id) == 'comment' and  condition_users.get(message.chat.id) >= 0 and condition_users.get(message.chat.id) < MAX_NUM_ELEM - 1:
        d = db.select("users", "num_week_filling, num_day_filling", "chat_id", (message.chat.id,))[0]
        index_week = d[0]
        index_day = d[1]
        db.update(f"week_{index_week}", f"{name_sql_values[condition_users.get(message.chat.id)]}_comm_{index_day} = ?", "chat_id", (message.text, message.chat.id))
        bot.send_message(message.chat.id, f"Введите значение для показателя отчёта <b><i>{name_report_indicator[condition_users.get(message.chat.id)+1]}</i></b>:", parse_mode = "HTML")
        cond_users_comm[message.chat.id] = 'number'
        condition_users[message.chat.id] += 1
    elif condition_users.get(message.chat.id) != None and cond_users_comm.get(message.chat.id) == 'comment' and  condition_users.get(message.chat.id) == MAX_NUM_ELEM - 1:
        d = db.select("users", "num_week_filling, num_day_filling", "chat_id", (message.chat.id,))[0]
        index_week = d[0]
        index_day = d[1]
        db.update(f"week_{index_week}", f"{name_sql_values[condition_users.get(message.chat.id)]}_comm_{index_day} = ?", "chat_id", (message.text, message.chat.id))
        update_datetime_last_filling(message.chat.id)
        bot.send_message(message.chat.id, "Молодец! Отчёт отправлен!")
        bot.send_message(message.chat.id, "Чтобы заполнить отчёт заново, введите /run или нажмите Начать", reply_markup=markup)
        cond_users_comm[message.chat.id] = None
        condition_users[message.chat.id] = None
    elif cond_users_comm.get(message.chat.id) == 'choose_btn' :
        bot.send_message(message.chat.id, "Пожалуйста, выберите кнопку Да или Нет!\nВы хотите оставить комментарий?", reply_markup=markup_btn_comment)
    elif cond_users_comm.get(message.chat.id) == 'number':
        bot.send_message(message.chat.id, "Пожалуйста, введите числовое значение для показателя отчёта!")

# Функция начала заполнения отчёта
def begin_filling_report(chat_id):
    if check_users(chat_id):
        bot.send_message(chat_id, "Введите значение для показателя отчёта <b><i>Исходные звонки</i></b>:", parse_mode = "HTML")
        cond_users_comm[chat_id] = 'number'
        condition_users[chat_id] = 0
    else:
        bot.send_message(chat_id, "Зарегистрируйтесь!")
        bot.send_message(chat_id, "Для начала регистрации введите /start")
        condition_users[chat_id] = None

    

# Обновление даты и времени последнего заполнения
def update_datetime_last_filling(chat_id):
    date_time_now = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")).isoformat()
    db.update("users", "last_filling_date = ?, condition_filling = ?", "chat_id", (date_time_now, True, chat_id))

# Проверка наличия пользователя в базе    
def check_users(chat_id):
    user = db.select("users", "user_name", "chat_id", (chat_id,))
    if user == []:
        return False
    else:
        return True

# Функция получения номера недели и дня 
def week_number_of_month():
    date_value = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")).date()
    current_week = date_value.isocalendar()[1]
    first_day_week = date_value.replace(day=1).isocalendar()[1] 
    week_number = current_week - first_day_week + 1 
    weekday_number = date_value.weekday() + 1
    return week_number, weekday_number


# Функция для рассылки ежедневного сообщения
def send_daily_message():
    index_week, index_day = week_number_of_month()
    if index_day not in [6,7]:
        time = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")).strftime("%H:%M")
        users = db.select_without_where("users", "chat_id, condition_filling") 
        for id in users:
            print(id)
            if time == "18:00":
                bot.send_message(id[0], "Добрый вечер! Время добавить отчёт ☺", reply_markup=markup)
            elif time == "19:00" and id[1] == False:
                bot.send_message(id[0], "Добрый вечер! Время добавить отчёт ☺", reply_markup=markup)
            elif time == "20:00" and id[1] == False:
                bot.send_message(id[0], "Добрый вечер! Время добавить отчёт ☺", reply_markup=markup)
            elif time == "21:00" and id[1] == False:
                bot.send_message(id[0], "Добрый вечер! Время добавить отчёт ☺", reply_markup=markup)
            elif time == "22:00" and id[1] == False:
                bot.send_message(id[0], "Добрый вечер! Время добавить отчёт ☺", reply_markup=markup)
            elif time == "23:00" and id[1] == False:
                bot.send_message(id[0], "Добрый вечер! Время добавить отчёт ☺", reply_markup=markup)

    
# Обновление номеров недели и дня для всех пользователей в базе данных
def update_date_day_filling():
    index_week, index_day = week_number_of_month()
    if index_day not in [6,7]:
        users = db.select_without_where("users", "chat_id")
        index_date = datetime.datetime.now(pytz.timezone("Asia/Yekaterinburg")).strftime("%d.%m.%Y")
        for id in users: 
            db.update("users", "num_week_filling = ?, num_day_filling = ?, num_date_filling = ?, condition_filling = ?", "chat_id", (index_week, index_day, index_date, False, id[0]))    
            
# Планировщик задач
def schedule_checker():
    schedule.every().day.at("17:59","Asia/Yekaterinburg").do(update_date_day_filling)
    schedule.every().day.at("18:00","Asia/Yekaterinburg").do(send_daily_message)
    schedule.every().day.at("19:00","Asia/Yekaterinburg").do(send_daily_message)
    schedule.every().day.at("20:00","Asia/Yekaterinburg").do(send_daily_message)
    schedule.every().day.at("21:00","Asia/Yekaterinburg").do(send_daily_message)
    schedule.every().day.at("22:00","Asia/Yekaterinburg").do(send_daily_message)
    schedule.every().day.at("23:00","Asia/Yekaterinburg").do(send_daily_message)
    
    while True:
        schedule.run_pending()

# Запуск планировщика в отдельном потоке
threading.Thread(target=schedule_checker, daemon=True).start()
# Бесконечный цикл поллинга с обработкой исключений
bot.infinity_polling()
