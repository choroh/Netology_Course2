import requests
import operator
import json

with open('files/config.txt', 'r', encoding='UTF-8') as f:
    my_token = f.readline().strip()
    photo_token = f.readline().strip()


#  Работа с VK
class VKUser:
    """
    Клас обработки данных пользователя VK
    """
    url = 'https://api.vk.com/method/'

    #  Авторизация на VK

    def __init__(self):
        # получаем токены от VK

        self.my_token = ''
        self.owner_id = ''
        # while self.my_token == '':
        # self.my_token = input('Введите токен VK: ').strip()
        self.my_token = my_token
        self.v = '5.131'
        self.params = {
            'access_token': self.my_token,
            'v': self.v
        }

    def cut_year(self, date_: str) -> int:
        """
        Функция получает дату в виде строки, если она есть, и год указан верно - выдает год в виде числа
        :param date_:
        :return:
        """
        self.date = date_
        if self.date and ('.' not in self.date[-4:]):
            return int(self.date[-4:])

    def swap_sex(self, sex_: int) -> int:
        """
        Функция возвращает инверсию пола
        :param sex_:
        :return:
        """
        self.sex = sex_
        out = {1: 2, 2: 1, 0: 0}
        return out.get(self.sex)


    def get_user(self, user_ids: int) -> list:
        """
        Функция получения данных по id, метод users.get, выдает в списке словарь со всеми данными
        :param user_ids: str
        :return: response [{}]
        """
        user_url = self.url + 'users.get'
        self.user_ids = user_ids
        self.user_params = {
            'user_ids': self.user_ids,
            'fields': 'bdate, sex, city, relation'
        }

        try:
            req = requests.get(user_url, params={**self.params, **self.user_params}).json()
        except Exception as error:
            return 'Убедитесь в верном токене, логине. {error}'
        if 'error' in req:
            print('Неверный логин')
        return req.get('response')

    def user_info(self, response_: list) -> dict:
        """
        функция получает из ответа нужные данные, возвращает в виде словаря
        :param response_: [{}]
        :return:
        """
        self.resp = response_
        self.city = ''

        self.name = self.resp[0].get('first_name')
        self.last_name = self.resp[0].get('last_name')
        self.bdate = self.resp[0].get('bdate')
        if self.resp[0].get('city'):
            self.city = self.resp[0].get('city').get('title')
        else:
            self.city = None
        self.relation = self.resp[0].get('relation', None)
        self.sex = self.resp[0].get('sex')

        if self.resp[0].get('deactivated'):
            # Для проверки блокировки пользователя
            self.deactivated = self.resp[0].get('deactivated')
        else:
            self.deactivated = None

        self.find_info = {'bdate': self.bdate, 'sex': self.sex, 'city': self.city, 'relation': self.relation,
            'deactivated': self.deactivated}
        return self.find_info

    def select_users(self, any_info_: list, find_params: list):
        """
        функция отфильторвывает из перебираемых учкстинков тех, кто подходит по данным пользователю.
         если страница заблокирована возвращается кортеж с id и причиной
        :param any_info_: данные перебираемых участников
        :param find_params: данные, которые необходимо искать для пользователя
        :return: list/ tuple
        relation:
            1 — не женат/не замужем;
            6 — в активном поиске
            0 — не указано
        """
        self.any_info = any_info_
        self.find_params = find_params

        if not self.any_info[0].get('deactivated'):
            # Если страница пользователя не заблокирована и не удалена
            self.age_any = self.cut_year(self.any_info[0].get('bdate'))  # год рождения кандидатов
            self.age_find = self.cut_year(self.find_params.get('bdate'))  # год рождения пользователя
            self.sex_find = self.swap_sex(self.find_params.get('sex'))  # пол пользователя
            if self.age_any:
                self.age_user = range(self.age_find - 3, self.age_find + 3)
                #  Если год рождения указан и верен, диаппазон для поиска +- 1 год от года пользователя
                self.city = self.any_info[0].get('city', None)
                if self.city:
                    self.city = self.city.get('title')
                    # Проверили, что город присутствует и получили его из 'title'

                    if ((int(self.age_any) in self.age_user)
                            and (self.any_info[0].get('sex') == self.sex_find)
                            and (self.city == self.find_params.get('city'))
                            and (self.any_info[0].get('relation') in (1, 6, 0))):
                        return self.any_info
        else:
            return (self.any_info[0].get('id'), self.any_info[0].get('deactivated'))

    def get_photos(self, user_id: int, numbers=30) -> list:
        """
        Функция получения списка фотографий с профиля, метод photos.get
        :param user_id: id пользователя
        :param numbers: ограничим число фотографий для выбора
        :return:
        """
        self.photo_url = self.url + 'photos.get'
        self.numbers = numbers
        self.user_id = user_id
        self.photo_params = {
            'access_token': photo_token,  # токен с правами получения фотографий
            'owner_id': user_id,
            'count': numbers,
            'album_id': 'profile',
            'photo_size': 1,
            'extended': 1  # расширренное чтобы отобразились лайки
        }
        req = requests.get(self.photo_url, params={**self.params, **self.photo_params}).json()
        if req.get('response').get('count') > 2:  # Если есть фото
            return req

    def photo_info(self, req: list) -> list:
        """
        Получение данных о фотографиях. Отбор фото с максимальным значением like+comment, фото с максимальным размером
        :param req:
        :return:
        """
        try:
            photos_all_list = req.get('response').get('items')
        except Exception as error:
            return 'Убедитесь в верном токене VK и id. {error}'

        all_my_photo = []
        likes_com_list = []  # Список значений лайков + комментариев
        size_list = []  # Список данных с максимальным фото

        #  Likes + comm
        for i in photos_all_list:
            # Составляем список значений лайк + комментарий
            likes = i.get('likes').get('count')
            comments = i.get('comments').get('count')
            likes_com = likes + comments

            likes_com_list.append(likes_com)

        likes_com_list.sort()
        likes_com_list = likes_com_list[-3:][::-1]
        #  Получили список 3 максимальных значений начиная с максимального

        for i in photos_all_list:
            #  photos_sizes словать коллекции фото с разлиными размерами текущего id
            photos_sizes = {}  # словарь данных по размерам
            photo_info = {}  # photo_info слоарь - данные по всем фотографиям сгруппированные по id.
            id_photo = i.get('id')

            sizes = i.get('sizes')
            likes = i.get('likes').get('count')
            comments = i.get('comments').get('count')
            likes_com = likes + comments

            likes_com_list.append(likes_com)
            # Собираем список значений лайк + комментарий

            for j in sizes:
                #  Получаем ссылки на фото с максимальных разрешением
                height = j.get('height')
                width = j.get('width')
                size = j.get('type')
                url_photo_collection = j.get('url')
                #  получаем разешение каждой фото из коллекции и их площадь
                resolution = f'{height} x {width}'
                #  площадь в ключе словаря используем для сортировки
                photos_sizes[height * width] = [resolution, url_photo_collection, size, likes_com]

            #  сортируем словарь с коллекцией фотографий по площади изображения, выбираем последнюю, как самую большую
            resolutions_list = sorted(photos_sizes.items(), key=operator.itemgetter(0))

            #  получаем максимальное разрешение и адрес
            url_resolution_collection_max = resolutions_list[len(resolutions_list) - 1][1]
            size_list.append(url_resolution_collection_max)

            url_max = url_resolution_collection_max[1]
            if likes_com >= likes_com_list[2]:
                # Выбираем фото с максимальным рарешением из отобранных максимальных значений like+ comm
                photo_info['url_max'] = url_max
                photo_info['likes_com'] = likes_com
                photo_info['id_photo'] = id_photo
                all_my_photo.append(photo_info)
        while len(all_my_photo) > 3:
            #  Если фото окажется более 3 лишние отбрасываем.
            del(all_my_photo)[0]
        return all_my_photo
