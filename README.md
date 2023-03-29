# Социальная сеть YaTube

В проекте реализованы следующие функции:

- добавление/удаление постов авторизованными пользователями
- редактирование постов только его автором
- возможность авторизованным пользователям оставлять комментарии к постам
- подписка/отписка на понравившихся авторов
- создание отдельной ленты с постами авторов, на которых подписан пользователь
- создание отдельной ленты постов по группам(тематикам)


Подключены пагинация, кеширование, авторизация пользователя, возможна смена пароля через почту.
Неавторизованному пользователю доступно только чтение.
Покрытие тестами.


# Запуск:
    Клонировать репозиторий:
        <git clone https://github.com/DevCatRain/hw05_final.git>
    
    перейти в него в командной строке:
        <cd api_yamdb>

    Cоздать и активировать виртуальное окружение:
        <python -m venv venv>
        <source venv/Scripts/activate>
    
    Обновить менеджер пакетов:
        <python -m pip install --upgrade pip>

    Установить зависимости из файла requirements.txt:
        <pip install -r requirements.txt>

    Выполнить миграции:
        <python manage.py migrate>

    Запустить проект:
        <python manage.py runserver>
