# -*- coding: utf-8 -*-
import requests
import json
import traceback
import urllib.parse
import os
import pickle
from sql import SQLighter

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium import webdriver
from selenium.webdriver.common.by import By 
from bs4 import BeautifulSoup as bs
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, executor, types
from time import sleep

bot = Bot(token='5595919153:AAEySTo0oltSx4-vFFwsXZ4giEotChyHy6k')
dp = Dispatcher(bot)


def create_driver(headless=True):
	print('create_driver()')
	chrome_options = webdriver.ChromeOptions()
	if headless:
		chrome_options.add_argument("--headless")
	chrome_options.add_argument("--log-level=3")
	chrome_options.add_argument("--start-maximized")
	chrome_options.add_argument('--no-sandbox')
	chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36')
	chrome_options.add_argument('--disable-blink-features=AutomationControlled')
	#chrome_options.add_argument('--proxy-server='+proxy)

	chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
	chrome_options.add_experimental_option('useAutomationExtension', False)
	chrome_options.add_argument("--disable-blink-features")
	chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.63 Safari/537.36")
	chrome_options.add_experimental_option("prefs", { 
	"profile.default_content_setting_values.media_stream_mic": 1, 
	"profile.default_content_setting_values.media_stream_camera": 1,
	"profile.default_content_setting_values.geolocation": 1, 
	"profile.default_content_setting_values.notifications": 1,
	"profile.default_content_settings.geolocation": 1,
	"profile.default_content_settings.popups": 0
  })
	
	caps = DesiredCapabilities().CHROME

	caps["pageLoadStrategy"] = "none"	
	
	driver = webdriver.Chrome(desired_capabilities=caps,chrome_options=chrome_options)	

	driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
 "source": """
	  const newProto = navigator.__proto__
	  delete newProto.webdriver
	  navigator.__proto__ = newProto		
	  """
})
	driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
	
	caps["pageLoadStrategy"] = "none"
	driver.implicitly_wait(30)

	#params = {
	#"latitude": 55.5815245,
	#"longitude": 36.825144,
	#"accuracy": 100
	#}
	#driver.execute_cdp_cmd("Emulation.setGeolocationOverride", params)
	#driver.refresh()
	
	return driver

#
#BASE_DIR = os.path.dirname(os.path.abspath(__file__))
#db_path = os.path.join(BASE_DIR, "db.db")

#db = SQLighter(db_path)

driver = create_driver()

@dp.message_handler()
async def answer(message):
	number = check_product(message.text)
	if number is None:
		answer_message = 'Товар на 25+ странице'
	elif 'реклама' in str(number):
		number = number.split(' ')[1]
		answer_message = 'Товар рекламный©,место '+number
	else:
		answer_message = 'Товар на '+str(number)+' месте'
	
	await message.answer(answer_message)

def get_products(chat_id):
	with open(f'products/products {chat_id}.json','r',encoding='utf-8-sig') as file:
		products = json.loads(file.read())

	return products

def save_products(products,chat_id):
	print('saving')
	with open(f'products/products {chat_id}.json','w',encoding='utf-8-sig') as file:
		file.write(json.dumps(products))


def check_if_product_selling(id_,exctra):
	search_url = f'https://card.wb.ru/cards/detail?spp=0&{exctra}pricemarginCoeff=1.0&appType=1&nm='+str(id_)
	print(search_url)
	data = get_page(search_url)['data']['products'][0]

	if 'wh' in data:
		return True

	return False

#@dp.message_handler()
def start_parse(chat_id):
	products = get_products(chat_id)
	send_message('Отчёт готовится,ожидайте',chat_id)
	count = 0
	text = ''

	for product in products:
		name = product['name'].split('/')[0]
		url = product['url']
		id_ = url.split('/?')[0].split('-')[-1]
		count += 1
		try:
			number = str(check_product(url))
			
			if number is None:
				answer_message = product['name']+' - товар в выдаче, на 25+ странице🔴'
			elif 'реклама' in number:
				number = number.split()[1]
				if product['place'] is None or not 'реклама' in product['place']:
					answer_message = product['name']+' - товар рекламный©,место '+number+' 🟢'
				else:
					diff = str(int(product['place'].split()[1])-int(number))
					end = '🟢' if int(diff) >= 0 else '🔴'
					diff = '+'+diff if int(diff) >= 0 else diff

					answer_message = product['name']+' - товар рекламный©,место '+number+'('+diff+') '+end
			
			elif 'нет' in number:
				answer_message = '<del>'+product['name']+'</del>'+' - товар отсутствует в выдаче 🔴'
			
			else:
				if not product['place'] or not product['place'].isnumeric():
					answer_message = product['name']+' - место '+number+' 🟢'
				else:
					diff = str(int(product['place'])-int(number))
					end = '🟢' if int(diff) >= 0 else '🔴'
					diff = '+'+diff if int(diff) >= 0 else diff

					answer_message = product['name']+' - место '+number+'('+diff+') '+end
		
			
			product['place'] = number
			save_products(products,chat_id)
		except:
			traceback.print_exc()
			answer_message = product['name']+' - произошла ошибка⚠️'

		text += str(count)+'. '+answer_message+'\n'

		text += '\n'
			
	send_message(text,chat_id)


def send_message(message,chat_id):
	telegram_api = 'https://api.telegram.org/bot5595919153:AAEySTo0oltSx4-vFFwsXZ4giEotChyHy6k/'
	chat_id = chat_id
	message = urllib.parse.quote_plus(message)
	keyboard = [['Получить отчёт'],['Добавить товар'],['Удалить товар']]
	keyboard = {'keyboard':keyboard,'resize_keyboard':False}
	
	url = telegram_api + 'sendMessage?chat_id='+chat_id+'&text='+message+'&parse_mode=html&reply_markup='+json.dumps(keyboard)
	
	requests.get(url)

def get_page(url):
	headers = get_headers()
	r = requests.get(url,headers=headers)
	test(r.text,'test.html')
	json_ = json.loads(r.text)
	sleep(1)
	
	return json_

def test(content,name):
	with open(name,'w',encoding='utf-8') as f:
		f.write(content)

def get_headers():
	with open('headers.txt','r',encoding='utf-8') as file:
		headers = file.read()
		headers = headers.splitlines()
		py_headers = {}
		for header in headers:
			key,value = header.split(': ')
			py_headers[key] = value

		return py_headers

def check_adv(query,id_):
	search_url = f'https://catalog-ads.wildberries.ru/api/v5/search?keyword={query}'
	print(search_url)
	data = get_page(search_url)['adverts']
	number = 1
	if data is None:
		return None
	
	for adv in data:
		print(int(adv['id']))
		if int(adv['id']) == int(id_):
			return number
		number += 1
	return None

def get_page_driver(url):
	print(url)
	while True:
		try:
			driver.get(url)
			break
		except:
			traceback.print_exc()
	sleep(0.2)
	load_cookie()
	sleep(1)

	data = driver.find_element(By.XPATH,"/html/body").text
	test(data,'test.html')
	#driver.delete_all_cookies()
	return json.loads(data)

def get_category(id_):
	search_url = 'https://www.ozon.ru/product/'+str(id_)
	driver.get(search_url)
	driver.find_element(By.XPATH,'//ol[@class="e5i"]')
	soup = bs(driver.page_source,'html.parser')

	category = soup.findAll('li',class_='e5i')

	if category == []:
		category = soup.findAll('li',class_='ie5')

	full_category = category
	category = category[-2].find('a')

	if not category:
		category = full_category[-1].find('a')

	return category.get('href')



def start_loop():
	print('Петля запущена')
	BASE_DIR = os.path.dirname(os.path.abspath(__file__))
	db_path = os.path.join(BASE_DIR, "db_ozon.db")

	db = SQLighter(db_path)
	
	while  True:
		sended_message = False
		while True:
		#	try:
		#		users = db.get_users()
		#		for user in users:
		#			if os.path.exists('products/products_competive '+user[0]+'.json'):
		#				check_competitor(user[0])
		#	except:
		#		traceback.print_exc()
			users = db.get_users()
			hour,minute = datetime.now().strftime("%H:%M").split(':')
			print(hour,'hour')
			if hour == '10' and not sended_message:
				for user in users:		
					start_parse(user[0])
				sended_message = True
			if hour == '11':
				break
			
			sleep(3)



def check_product(id_,last_page=26,region='',extra_params=''):
	number = 0
	add_number = 0
	id_ = id_.split('/?')[0].split('-')[-1]

	category = get_category(id_)
	
	next_page_str = ''
	
	for page in range(1,last_page):
		search_url = 'https://www.ozon.ru/api/composer-api.bx/page/json/v2?url='
		
		search_param = category+'?page='+str(page) if page == 1 else next_page_str.replace('layout_container=searchMegapagination&','')
		
		json_ = get_page_driver(search_url+search_param)
		 
		if page == 1:
			searchresult = 'searchResultsV2-252189-default-'
			next_page_param = json.loads(json_['widgetStates']['megaPaginator-252190-default-'+str(page)])
		else:
			searchresult = 'searchResultsV2-193750-categorySearchMegapagination-'
			next_page_param = json_

		
		items = json.loads(json_['widgetStates'][searchresult+str(page)])['items']
		
		if len(items) == 0:
			return None
		
		for item in items:
			item_id = item['action']['link'].split('/?')[0].split('-')[-1]
			print(item_id)
			if not 'backgroundColor' in item:
				number += 1
				result = number
			else:
				add_number += 1
				result = 'реклама '+str(add_number)

			if item_id == id_:
				return result

		next_page_str = next_page_param['nextPage']
	else:
		return None


def load_cookie(cookie='cookie'):
	with open(cookie, 'rb') as cookiesfile:
		cookies = pickle.load(cookiesfile)
		for cookie in cookies:
			driver.add_cookie(cookie)

	driver.refresh()
	return False


def save_cookie():
	driver.get('https://www.ozon.ru/')
	input()
	with open('cookie', 'wb') as filehandler:
		pickle.dump(driver.get_cookies(), filehandler)

if __name__ == '__main__':
	#start_parse('618939593')
	#start_loop()
	#send_message('~Товар~','618939593')
	#print(get_name('43475901'))
	executor.start_polling(dp,skip_updates=True)
	#save_cookie()
	#print(check_product('323066385'))