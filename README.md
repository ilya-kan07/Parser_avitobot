# Parser avito bot

## Описание

Данный бот находит объявления на сайте avito.ru по данным, введеным пользователем через телеграмм бота. В качестве результата работы отсылает файл в формате .xlsx с полученными данными.

# **Важно**
Для работы скрипта у вас должен быть установлен браузер Google Chrome любой более менее свежей версии.

## Установка

Склонируйте прокет 
```bash
  git clone https://github.com/ilya-kan07/parser_avitobot.git
```
Перейдите в директорию с проектом и создайте виртуальное окружение
```bash
  python -m venv venv 
```

Активируйте виртуальное окружение
```bash
  venv/scripts/activate
```

Установите зависимости из файла **requirements.txt**
```bash
  pip install -r requirements.txt
```
В файле *parser_cls.py* на строке 168 нужно поставить token вашего телеграмм бота
```
TOKEN = '6276819341:AAFWSydjrYMWG2yYKqKarSsF4TFp9e6YaZA'
```
Для старта работы запускаем файл *parser_cls.py*
```
python parser_cls.py
```
