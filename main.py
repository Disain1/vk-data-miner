import vk_api
import webbrowser
import re
import pickle
import os

from datetime import datetime
from progress.bar import PixelBar
from progress.spinner import PixelSpinner
from time import sleep
from colorama import Fore

def captcha_handler(captcha):
    webbrowser.open_new(captcha.get_url())
    key = input("Введите капчу: ")
    return captcha.try_again(key)

def sort_data(res):
	return sorted(res, key=lambda x: res.get(x))[-1]

def search(res):
	users = vk.method(
		method='users.get',
		values={'user_ids': res, 'fields':'city, bdate, schools'}
	)

	citys = {}
	bdates = {}
	schools = {}

	bar = PixelBar('Поиск...', max = len(users))

	for user in users:
		bar.next()
		sleep(0.01)

		if 'city' in user.keys():
			city = user['city']['title']
			
			if city in citys.keys(): citys[city] += 1
			else: citys[city] = 1

		if 'bdate' in user.keys():
			bdate = user['bdate'].split('.')
			
			if len(bdate) == 3:
				if bdate[2] in bdates.keys(): bdates[bdate[2]] += 1
				else: bdates[bdate[2]] = 1

		if 'schools' in user.keys() and user['schools'] != []:
			schools_list = user['schools']

			for school in schools_list:
				if school['name'] in schools.keys(): schools[school['name']] += 1
				else: schools[school['name']] = 1

	bar.finish()
	return citys, bdates, schools

def getScreenName(hint):
	link = input(hint)
	screen_name = link.split('/')[-1]
	return screen_name

def resolveScreenName(screen_name):
	user_id = vk.method( # id пользователя
		method='utils.resolveScreenName',
		values={'screen_name':screen_name}
	)['object_id']

	return user_id

def getFriends(user_ids):
	result = vk.method(method='friends.get', values={'user_id':user_ids}) # получаем друзей
	return result

def getUsers(user_ids):
	result = vk.method(
		method='users.get',
		values={'user_ids': user_ids, 'fields': 'domain'}
	)
	return result

def resolveList(list):
	return str(list).replace('[', '').replace(']', '')

vk = ...

if not os.path.exists('session'):
	print("Авторизируйтесь в ВК, для этого скопируйте ссылку в открывшимся окне.")
	webbrowser.open_new(
		"https://oauth.vk.com/authorize?"
		"client_id=7590779&"
		"display=page&"
		"redirect_uri=https://oauth.vk.com/blank.html&scope=friends,status&"
		"response_type=token&v=5.122"
	)
	auth_link = input("Ссылка: ")
        
	try:
		access_token = re.search(r"access_token=(\w+)", auth_link).group(0).split('=')[1] # получаем access token

		with open('session', 'wb') as file: # записываем access token в файл session
			pickle.dump(access_token, file)
	except Exception as e:
		print(f'Возникла ошибка: {e}, возможно вы ввели недействительную ссылку.')
		exit(0)
	
	print("\n") # отступ

if not os.path.exists('friends'): # создаем папку friends, если ее еще нет
	os.mkdir('friends')

with open('session', 'rb') as file: # записываем access token из файла session
	vk = vk_api.VkApi(
		token="a8b6d35ba8b6d35ba8b6d35b3ca8c50020aa8b6a8b6d35bf7e13245b6cbbc9c270ee2b5",
		captcha_handler=captcha_handler
	)

print(Fore.YELLOW + "VK DATA MINER" + Fore.RESET)
print("1. Информация о пользователе")
print("2. Мониторинг друзей")
print("3. Нахождение дружеских связей")
print("4. Завершить сессию")
menu = input('> ')

if menu == '1':
	screen_name = getScreenName('\nСсылка: ')
	result = getFriends(resolveScreenName(screen_name))

	user_ids = resolveList(result['items']) # получаем список друзей/подписчиков (без '[' и ']' для вк запроса)
	search_result = search(user_ids) # выполняем поиск информации

	print(Fore.YELLOW + "\nИнформация о пользователе" + Fore.RESET)
	city = sort_data(search_result[0])
	print(f'Город: {city}')

	year = int(datetime.now().year)
	bdate = int(sort_data(search_result[1]))
	age = year - bdate
	print(f'Возраст: {age} лет ({bdate} г.р.)')

	school = sort_data(search_result[2])
	print(f'Школа: {school}')
	
elif menu == '2':
	screen_name = getScreenName('\nСсылка: ')
	result = getFriends(resolveScreenName(screen_name))

	if not os.path.exists(f'friends/{screen_name}'):
		with open(f'friends/{screen_name}', 'wb') as file:
			pickle.dump(result['items'], file)
			print(f"Друзья для {screen_name} были сохранены")
	else:
		new_friends = []
		old_friends = []

		bar = PixelBar('Поиск...', max = len(result['items']))
		with open(f'friends/{screen_name}', 'rb') as file:
			dump = pickle.load(file)

			for friend in result['items']:
				sleep(0.01)
				bar.next()
				if not friend in dump:
					new_friends.append(friend)
					
			for friend in dump:
				if not friend in result['items']:
					old_friends.append(friend)

			bar.finish()
		
		if new_friends == []:
			print(f'Нет новых друзей для {screen_name}')
		else:
			print(Fore.YELLOW + '\nНовые друзья:' + Fore.RESET)
			new_friends = resolveList(new_friends)
			users = getUsers(new_friends)
			
			for user in users:
				print('- {0} {1} (https://vk.com/{2})'.format(user['first_name'], user['last_name'], user['domain']))
		
		if old_friends == []:
			print(f'Нет удаленных друзей для {screen_name}')
		else:
			print(Fore.YELLOW + '\nУдаленные (или скрытые) друзья:' + Fore.RESET)
			old_friends = resolveList(old_friends)
			users = getUsers(old_friends)

			for user in users:
				print('- {0} {1} (https://vk.com/{2})'.format(user['first_name'], user['last_name'], user['domain']))

elif menu == '3':
	pass
		
elif menu == '4':
	os.remove('session')
	print(Fore.RED + 'Сессия завершена, перезапустите программу!' + Fore.RESET)
	exit(0)
