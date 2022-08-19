import sqlite3

class SQLighter:

	def __init__(self,database_file):
		"""Подключаемся к БД и сохраняем курсор соединения"""
		self.connection = sqlite3.connect(database_file)
		self.execute = self.connection.cursor().execute

	def user_exists(self,chat_id):
		with self.connection:
			result = self.execute("SELECT * FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
			return bool(len(result))

	def get_status(self,chat_id):
		result = self.execute("SELECT `status` FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return result[0][0]

	def get_temp(self,chat_id):
		result = self.execute("SELECT `temp_product` FROM `user_condition` WHERE `chat_id` = ?",(chat_id,)).fetchall()
		
		return result[0][0]
	
	def get_users(self):
		users = self.execute("SELECT `chat_id` FROM `user_condition`").fetchall()
		
		return users 
	
	def add_user(self,chat_id):
		"""Добавляем пользователя в базу"""
		with self.connection:
			return self.execute("INSERT INTO `user_condition` (`chat_id`) VALUES (?)",(chat_id,))

	def update_status(self,chat_id,value):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `status` = ? WHERE `chat_id` = ?",(value,chat_id,))

	def update_temp(self,chat_id,value):
		"""Обновляем значение"""
		with self.connection:
			return self.execute("UPDATE `user_condition` SET `temp_product` = ? WHERE `chat_id` = ?",(value,chat_id,))

	def close(self):
		self.connection.close()