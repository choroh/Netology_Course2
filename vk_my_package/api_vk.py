from random import randrange
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType

with open('config_vk.txt', 'r', encoding='UTF-8') as f:
    token = f.readline().strip()

vk = vk_api.VkApi(token=token)  # Создаем сессию
longpoll = VkLongPoll(vk)


def write_msg(user_id, messages, attachments=''):
    vk.method('messages.send', {'user_id': user_id, 'message': messages,  'random_id': randrange(10 ** 7),'attachment': attachments})


def dialog():
    # Слушаем longpoll
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW:
        #  Если появилсь новое сообщение
            if event.to_me:  # Чтобы наш бот не слышал и не отвечал на самого себя
                request = event.text.lower()
                user_id = event.user_id  # получили id отправителя
                user_message = (user_id, request)
                return user_message
