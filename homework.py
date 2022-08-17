import logging
import os
import time
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

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.INFO,
    filename='logs_bot.txt',
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)


def check_tokens():
    """Проверка токенов и переменных окружения"""
    return all([TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, PRACTICUM_TOKEN])


def send_message(bot, message):
    """Отправляет сообщение в TG чат, на основе переменной TELEGRAM_CHAT_ID.
    Принимает на вход два параметра: экземпляр класса Bot и текст сообщения."""
    try:
        chat_id = TELEGRAM_CHAT_ID
        bot.send_message(chat_id, message)
        logging.info('Сообщение успешное отправлено')
    except custom.SendMessageError as SendMessageError:
        print(SendMessageError)
        logging.error('Сообщение не отправлено!')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса и возвращает ответ."""
    try:
        timestamp: int = current_timestamp or int(time.time())
        params = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=params)
        if response.status_code != HTTPStatus.OK:
            raise f'Эндпойнт не отвечает: {response.status_code}'
        logging.info('Данные по API успешно получены')
        return response.json()
    except custom.GetAPIAnswerError as GetAPIAnswerError:
        print(GetAPIAnswerError)
        logging.error('Проблема с получением данных через API!')


def check_response(response):
    """Проверяет ответ API на корректность.
    Функция должна вернуть список домашних работ (он может быть и пустым)"""
    try:
        homework_list = response['homeworks']
        if (type(homework_list)) is not list:
            raise custom.CheckResponseReturnNotList(
                'Из check_response возвращается не список'
            )
        return homework_list
    except custom.CheckResponseError as CheckResponseError:
        print(CheckResponseError)
        logging.error('Проблема с обработкой данных в check_response!')


def parse_status(homework):
    """Извлекает инфу из конкретной работе, которая поступила на вход"""
    if 'homework_name' not in homework:
        raise custom.HomeworkNameNotExist('Отсутствует "homework_name"')
    if 'status' not in homework:
        raise custom.HomeworkStatusNotExist('Отсутствует "status"')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise custom.UnknownStatus('Получен неизвестный статус работы')
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        logging.critical('Все сломалось, токенов нет!')
        raise custom.TokenError('Проблема с получением токенов!')
        exit()
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            message = parse_status(homework)
            send_message(bot, message)
            current_timestamp = response.get('current_date', current_timestamp)
            time.sleep(RETRY_TIME)
        except custom.ApplicationBotError as ApplicationBotError:
            message = f'Сбой в работе программы: {ApplicationBotError}'
            logging.critical(message)
            time.sleep(RETRY_TIME)
        else:
            print('Game Over')
        return


if __name__ == '__main__':
    main()
