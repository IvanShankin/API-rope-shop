from src.modules.base.exception import ServiceException

class HandlerFileException(ServiceException):
    """Базовое исключение для работы с файлами."""
    pass

class InvalidImageFormat(HandlerFileException):
    """Исключение при неподдерживаемом или неверном формате изображения."""
    pass

class FileTooLarge(HandlerFileException):
    """Исключение при превышении допустимого размера файла."""
    pass

class ImageConversionError(HandlerFileException):
    """Исключение при ошибке конвертации изображения."""
    pass

class ImageCompressionError(HandlerFileException):
    """Исключение при ошибке сжатия изображения."""
    pass
