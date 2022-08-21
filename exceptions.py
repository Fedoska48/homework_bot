class ResponseCodeError(Exception):
    """Ошибка ответа"""
    pass


class EmptyResponseFromAPI(Exception):
    """Пустой ответ от API"""
    pass


class NotForReply(Exception):
    """Сообщение не для пересылки"""
    pass


class HomeworkStatusNotExist(KeyError):
    """Отсутствует статус работы"""
    pass


class TokenError(Exception):
    """Ошибка с получением данных для аутентификации"""
    pass
