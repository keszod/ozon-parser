# -*- coding: utf-8 -*-
from sql import SQLighter
import requests
import json
import os
from threading import Thread
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import ReplyKeyboardRemove,ReplyKeyboardMarkup, KeyboardButton
from time import sleep

from parserozon import start_parse,start_loop

bot = Bot(token='5595919153:AAEySTo0oltSx4-vFFwsXZ4giEotChyHy6k')
dp = Dispatcher(bot)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "db_ozon.db")

db = SQLighter(db_path)

start_buttons = ReplyKeyboardMarkup().add(KeyboardButton('Получить отчёт')).add(KeyboardButton('Добавить товар')).add(KeyboardButton('Удалить товар'))
edit_search_keyboard = ReplyKeyboardMarkup().add(KeyboardButton('Добавить новый')).add(KeyboardButton('Главное меню'))

def get_products(chat_id):
	with open(f'products/products {chat_id}.json','r',encoding='utf-8-sig') as file:
		products = json.loads(file.read())

	return products

def save_products(products,chat_id):
	print('saving')
	with open(f'products/products {chat_id}.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(products))

@dp.message_handler()
async def answer(message):
	start_message = 'Приветствую,выберите действие ниже'
	chat_id = message.chat.id
	
	if not db.user_exists(str(chat_id)):
		db.add_user(str(chat_id))
		save_products([],chat_id)
		await message.answer(start_message,reply_markup=start_buttons)
	
	status = db.get_status(chat_id)
	text = message.text
	keyboard = ReplyKeyboardMarkup().add('Главное меню')
	answer = ''
	save = False
	parse = False

	if text == 'Главное меню' or text == '/start':
		if status != 'main':
			start_message = 'Выбор отменён,выберите действие'
		db.update_status(chat_id,'main')
		await message.answer(start_message,reply_markup=start_buttons)
		return
	
	products = get_products(chat_id)
	
	if status == 'main':
		if text == 'Получить отчёт':
			answer = ''
			keyboard = ReplyKeyboardMarkup()
			parse = True
		elif text == 'Добавить товар':
			db.update_status(chat_id,'add_product_url')
			answer = 'Пришлите ссылку на товар'
		elif text == 'Удалить товар':
			if len(products) > 0:
				list_text = ''
				for i in range(len(products)):
					list_text += str(i+1)+') '+products[i]['name']+'\n\n' 
				answer = f'Список товаров на отслеживание: \n\n{list_text}\n\n Отправьте порядоквый номер товара,который нужно удалить'
				db.update_status(chat_id,'delete_choose')
			else:
				answer = f'Товары отсуствуют'
				keyboard = start_buttons
				
	elif 'add_product' in status:
		if 'url' in status:
			try:
				id_ = text.split('/?')[0].split('-')[-1]
			except:
				id_ = ''

			if id_.isnumeric():
				db.update_status(chat_id,'add_product_name')
				answer = 'Введите название товара'
				db.update_temp(chat_id,text)
			else:
				db.update_status(chat_id,'main')
				answer = 'Ошибка добавления товара,неверный url'
				keyboard = start_buttons
		
		elif 'name' in status:
			url = db.get_temp(chat_id)
			name = text
			db.update_status(chat_id,'main')
			answer = f'Товар `{name}` добавлен,ожидайте отчёт'
			product = {'url':url,'name':name,'place':None}
			products.append(product)
			keyboard = start_buttons
			save = True

	elif 'delete' in status:
		keyboard = start_buttons
		db.update_status(chat_id,'main')
		if text.isnumeric() and int(text) <= len(products):
			del products[int(text)-1]
			answer = f'Товар {text} удалён'
			save = True
		else:
			answer = 'Такой номер отсуствует'
	
	if save:
		save_products(products,chat_id)

	if answer != '':
		await message.answer(answer,reply_markup=keyboard)

	if parse:
		start_parse(str(chat_id))

if __name__ == '__main__':
	Thread(target=start_loop,args=[]).start()
	executor.start_polling(dp,skip_updates=True)