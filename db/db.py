import sqlalchemy
import psycopg2

user = 'finder'
password = 'socseti'

#  Создаем engine
db = f'postgresql://{user}:{password}@localhost:5432/vk_kandidat'
engine = sqlalchemy.create_engine(db)
try:
    connection = engine.connect()
#  Установили соединение с базой данных
except Exception as error:
    print('Ошибка при работе с PostgreSQL. Возможны повторения данных', {error})


def insert_user(user_id: int):
    """
    Функция записывает данные пользователя в таблицу пользователей
    :param user_id:
    :return:
    """
    connection.execute(f"INSERT INTO vk_users (user_id) VALUES({user_id})")


def insert_kandidat(owner_id: int, kandidat_info: dict):
    """
    Функция записывает кандидита в ткблицу кандидатов, получает первичные ключи из таблиц пользователя и кандидата,
    вносит промежуточную запись для связывания этих таблиц в таблицу vk_users_vk_kandidat
    :param owner_id:
    :param kandidat_info:
    :return:
    """
    info = f"""INSERT INTO vk_kandidat (kandidat_id, first_name, last_name, bdate, city, relation, url_account, url_photo1, url_photo2, 
    url_photo3, bloked) VALUES({kandidat_info.get('kandidat_id')}, '{kandidat_info.get('first_name')}', '{kandidat_info.get('last_name')}', 
    '{kandidat_info.get('bdate')}','{kandidat_info.get('city')}', '{kandidat_info.get('relation')}', '{kandidat_info.get('url_account')}', '{kandidat_info.get('url_photo1')}', 
    '{kandidat_info.get('url_photo2')}', '{kandidat_info.get('url_photo3')}', '{kandidat_info.get('bloked')}');"""
    connection.execute(info)
    id_user = connection.execute(f"""SELECT id from vk_users WHERE user_id = {owner_id}""").fetchone()
    id_kandidat = connection.execute(f"""SELECT id from vk_kandidat WHERE kandidat_id = {kandidat_info.get('kandidat_id')}""").fetchone()
    insert_vk_users_vk_kandidat(*id_user, *id_kandidat)


def insert_ban(any_id: int, bloked: str):
    """
    Функция записывает заблокированных кандидатов в таблицу кандидатов с отметкой блокировки
    :param any_id:
    :param bloked:
    :return:
    """
    connection.execute(f"""INSERT INTO vk_kandidat (kandidat_id, bloked) VALUES({any_id}, '{bloked}')""")


def insert_vk_users_vk_kandidat(id_user: int, id_kandidat: int):
    """
    Функция вносит промежуточную запись для связывания таблиц в таблицу vk_users_vk_kandidat
    :param id_user:
    :param id_kandidat:
    :return:
    """
    connection.execute(f"""INSERT INTO vk_users_vk_kandidat (id_user, id_kandidat) VALUES({id_user}, {id_kandidat})""")


def read_all(table_name: str, column: str) -> tuple:
    """
    Функция вспомогательная для отладки, чтение данных из таблицы
    :param table_name:
    :param column:
    :return:
    """
    return connection.execute(f"SELECT {column} FROM {table_name}").fetchall()


def get_kandidat_id_for_user_id(user_id, kandidat_id) -> tuple:
    """
    Функция проверяет на наличие записи кандидата для данного пользователя
    :param user_id:
    :param kandidat_id:
    :return:
    """
    sel = connection.execute(f"""SELECT kandidat_id FROM vk_kandidat
    JOIN vk_users_vk_kandidat ON vk_kandidat.id=vk_users_vk_kandidat.id_kandidat
    JOIN vk_users ON vk_users_vk_kandidat.id_user = vk_users.id
    WHERE (vk_users.user_id = {user_id}) AND (vk_kandidat.kandidat_id = {kandidat_id})""").fetchall()
    return(sel)


def if_user_inlist(user_id: int) -> tuple:
    """
    Проверка существовашия пользователя в таблице для избежания повторов его id vk
    :param user_id:
    :return:
    """
    sel = connection.execute(f"""SELECT user_id FROM vk_users WHERE user_id = {user_id}""").fetchall()
    return sel


def if_bloked(kandidat_id: int) -> tuple:
    """
    Проверяет содержимое поля bloked на заполение. Если непуст - значит акканут заблокирован
    :param user_id:
    :return:
    """
    con = connection.execute(f""" SELECT bloked FROM vk_kandidat WHERE kandidat_id = {kandidat_id} """).fetchone()
    return con


