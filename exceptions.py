class SendMessageError(Exception):
    """Ошибка отправки сообщения"""
    pass


class GetAPIAnswerError(Exception):
    """Ошибка получения данных через API"""
    pass


class CheckResponseReturnNotList(Exception):
    """Функция возвращает не тип данных list"""
    pass


class CheckResponseError(Exception):
    """Ошибка в функции check_response"""
    pass


class HomeworkNameNotExist(KeyError):
    """Отсутствует название работы"""
    pass


class HomeworkStatusNotExist(KeyError):
    """Отсутствует статус работы"""
    pass


class UnknownStatus(Exception):
    """Получен неизвестный статус работы"""
    pass


class TokenError(Exception):
    """Ошибка с получением данных для аутентификации"""
    pass


class ApplicationBotError(Exception):
    """Ошибка приложения в main()"""
    pass
