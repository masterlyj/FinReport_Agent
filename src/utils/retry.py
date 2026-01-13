"""
重试装饰器和错误处理工具模块
提供统一的重试机制、错误处理和日志记录
"""
import asyncio
import functools
import time
from typing import Callable, Optional, Tuple, Type, Union
from .logger import get_logger

logger = get_logger()


class RetryError(Exception):
    """重试失败后抛出的异常"""
    def __init__(self, message: str, last_exception: Optional[Exception] = None):
        super().__init__(message)
        self.last_exception = last_exception


def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
    logger_name: Optional[str] = None
):
    """
    同步函数重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避系数，每次重试延迟时间乘以此系数
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数，接收 (attempt, exception) 参数
        logger_name: 日志记录器名称

    Example:
        @retry(max_attempts=3, delay=1.0, backoff=2.0)
        def fetch_data():
            # 可能失败的操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            _logger = get_logger()
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        _logger.error(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后失败",
                            extra={"error": str(e), "function": func.__name__}
                        )
                        raise RetryError(
                            f"函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败",
                            last_exception=e
                        )

                    _logger.warning(
                        f"函数 {func.__name__} 第 {attempt}/{max_attempts} 次尝试失败: {str(e)}，"
                        f"{current_delay:.1f}秒后重试",
                        extra={"attempt": attempt, "max_attempts": max_attempts, "error": str(e)}
                    )

                    if on_retry:
                        try:
                            on_retry(attempt, e)
                        except Exception as callback_error:
                            _logger.error(f"重试回调函数执行失败: {callback_error}")

                    time.sleep(current_delay)
                    current_delay *= backoff

            raise RetryError(
                f"函数 {func.__name__} 执行失败",
                last_exception=last_exception
            )

        return wrapper
    return decorator


def async_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
    on_retry: Optional[Callable] = None,
    logger_name: Optional[str] = None
):
    """
    异步函数重试装饰器

    Args:
        max_attempts: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 退避系数，每次重试延迟时间乘以此系数
        exceptions: 需要重试的异常类型元组
        on_retry: 重试时的回调函数，接收 (attempt, exception) 参数
        logger_name: 日志记录器名称

    Example:
        @async_retry(max_attempts=3, delay=1.0, backoff=2.0)
        async def fetch_data():
            # 可能失败的异步操作
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            _logger = get_logger()
            last_exception = None
            current_delay = delay

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_attempts:
                        _logger.error(
                            f"异步函数 {func.__name__} 在 {max_attempts} 次尝试后失败",
                            extra={"error": str(e), "function": func.__name__}
                        )
                        raise RetryError(
                            f"异步函数 {func.__name__} 在 {max_attempts} 次尝试后仍然失败",
                            last_exception=e
                        )

                    _logger.warning(
                        f"异步函数 {func.__name__} 第 {attempt}/{max_attempts} 次尝试失败: {str(e)}，"
                        f"{current_delay:.1f}秒后重试",
                        extra={"attempt": attempt, "max_attempts": max_attempts, "error": str(e)}
                    )

                    if on_retry:
                        try:
                            if asyncio.iscoroutinefunction(on_retry):
                                await on_retry(attempt, e)
                            else:
                                on_retry(attempt, e)
                        except Exception as callback_error:
                            _logger.error(f"重试回调函数执行失败: {callback_error}")

                    await asyncio.sleep(current_delay)
                    current_delay *= backoff

            raise RetryError(
                f"异步函数 {func.__name__} 执行失败",
                last_exception=last_exception
            )

        return wrapper
    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return=None,
    log_error: bool = True,
    logger_name: Optional[str] = None,
    **kwargs
):
    """
    安全执行函数，捕获所有异常并返回默认值

    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 发生异常时的默认返回值
        log_error: 是否记录错误日志
        logger_name: 日志记录器名称
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果或默认值

    Example:
        result = safe_execute(risky_function, arg1, arg2, default_return=[])
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_error:
            _logger = get_logger()
            _logger.error(
                f"函数 {func.__name__} 执行失败: {str(e)}",
                extra={"error": str(e), "function": func.__name__}
            )
        return default_return


async def async_safe_execute(
    func: Callable,
    *args,
    default_return=None,
    log_error: bool = True,
    logger_name: Optional[str] = None,
    **kwargs
):
    """
    安全执行异步函数，捕获所有异常并返回默认值

    Args:
        func: 要执行的异步函数
        *args: 函数参数
        default_return: 发生异常时的默认值
        log_error: 是否记录错误日志
        logger_name: 日志记录器名称
        **kwargs: 函数关键字参数

    Returns:
        函数执行结果或默认值
    """
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        if log_error:
            _logger = get_logger()
            _logger.error(
                f"异步函数 {func.__name__} 执行失败: {str(e)}",
                extra={"error": str(e), "function": func.__name__}
            )
        return default_return
