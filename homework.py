import logging
import os
import sys
import time

from telegram import TelegramError

import exceptions as custom

import requests
import telegram
from dotenv import load_dotenv
from http import HTTPStatus

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

BASEDIR = os.path.dirname('')

VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='logs_bot.log',
    format='%(asctime)s - %(funcName)s - %(lineno)s - '
           '%(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout),
        logging.FileHandler(
            filename=BASEDIR + 'logs_bot.log',
            encoding='UTF-8'
        )
    ]
)


def check_tokens():
    """Проверка токенов и переменных окружения."""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def send_message(bot, message):
    """Отправляет сообщение в TG чат."""
    try:
        logging.info('Начата отправка сообщения в телеграмм')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError as error:
        logging.error(f'Сообщение не отправлено! {error}')
    else:
        logging.info('Сообщение успешное отправлено')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса и возвращает ответ."""
    timestamp: int = current_timestamp
    params = {'from_date': timestamp}
    pargs = {
        'url': ENDPOINT,
        'headers': HEADERS,
        'params': params
    }
    logging.info(('Начался запрос к API. {url}, {headers}, {params}.')
                 .format(**pargs))
    try:
        response = requests.get(**pargs)
        if response.status_code != HTTPStatus.OK:
            raise custom.ResponseCodeError(
                f'Эндпойнт не отвечает:{response.status_code}, '
                f'{response.text}, {response.reason} '
            )
        logging.info('Данные по API успешно получены')
        return response.json()
    except Exception as error:
        raise ConnectionError(('При запросе к эндпойнту произошла ошибка:'
                               '{error}: {url}, {headers}, {params}.')
                              .format(**pargs))


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.info('Началась проверка API на корректность')
    if not isinstance(response, dict):
        raise TypeError('Ошибка, response должен быть словарем')
    if 'homeworks' not in response:
        raise custom.EmptyResponseFromAPI('Пустой ответ от API')
    homework_list = response.get('homeworks')
    if not isinstance(homework_list, list):
        raise KeyError('Ошибка, homework_list должен быть списком')
    return homework_list


def parse_status(homework):
    """Извлекает инфу из конкретной работе, которая поступила на вход."""
    if 'homework_name' not in homework:
        raise KeyError('Отсутствует "homework_name"')
    if 'status' not in homework:
        raise KeyError('Отсутствует "status"')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status not in VERDICTS:
        raise ValueError('Получен неизвестный статус работы')
    return (
        'Изменился статус проверки работы "{homework_name}". {verdict}'
        .format(
            homework_name=homework_name,
            verdict=VERDICTS[homework_status]
        )
    )


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Все сломалось, токенов нет!')
        raise custom.TokenError('Проблема с получением токенов!')
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_report['message'] = ''
    prev_report = {}

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            homework = homework[0]
            if len(homework) != 0:
                message = parse_status(homework)
            else:
                current_report['message'] = 'Новых домашек нет'
            if current_report != prev_report:
                send_message(bot, message)
                prev_report = current_report.copy()
                current_timestamp = response.get(
                    'current_date',
                    current_timestamp
                )
            else:
                logging.info('Нет обновления статуса')
        except custom.EmptyResponseFromAPI as error:
            logging.error(f'{error}. Пустой ответ от API.')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            current_report['message'] = ''
            prev_report = {}
            if current_report != prev_report:
                logging.exception(f'Отправка сообщения о {error}')
                send_message(bot, message)
                prev_report = current_report.copy()
                current_timestamp = response.get(
                    'current_date',
                    current_timestamp
                )
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
