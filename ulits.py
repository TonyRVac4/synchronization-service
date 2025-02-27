from typing import Callable
from functools import wraps


def apply_decorator_for_all_methods(decorator: Callable, exclude: tuple[str] = ()) -> Callable:
    @wraps(decorator)
    def decorate(cls):
        for attr in dir(cls):
            if not attr.startswith("__") and not attr.startswith("_") and attr not in exclude:
                current_method = getattr(cls, attr)
                decorated_method = decorator(current_method)
                setattr(cls, attr, decorated_method)
        return cls
    return decorate


def logger_decorator(logger_for_method) -> Callable:
    def decorator(method: Callable) -> Callable:
        @wraps(method)
        def wrapper(self, *args, **kwargs):
            try:
                result: dict = method(self, *args, **kwargs)
            except Exception as exp:
                logger_for_method.exception(exp)
                raise
            else:
                if args:
                    if result["result"]:
                        logger_for_method.info(result['message'])
                    else:
                        logger_for_method.error(
                            f"{result['message']} | {result['status_code']}"
                        )

                return result
        return wrapper
    return decorator
