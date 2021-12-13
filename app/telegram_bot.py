import telebot
from transitions import Machine
import os


class KvintBot(object):
	states = ['asleep', 'pizza_size_q', 'payment_type_q', 'confirmation']

	def __init__(self, name, instance):
		self.name = name
		self.bot = instance
		self.machine = Machine(model=self, states=KvintBot.states, initial='asleep')

		self.machine.add_transition(trigger='ask_pizza_size', source='*', dest='pizza_size_q', before='pizza_size_message')
		self.machine.add_transition(trigger='ask_payment_type', source='*', dest='payment_type_q', before='payment_type_message')
		self.machine.add_transition(trigger='confirm', source='*', dest='confirmation', before='confirm_message')
		self.machine.add_transition(trigger='sleep', source='*', dest='asleep')

	#Buttons with the response

	pizza_types = ['Большую', 'Маленькую']
	pizza_type_kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	for button in pizza_types:
		pizza_type_kb.add(button)

	payment_types = ['Картой', 'Наличными']
	payment_type_kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	for button in payment_types:
		payment_type_kb.add(button)

	confirm_kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
	confirm_kb.row('Да', 'Нет')

	#Messages

	def pizza_size_message(self, message):
		bot.send_message(message.chat.id, 'Какую пиццу вы хотите?', reply_markup=self.pizza_type_kb)

	def payment_type_message(self, message):
		ORDERS[message.chat.id]['pizza_size'] = message.text.lower()
		bot.send_message(message.chat.id, 'Как будете платить?', reply_markup=self.payment_type_kb)

	def confirm_message(self, message):
		payment_type = ORDERS[message.chat.id]['payment_type'] = message.text.lower()
		pizza_size = ORDERS[message.chat.id]['pizza_size']
		bot.send_message(message.chat.id, f'Вы хотите {pizza_size} пиццу, оплата {payment_type}?', reply_markup=self.confirm_kb)
	
	def unexpected_text_response(self, message):
		bot.send_message(message.chat.id, 'Не понял. Выберите один из вариантов!')

if __name__ == "__main__":
	ORDERS = {}

	bot = telebot.TeleBot(os.getenv('TELEBOT_TOKEN'))
	kvint = KvintBot('Kvint', bot)

	@bot.message_handler(content_types=['text'])
	def order(message):
		if ORDERS.get(message.chat.id) is None:
			kvint.ask_pizza_size(message)
			ORDERS[message.chat.id] = {}
			ORDERS[message.chat.id]['state'] = kvint.state
			return
		if (ORDERS[message.chat.id]['state'] == 'pizza_size_q') and (message.text in kvint.pizza_types):
			kvint.ask_payment_type(message)
			ORDERS[message.chat.id]['state'] = kvint.state
			return
		if (ORDERS[message.chat.id]['state'] == 'payment_type_q') and (message.text in kvint.payment_types):
			kvint.confirm(message)
			ORDERS[message.chat.id]['state'] = kvint.state
			return
		if (ORDERS[message.chat.id]['state'] == 'confirmation'):
			match message.text:
				case 'Да':
					bot.send_message(message.chat.id, 'Спасибо за заказ!', reply_markup=telebot.types.ReplyKeyboardRemove())
					kvint.sleep()
					ORDERS.pop(message.chat.id)
					return
				case 'Нет':
					bot.send_message(message.chat.id, 'Давайте еще раp!', reply_markup=telebot.types.ReplyKeyboardRemove())
					kvint.ask_pizza_size(message)
					ORDERS[message.chat.id]['state'] = kvint.state
					return
		if ORDERS[message.chat.id].get('state'):
			kvint.unexpected_text_response(message)

	bot.infinity_polling()