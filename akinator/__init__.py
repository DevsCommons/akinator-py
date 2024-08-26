"""
Akinator Library

This library provides an interface to interact with the Akinator game API.
It includes both synchronous and asynchronous implementations.

Classes:
    Akinator: Synchronous implementation of the Akinator game.
    AsyncAkinator: Asynchronous implementation of the Akinator game.

Usage:
    from akinator import Akinator, AsyncAkinator, Answer, Language

    # For synchronous usage
    aki = Akinator(language=Language.English)
    result = aki.start_game()

    # For asynchronous usage
    async_aki = AsyncAkinator(language=Language.French)
    result = await async_aki.start_game()
"""

from .akinator import Akinator, AsyncAkinator
from .enums import Answer, Language

__all__ = ["Akinator", "AsyncAkinator", "Answer", "Language"]

__version__ = "0.0.1"
__author__ = "Rio"
__email__ = "contact@devrio.org"
__url__ = "https://github.com/DevsCommons/akinator-py"
__license__ = "MIT"
__description__ = "A Python library for interacting with the Akinator game API"
