#импорт библиотек
import sqlite3
from sqlite3 import Error

#функция для подключения к базе данных
def create_connection(path):
    connection = None
    try:
        connection = sqlite3.connect("bd.sqlite", check_same_thread=False)
        print("Подключение к базе данных успешно!")
    except Error as e:
        print(f"Ошибка при подключении к базе данных: '{e}'")

    return connection

#сохранение подключения к базе в переменную
connection = create_connection("bd.sqlite")

#запрос в БД с одной переменной
def execute_query_one_component(query, component):
    cursor = connection.cursor()
    try:
        if component == "None":               
            result = cursor.execute(query)
            result = cursor.fetchall()
            connection.commit()
        else:                 
            result = cursor.execute(query,(component,))
            result = cursor.fetchall()
            connection.commit()
        return result
    except Error as e:
        print(f"Ошибка при запросе с одним компонентом: '{e}'. Компонент: " + str(component))

#запрос в БД с двумя переменными
def execute_query_two_component(query, firstComp, secondComp):
    cursor = connection.cursor()
    try:            
        result = cursor.execute(query, (firstComp, secondComp))
        result = cursor.fetchall()
        connection.commit()
        return result
    except Error as e:
        print(f"Ошибка при обращении с двумя компонентами: '{e}'")


#создание таблиц
create_ref_table = """CREATE TABLE IF NOT EXISTS users (
  userid INTEGER,
  refid INTEGER,
  balance INTEGER,
  countPartners INTEGER,
  daysSinceJoin INTEGER,
  wasReward INTEGER,
  existSubscribe INTEGER);"""
execute_query_one_component(create_ref_table,"None")   

create_days_table = """CREATE TABLE IF NOT EXISTS dates (
   currentDay INTEGER);"""
execute_query_one_component(create_days_table,"None") 

create_channel_table = """CREATE TABLE IF NOT EXISTS channelData (
    linkForSubscribe TEXT,
    channelID TEXT);"""
execute_query_one_component(create_channel_table,"None") 

#функция для вставки обязательных данных в таблицу
def insertData():
    existChannelData = execute_query_one_component("SELECT EXISTS(SELECT * FROM channelData)", "None")[0][0]
    if existChannelData == 0:
        execute_query_one_component("INSERT INTO channelData(linkForSubscribe, channelID) VALUES ('https://t.me/+i0lz0wvgG5RmMGRk', '-1000000')", "None")

    existCurrentDate = execute_query_one_component("SELECT EXISTS(SELECT * FROM dates)", "None")[0][0]
    if existCurrentDate == 0:
        execute_query_one_component("INSERT INTO dates(currentDay) VALUES (0)", "None")

#вызов самой функции
insertData()

