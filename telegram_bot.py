#!/usr/bin/env python3

import sys # python-telegram-bot==5.3.1
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, ConversationHandler, RegexHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode
import requests
import logging
import ettu

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
transport = ettu.Ettu(logger)
INFO = "hello"

def start(bot, update):
    user = update.message.from_user
    logger.info("User {} started the conversation.".format(user))
    update.message.reply_text(INFO)


def help(bot, update):
    update.message.reply_text(INFO)


def map_approx(bot, update):
    lon, lat = update.message.location.longitude, update.message.location.latitude
    logger.info("user sent coord: {},{}".format(lon,lat))
    nearest3 = list(map(transport.get_info, transport.find_nearest(lat, lon, 3)))
    update.message.reply_text('--'.join(nearest3))


def error(bot, update, error):
    logger.warn('Update "{}" caused error "{}"'.format(update, error))


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User {} canceled the conversation.".format(user))
    update.message.reply_text('Bye!', reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END


def main(argv):
    logger.info("Starting...")
    updater = Updater(argv[1])

    dp = updater.dispatcher

    start_handler = CommandHandler('start', start)
    cancel_handler = CommandHandler('cancel', cancel)
    map_handler = MessageHandler(Filters.location, map_approx)

    dp.add_handler(start_handler)
    dp.add_handler(cancel_handler)
    dp.add_handler(map_handler)
    dp.add_error_handler(error)
    logger.info("Started.")
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main(sys.argv)
