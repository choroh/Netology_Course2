"""
Netology. Курсовая работа.
Используя данные из VK, нужно сделать сервис намного лучше, чем Tinder, а именно: чат-бота "VKinder".
Бот должен искать людей, подходящих под условия, на основании информации о пользователе из VK:

    возраст,
    пол,
    город,
    семейное положение.

У тех людей, которые подошли по требованиям пользователю, получать топ-3 популярных фотографии профиля и
отправлять их пользователю в чат вместе со ссылкой на найденного человека.
Популярность определяется по количеству лайков и комментариев.

Входные данные

Имя пользователя или его id в ВК, для которого мы ищем пару.

    если информации недостаточно нужно дополнительно спросить её у пользователя.

Требование к сервису:

    1. Код программы удовлетворяетPEP8.
    2. 0Получать токен от пользователя с нужными правами.
    3. Программа декомпозирована на функции/классы/модули/пакеты.
    4.Результат программы записывать в БД.
    5. Люди не должны повторяться при повторном поиске.
    6. Не запрещается использовать внешние библиотеки для vk.

01.11.21
"""

import json

import vk_my_package.vk_find_user_modul
import vk_my_package.api_vk
import db.db
import re

vk_client = vk_my_package.vk_find_user_modul.VKUser()
info_for_db = {}   # Словарь с данными для внесения в базу данных
list_info_for_db = []  # Список словарей с данными для записи в БД
dict_bloked = {}  # Словарь с заблоированными пользователями
list_bloked = []  # Список словарей с заблоированными пользователями

with open('files/config.txt', 'r', encoding='UTF-8') as f:
    my_token = f.readline().strip()


def decod_relation(code: int) -> str:
    """
    функция декодирует код семейного положения в семейное положение
    :param code:
    :return:
    """
    decoder = {1: 'не женат/не замужем', 2: ' есть друг/есть подруга', 3: 'помолвлен/помолвлена', 4: 'женат/замужем',
               5: 'всё сложно', 6: 'в активном поиске', 7: 'влюблён/влюблена', 8: 'в гражданском браке', 0: 'не указано'}
    return decoder.get(code)


def get_photo(i, owner_id: int) -> dict:
    """
    Функция получает список найденных кандидатов, id пользователя
    Заносит данные о кандидате в базу данных
    :param list_find:
    :param vk_client:
    :param owner_id:
    :return:
    """
    kandidat_id = i[0].get('id')
    first_name = i[0].get('first_name')
    last_name = i[0].get('last_name')
    bdate = i[0].get('bdate')
    city = i[0].get('city').get('title')
    relation = decod_relation(i[0].get('relation'))

    candidate = {'kandidat_id': kandidat_id, 'first_name': first_name, 'last_name': last_name, 'bdate': bdate,
                'city': city, 'relation': relation}

    if vk_client.get_photos(kandidat_id):  # Если получили id подходящего кандидата с фото
        account = 'https://vk.com/id' + str(kandidat_id)
        print()
        dict_photo = vk_client.get_photos(kandidat_id)
        list_photo = vk_client.photo_info(dict_photo)
        print()

        kandidat_info = {'url_account': account, 'url_photo1': list_photo[0].get('id_photo'),
                'url_photo2': list_photo[1].get('id_photo'), 'url_photo3': list_photo[2].get('id_photo')}

        kandidat_info_all = {**candidate, **kandidat_info}  # Объединили данные словарей
        info_for_db['owner_id'] = owner_id
        info_for_db['kandidat_info_all'] = kandidat_info_all
        temp = info_for_db.copy()  # Создаем временный словарь для передачи словарей в список
        list_info_for_db.append(temp)
        #  Занесли в словарь для записи в БД данные о пользователе и словарь с  данными кандидата
        return kandidat_info_all


def find_user(users_: list, owner_params_: list, owner_id_: int):
    """
    Функция полцчает диаппазон id пользователей для поиска пары, параметры пользователя для поиска, id пользователя
    Отфильтровывает заблокированных пользователей, аккаунты, уже находящиеся в базе данных с пометкой блокировки,
    кандидатов, которые для данного пользователя уже были ему показаны и внесены в базу данных,
    заносит найденных кандидатов для данного пользователя в базу данных и выдает их
    :param users:
    :param owner_params:
    :param owner_id:
    :return:
    """
    owner_params = owner_params_
    owner_id = owner_id_
    list_find = []
    users = users_
    error_conneceton = False
    dict_bloked = {}
    for i in users:
        any_info = vk_client.get_user(i)
        any_id = any_info[0].get('id')
        try:
            kandidat_id_for_user_id = db.db.get_kandidat_id_for_user_id(owner_id, any_id)
            bloked_user = db.db.if_bloked(any_id)
            if (not kandidat_id_for_user_id) and (not bloked_user):
                # Если текущего кандидата нет в списке просмотренных данным пользователем и в списке заблокированных
                if not any_info[0].get('deactivated'):
                    #  Если текущий кандидат не заблокирован и его нет в в списке заблокированных
                    find_users = vk_client.select_users(any_info, owner_params)
                    #  Поиск кандидата по параметрам
                    if find_users:
                        list_find.append(find_users)
                    print('.', end='')
                else:
                    #  В нести в список кандидатов с пометкой блокировки
                    dict_bloked['bloked_user'] = any_info[0].get('id')
                    # print(' dict_bloked',  dict_bloked)
                    dict_bloked['bloked_info'] = any_info[0].get('deactivated')
                    temp = dict_bloked.copy()  # Копируем словарь с заблокированными и добавляем в список
                    list_bloked.append(temp)

        except Exception as Error:
            error_conneceton = True
            if not any_info[0].get('deactivated'):
                #  Если текущий кандидат не заблокирован
                find_users = vk_client.select_users(any_info, owner_params)
                #  Поиск кандидата по параметрам
                if find_users:
                    list_find.append(find_users)
                print('.', end='')

    if error_conneceton:
        print('База данных временно недоступна. find_user, kandidat_id_for_user_id')
    print()
    #  Получаем ссылки на фотографии
    return list_find


def check_user_params(owner_id_:int, owner_params_:dict) -> dict:
    """
    Функция проверяет на наличие необходимых данных у пльзователя.
    Если не хватает - запрашивает и добавляте в словарь данных пользователя
    :param owner_id_:
    :param owner_params_:
    :return:
    """
    owner_params = owner_params_
    owner_id = owner_id_
    if not owner_params.get('city', None):  # Если не указан город
        vk_my_package.api_vk.write_msg(owner_id, 'Укажите ваш город')
        city = vk_my_package.api_vk.dialog()[1].title()
        owner_params['city'] = city

    if owner_params.get('sex') not in (1, 2):  # Если не указан пол
        message = """
        Укажите ваш пол
        женщина - 1
        мужчина - 2
        """
        vk_my_package.api_vk.write_msg(owner_id, message)
        sex = vk_my_package.api_vk.dialog()[1]
        owner_params[sex] = sex

    if not owner_params.get('bdate', None) or not re.findall('\d{1,2}.\d{1,2}.\d{4}', owner_params.get('bdate')):
        # Если не указан год или неверный формат
        vk_my_package.api_vk.write_msg(owner_id, 'Укажите ваш год рождения "дд.мм.гггг')
        bdate = vk_my_package.api_vk.dialog()[1]
        owner_params['bdate'] = bdate
    return owner_params

def send_message_to_user(i_, owner_id_, kandidat_):
    """
    Функция принимает словарь с данными пользователя, id пользователя
    Отеравляет пользователю результат поиска
    """
    i = i_
    owner_id = owner_id_
    kandidat = kandidat_
    if kandidat:  # Если найден кандидат подходящий по всем параметрам с фото
        vk_my_package.api_vk.write_msg(owner_id, 'Аккаунт кандидата: ')
        vk_my_package.api_vk.write_msg(owner_id,
                                       f"{i[0].get('first_name')} {i[0].get('last_name')} {kandidat.get('url_account')}")
        vk_my_package.api_vk.write_msg(owner_id, 'Фотография кандидата 1:',
                                       f"photo{kandidat.get('kandidat_id')}_{kandidat.get('url_photo1')}")
        vk_my_package.api_vk.write_msg(owner_id, 'Фотография кандидата 2:',
                                       f"photo{kandidat.get('kandidat_id')}_{kandidat.get('url_photo2')}")
        vk_my_package.api_vk.write_msg(owner_id, 'Фотография кандидата 3:',
                                       f"photo{kandidat.get('kandidat_id')}_{kandidat.get('url_photo3')}")
        vk_my_package.api_vk.write_msg(owner_id, '*' * 40)

    else:
        print('Записей удовлетворяющих запросу не обнаруеженно.')
        vk_my_package.api_vk.write_msg(owner_id, 'Записей удовлетворяющих запросу не обнаруеженно.')


def main():
    """
    При получении от пользователя группы сообщения "Поиск пары", из текста получаем id пользователя vk
    По его id получаем необходимые данные для выяснения требований поиска.
    Если у пользователя в аккаунте не достаточно данных - запрашиваем в сообщении.
    Сканируем пользователей vk, отбираем удовлетворяющих требованиям.
    Информация о найденных кандидатах для данного пользователя заносится в базу данных и отправляется пользователю в сообщении.
    :return:
    """
    # Диапазон id для сканирования сети
    users = (i for i in range(100_000_000, 100_000_200))

    user_message = vk_my_package.api_vk.dialog()
    owner_id = user_message[0]
    owner_message = user_message[1]
    kandidat_list_clear = False
    ban_list_clear = False

    while owner_message != 'поиск пары':  # Ждем от пользователя фразы поиска
        bot_message = 'Для поиска пары, напишите "поиск пары"'
        vk_my_package.api_vk.write_msg(owner_id, bot_message)
        user_message = vk_my_package.api_vk.dialog()
        owner_id = user_message[0]
        owner_message = user_message[1]

    owner_info = vk_client.get_user(owner_id)  # Получили в списке словарь с необходимыми данными пользователя
    #print('owner_info', owner_info)

    owner_params = vk_client.user_info(owner_info)  # Сформировали нужные данные

    #owner_params = {'bdate': '01.01.1988', 'sex': 2, 'city': 'Санкт-Петербург', 'relation': 1}
    # Тест. Подставляем шаблон пользователя для проверки
    print('owner_params', owner_params)
    #  Проверяем данные пользователя
    owner_params = check_user_params(owner_id, owner_params)

    print()
    vk_my_package.api_vk.write_msg(owner_id, 'Идет поиск кандидатов')
    list_find = find_user(users, owner_params, owner_id)

    #  Ищем кандидатов для данного пользователя
    if list_find:
        vk_my_package.api_vk.write_msg(owner_id, 'Подходящие кандидаты: ')
         #Отправляем результаты поиска пользователю в сообщении
        for i in list_find:
            kandidat = get_photo(i, owner_id)
            send_message_to_user(i, owner_id, kandidat)

    # Если нашли кандидата - заносим в БД
    if list_info_for_db:
        for i in list_info_for_db:
            owner_id = i.get('owner_id')
            #  Проверяем на наличие текущего id пользователя в БД. Если нет - заносим
            try:
                user_inlist = db.db.if_user_inlist(owner_id)
                if not user_inlist:
                    db.db.insert_user(owner_id)
            except Exception as Error:
                print('База данных временно недоступна. owner_id не внесен в БД', {Error})

            # if not i.get('deactivated'):
            #     # Если пользователь не заблокирован
            try:
                db.db.insert_kandidat(owner_id, i.get('kandidat_info_all'))  # Занесли в БД информацию о кандидате
                kandidat_list_clear = True
            except Exception as Error:
                print('База данных временно недоступна, возможны повторы', {Error})
                vk_my_package.api_vk.write_msg(owner_id, 'База данных временно недоступна, возможны повторы.')
    else:
        print('Записей удовлетворяющих запросу не обнаруеженно.')
        vk_my_package.api_vk.write_msg(owner_id, 'Записей удовлетворяющих запросу не обнаруеженно.')
    if list_bloked:
        for i in list_bloked:
            try:
                db.db.insert_ban(i.get('bloked_user'), i.get('bloked_info'))
                ban_list_clear = True
            except Exception as Error:
                print('База данных временно недоступна, невозможно внести данные о блокеровке пользователя', {Error})

    #  Если данные внесены в БД очищаем список для записи в БД
    if kandidat_list_clear:
        list_info_for_db.clear()
        kandidat_list_clear = False
    if ban_list_clear:
        list_bloked.clear()
        ban_list_clear = False

if __name__ == "__main__":
    main()