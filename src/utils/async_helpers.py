# -*- coding: utf-8 -*-
"""Async helper utilities for running coroutines safely from sync contexts."""

import asyncio
import threading
from typing import TypeVar, Coroutine, Any

T = TypeVar('T')


def run_async_safely(coro: Coroutine[Any, Any, T]) -> T:
    """
    Run an async coroutine safely from a sync context.
    
    Creates a NEW event loop in a dedicated thread to avoid deadlocks
    when called from within an already-running event loop (e.g., inside
    asyncio.gather or other async contexts).
    
    Args:
        coro: The coroutine to execute.
        
    Returns:
        The result of the coroutine execution.
        
    Raises:
        Exception: Re-raises any exception from the coroutine.
        
    Example:
        >>> async def my_async_function(x):
        ...     return x * 2
        >>> result = run_async_safely(my_async_function(5))
        >>> print(result)  # 10
    """
    result_container: dict = {}
    exception_container: dict = {}
    
    def run_in_new_loop():
        # Create a brand new event loop for this thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        try:
            result_container['result'] = new_loop.run_until_complete(coro)
        except Exception as e:
            exception_container['error'] = e
        finally:
            new_loop.close()
    
    # Run in a new thread to get a clean event loop
    thread = threading.Thread(target=run_in_new_loop)
    thread.start()
    thread.join()  # Wait for completion
    
    if 'error' in exception_container:
        raise exception_container['error']
    return result_container.get('result')
