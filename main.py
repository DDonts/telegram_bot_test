import requests
from bs4 import BeautifulSoup

from telegram import Update
from telegram.ext import Updater, CallbackContext, CommandHandler, MessageHandler, Filters

from sqlalchemy import select

from settings import TOKEN
from database import City, Base, engine, session


updater = Updater(token=TOKEN, use_context=True)

dispatcher = updater.dispatcher


def start(update: Update, context: CallbackContext):
    message = "Бот активирован!"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def info(update: Update, context: CallbackContext):
    message = "Введите название городского населённого пункта Московской области, для получения информации о нём."
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def update_database(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text='Процесс обновления базы городов запущен')

    Base.metadata.create_all(engine)

    LINK = 'https://ru.wikipedia.org/wiki/%D0%93%D0%BE%D1%80%D0%BE%D0%B4%D1%81%D0%BA%D0%B8%D0%B5_%D0%BD%D0%B0%D1%81%D0%B5%D0%BB%D1%91%D0%BD%D0%BD%D1%8B%D0%B5_%D0%BF%D1%83%D0%BD%D0%BA%D1%82%D1%8B_%D0%9C%D0%BE%D1%81%D0%BA%D0%BE%D0%B2%D1%81%D0%BA%D0%BE%D0%B9_%D0%BE%D0%B1%D0%BB%D0%B0%D1%81%D1%82%D0%B8'

    page = requests.get(LINK).text

    soup = BeautifulSoup(page, 'html.parser')
    tables = soup.findAll('table')
    for table in tables:
        if table['class'] == ['standard', 'sortable']:
            for row in table.find_all('tr')[1:]:
                url = row.contents[1].contents[0]['href']
                name = row.contents[1].contents[0].text
                population = row.contents[4]['data-sort-value']

                city = City(name=name, url=url, population=population)
                if city.exists():
                    city.update_data()
                else:
                    city.add()

    context.bot.send_message(chat_id=update.effective_chat.id, text='База данных городов обновлена')


def city_search(update: Update, context: CallbackContext):
    message = update.message.text
    city_objects = session.execute(select(City).where(City.name.like(f"{message}%"))).scalars().all()
    if len(city_objects) > 1:
        response_message = 'Найдено несколько городов. Некоторые из них: \n'
        for city in city_objects[:5]:
            response_message += f'{city.name} \n'
        response_message += 'Введите название города, для подробной информации.'
    elif len(city_objects) == 1:
        city = city_objects[0]
        url = f'https://ru.wikipedia.org/{city.url}'
        response_message = f'<a href="{url}">{city.name}</a>. Численность населения: {city.population}'
    else:
        response_message = 'Нет совпадений по данному запросу'
    context.bot.send_message(chat_id=update.effective_chat.id, text=response_message, parse_mode='HTML')


start_handler = CommandHandler('start', start)
update_handler = CommandHandler('update', update_database)
info_handler = CommandHandler('help', info)
city_search_handler = MessageHandler(filters=Filters.text, callback=city_search)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(update_handler)
dispatcher.add_handler(info_handler)
dispatcher.add_handler(city_search_handler)

updater.start_polling()
updater.idle()

