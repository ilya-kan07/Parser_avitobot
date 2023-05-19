import os
import subprocess
import time
from random import choice
import pandas as pd

import undetected_chromedriver as uc
# from notifiers.logging import NotificationHandler
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.window import WindowTypes
from loguru import logger
from locator import LocatorAvito

info = []

class AvitoParse:
     
    def __init__(self,
                 url: str,
                 keysword_list: str,
                 count: int = 1,
                 tg_token: str = None,
                 max_price: int = 0,
                 min_price: int = 0
                 ):
        self.url = url
        self.keys_word = keysword_list
        self.count = count
        self.data = []
        self.tg_token = tg_token
        self.max_price = int(max_price)
        self.min_price = int(min_price)

    def __set_up(self):
        options = Options()
        options.add_argument('--headless')
        _ua = choice(list(map(str.rstrip, open("user_agent_pc.txt").readlines())))
        options.add_argument(f'--user-agent={_ua}')
        self.driver = uc.Chrome(version_main=self.__get_chrome_version, options=options)

    @property
    def __get_chrome_version(self):
        """Определяет версию chrome в зависимости от платформы"""
        if os.name == 'nt':
            import winreg
            # открываем ключ реестра, содержащий информацию о Google Chrome
            reg_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
            # считываем значение ключа "version"
            version = winreg.QueryValueEx(reg_key, "version")[0]
            return version.split(".")[0]
        else:
            output = subprocess.check_output(['google-chrome', '--version'])
            try:
                version = output.decode('utf-8').split()[-1]
                version = version.split(".")[0]
                return version
            except Exception as error:
                logger.error(error)
                logger.info("У Вас не установлен Chrome, либо он требует обновления")
                raise Exception("Chrome Exception")

    def __get_url(self):
        self.driver.get(self.url)

    def __paginator(self):
        while self.count > 0:
            self.__parse_page()
            """Проверяем есть ли кнопка далее"""
            if self.driver.find_elements(*LocatorAvito.NEXT_BTN):
                self.driver.find_element(*LocatorAvito.NEXT_BTN).click()
                self.count -= 1
            else:
                logger.info("Нет кнопки дальше")
                break

    # @logger.catch
    def __parse_page(self):
        """Парсит открытую страницу"""
        
        titles = self.driver.find_elements(*LocatorAvito.TITLES)
        for title in titles:
            name = title.find_element(*LocatorAvito.NAME).text
            description = title.find_element(*LocatorAvito.DESCRIPTIONS).text
            url = title.find_element(*LocatorAvito.URL).get_attribute("href")
            price = title.find_element(*LocatorAvito.PRICE).get_attribute("content")

            data = {
                'name': name,
                'description': description,
                'url': url,
                'price': price
            }
            """Определяем нужно ли нам учитывать ключевые слова"""
            if (self.keys_word.lower() in name.lower()) and self.min_price <= int(price) <= self.max_price:
                logger.success(name)
                self.data.append(self.__parse_full_page(url, data))
                self.__save_data(data=data)
            else:
                continue


    def __parse_full_page(self, url: str, data: dict) -> dict:
        """Парсит для доп. информации открытое объявление на отдельной вкладке"""
        self.driver.switch_to.new_window(WindowTypes.TAB)  # новая вкладка
        self.driver.get(url)
        self.driver.switch_to.window(self.driver.window_handles[1])

        """Количество просмотров"""
        if self.driver.find_elements(*LocatorAvito.TOTAL_VIEWS):
            total_views = self.driver.find_element(*LocatorAvito.TOTAL_VIEWS).text.split()[0]
            data["views"] = total_views

        """Дата публикации"""
        if self.driver.find_elements(*LocatorAvito.DATE_PUBLIC):
            date_public = self.driver.find_element(*LocatorAvito.DATE_PUBLIC).text
            if "· " in date_public:
                date_public = date_public.replace("· ", '')
            data["date_public"] = date_public

        """Имя продавца"""
        if self.driver.find_elements(*LocatorAvito.SELLER_NAME):
            seller_name = self.driver.find_element(*LocatorAvito.SELLER_NAME).text
            if seller_name == 'Компания' and self.driver.find_elements(*LocatorAvito.COMPANY_NAME):
                seller_name = self.driver.find_element(*LocatorAvito.COMPANY_NAME) \
                    .find_element(*LocatorAvito.COMPANY_NAME_TEXT).text
            data["seller_name"] = seller_name

        """Закрывает вкладку №2 и возвращается на №1"""
        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])
        return data

    def __save_data(self, data: dict):        
        global info
        info.append(data)
            
    def parse(self):
        """Метод для вызова"""
        try:
            self.__set_up()
            self.__get_url()
            self.__paginator()
        except Exception as error:
            logger.error(f"Ошибка: {error}")
        finally:
            self.driver.quit()


if __name__ == '__main__':

    from telebot import TeleBot, types


    TOKEN = '6276819341:AAFWSydjrYMWG2yYKqKarSsF4TFp9e6YaZA'
    bot = TeleBot(TOKEN)
    user_data = {}
    


    @bot.message_handler(commands=["start"])
    def send_welcome(message):
        bot.send_message(message.chat.id, f'Приветствую, {message.from_user.first_name} \U0001F44B')
        bot.send_message(message.chat.id, """Меня зовут Avito bot\U0001F680, с моей помощью ты можешь собирать необходимую информацию с сайта авито.\n\n\U0001F9FEПравила просты: от тебя потребуется некоторая информация о товаре, я в свою очередь, предоставлю все объявления которые смогу найти.""" ) 
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn = types.InlineKeyboardButton('Заполнить данные', callback_data='change')
        markup.add(btn)
        bot.send_message(message.chat.id, "Прежде всего нужно заполнить данные\U0001F4DD", reply_markup=markup)


    @bot.message_handler(commands=["change"])
    def put_data(message):
        bot.send_message(message.chat.id, "\U00002757Запущен процесс ввода данных")
        msg = bot.send_message(message.chat.id, "Введите название товара, который хотите найти")
        bot.register_next_step_handler(msg, get_name)
        
    def get_name(message):
        global user_data
        user_data['keys'] = message.text
        msg = bot.send_message(message.chat.id, "Введите количество страниц, которые необходимо спарсить")
        bot.register_next_step_handler(msg, get_num_ads)

    def get_num_ads(message):
        global user_data
        user_data['num_ads'] = message.text
        msg = bot.send_message(message.chat.id, "Введите максимальную цену товара")
        bot.register_next_step_handler(msg, get_max_price)
        
    def get_max_price(message):
        global user_data
        user_data['max_price'] = message.text
        msg = bot.send_message(message.chat.id, "Введите минимальную цену товара")
        bot.register_next_step_handler(msg, get_min_price)
        
    def get_min_price(message):
        global user_data
        user_data['min_price'] = message.text
        msg = bot.send_message(message.chat.id, "Ссылку страницы авито")
        bot.register_next_step_handler(msg, get_url)
        
    def get_url(message):
        global user_data
        user_data['url'] = message.text
        bot.send_message(message.chat.id, "\U00002714Отлично, данные успешно заполнены")
        bot.send_message(message.chat.id, f"\U0001F4CBВаши введенные данные:\n\n1. Название товара - {user_data['keys']}\n2. Кол-во страниц, которые необходимо спарсить - {user_data['num_ads']}\n3. Максимальная цена товара - {user_data['max_price']}\n4. Минимальная цена товара - {user_data['min_price']}\n5. Ссылка - {user_data['url']}")
        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton('Начать парсинг\U0001F680', callback_data='start')
        btn2 = types.InlineKeyboardButton('Перезаписать данные\U0001F501', callback_data='change')
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, "Теперь вы можете начать парсинг страницы или перезаписать данные", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call:True)
    def callback(call):
        global user_data
        if call.message:
            if call.data == 'start':
                bot.send_message(call.message.chat.id, "\U00002757Начинаю парсинг, пожалуйста подождите, это может занять некоторое время\U0000231B")
                
                url = user_data['url']
                num_ads = int(user_data["num_ads"])
                keys = user_data['keys']
                max_price = int(user_data['max_price'])
                min_price = int(user_data['min_price'])
                flag = True
                
                while flag:
                    try:
                        AvitoParse(
                            url=url,
                            count=int(num_ads),
                            keysword_list=keys,
                            max_price=int(max_price),
                            min_price=int(min_price)
                        ).parse()
                        bot.send_message(call.message.chat.id, "\U00002705Парсинг завершен. Вот файл с данными.")
                        
                        global info                        
                        df = pd.DataFrame.from_dict(info)
                        df.to_excel('result/text.xlsx')                        
                        bot.send_document(call.message.chat.id, open(f'result/text.xlsx', 'rb'))       
                        f = open('result/text.xlsx.', 'w')
                        f.close()
                        flag = False
                        logger.info('Конец')
                    except Exception as error:
                        logger.error(error)
                        logger.error('Произошла ошибка, но работа будет продолжена через 30 сек. '
                                    'Если ошибка повторится несколько раз - перезапустите скрипт.'
                                    'Если и это не поможет - обратитесь к разработчику')
                        time.sleep(30)
            elif call.data == 'change':
                put_data(message=call.message)
        
    bot.polling(none_stop=True, interval = 0)

