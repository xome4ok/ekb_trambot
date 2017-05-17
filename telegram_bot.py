#!/usr/bin/env python3

import sys
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardRemove, ParseMode
import logging
import ettu

global transport

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

INFO = '''<i>Трамваи и троллейбусы Екатеринбурга.</i>
Отправьте местоположение во вложении, чтобы увидеть, какой транспорт подъезжает сейчас к ближайшим остановкам.

Данные сайта <a href="http://m.ettu.ru">m.ettu.ru</a>
'''


def start(bot, update):
    user = update.message.from_user
    logger.info("User {} started the conversation.".format(user))
    update.message.reply_text(INFO, parse_mode=ParseMode.HTML)


def help(bot, update):
    update.message.reply_text(INFO, parse_mode=ParseMode.HTML)


def map_approx_common(bot, update, lat, lon):
    global transport
    logger.info("user {} sent coord: {},{}".format(update.message.from_user, lon, lat))
    nearest3 = list(map(transport.get_info, transport.find_nearest(lat, lon, 3)))
    logger.info(nearest3)
    update.message.reply_text(
        '\n---\n'.join(
            map(
                lambda x: "{} ({})\n{}".format(
                    *x[:-1],
                    '\n'.join(map(lambda y: '<b>{:10}</b>{:10}{:10}'.format(*y), x[-1])) if x[-1] else 'нет транспорта'
                ),
                nearest3
            )
        ),
        parse_mode=ParseMode.HTML
    )


def map_approx_location(bot, update):
    map_approx_common(bot, update, update.message.location.latitude, update.message.location.longitude)


def map_approx_text(bot, update):
    map_approx_common(bot, update, *map(float, update.message.text.split(',')))


def error(bot, update, error):
    logger.warning('Update "{}" caused error "{}"'.format(update, error))


def cancel(bot, update):
    logger.info("User {} canceled the conversation.".format(update.message.from_user))
    update.message.reply_text('Счастливого пути!', reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


def main(argv):
    logger.info("Starting...")

    global transport
    transport = ettu.Ettu(logger)

    updater = Updater(argv[1])
    dp = updater.dispatcher

    handlers = (
        CommandHandler('start', start),
        CommandHandler('cancel', cancel),
        CommandHandler('help', help),
        MessageHandler(Filters.location, map_approx_location),
        MessageHandler(Filters.text, map_approx_text)
    )
    for handler in handlers:
        dp.add_handler(handler)
    dp.add_error_handler(error)

    logger.info("Started.")

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main(sys.argv)
