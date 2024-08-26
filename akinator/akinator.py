import json
import os
import time
import uuid
from typing import Any, Dict

import aiohttp
import requests
from bs4 import BeautifulSoup

from .enums import Answer, Language, url_type
from .exceptions import ApiException
from .types import ErrorResponse, ResultStart, ResultWin

CACHE_DIR = "cache"
CACHE_FILE = os.path.join(CACHE_DIR, "akinator.json")
CACHE_DURATION = 10 * 60  # 10 minutes in seconds


class AkinatorCache:
    def __init__(self):
        if not os.path.exists(CACHE_DIR):
            os.makedirs(CACHE_DIR)

    def _load_from_file(self) -> Dict[str, Any]:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as file:
                return json.load(file)
        return {}

    def _save_to_file(self, cache: Dict[str, Any]) -> None:
        with open(CACHE_FILE, "w", encoding="utf-8") as file:
            json.dump(cache, file, indent=2)

    def set(self, key: str, value: Any) -> None:
        cache = self._load_from_file()
        cache[key] = {"data": value, "expiry": time.time() + CACHE_DURATION}
        self._save_to_file(cache)

    def get(self, key: str) -> Any:
        cache = self._load_from_file()
        item = cache.get(key)
        return item["data"] if item and item["expiry"] > time.time() else None

    def delete(self, key: str) -> None:
        cache = self._load_from_file()
        if key in cache:
            del cache[key]
            self._save_to_file(cache)

    def clear_cache(self) -> None:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)


class Akinator:
    """
    A class to interact with the Akinator game API.

    This class provides methods to start a game, answer questions, and go back to previous questions.
    It uses synchronous HTTP requests to communicate with the Akinator API.

    Attributes:
        language (Language): The language for the Akinator game.
        child_mode (bool): Whether to use child mode or not.
        id (str): A unique identifier for the current game session.
        cache (AkinatorCache): An instance of AkinatorCache to store game state.
    """

    def __init__(self, language: Language = Language.English, child_mode: bool = False):
        self.child_mode = child_mode
        self.language = language
        self.base_url = self._get_url(url_type.game)
        self.answer_url = self._get_url(url_type.answer)
        self.back_url = self._get_url(url_type.back)
        self.id = str(uuid.uuid4())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }
        self.cache = AkinatorCache()
        self.question = ""
        self.signature = ""
        self.session = ""

    def _get_url(self, type_url: url_type) -> str:
        return f"https://{self.language.value}.akinator.com/{type_url.value}"

    def start_game(self) -> ResultStart | ErrorResponse:
        """
        Start a new Akinator game session.

        This method initializes a new game, retrieves the first question, and sets up the necessary
        session information.

        Returns:
            ResultStart: If the game starts successfully, containing the first question and game info.
            ErrorResponse: If there's an error starting the game.
        """
        try:
            return self._start_game_internal()
        except (ApiException, requests.exceptions.RequestException) as e:
            return ErrorResponse.parse({"ok": False, "error": str(e)})

    def _start_game_internal(self) -> ResultStart:
        response = requests.post(
            self.base_url,
            headers=self.headers,
            data={"cm": str(self.child_mode), "sid": "1"},
            timeout=120,
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        self.question = soup.select_one("#question-label").text.strip()
        self.session = soup.select_one('form#askSoundlike input[name="session"]')[
            "value"
        ]
        self.signature = soup.select_one('form#askSoundlike input[name="signature"]')[
            "value"
        ]

        if not self.session or not self.signature:
            raise ApiException("Error starting game: Session or signature missing.")

        cache_data = {
            "session": self.session,
            "signature": self.signature,
            "progress": "0.00000",
            "step": 0,
        }
        self.cache.set(self.id, cache_data)

        return ResultStart.parse(
            {
                "ok": True,
                "result": {
                    "question": self.question,
                    "id": self.id,
                    "progress": "0.00000",
                    "step": 0,
                },
            }
        )

    def answer_question(
        self, id: str, answer: Answer
    ) -> ResultStart | ResultWin | ErrorResponse:
        """
        Submit an answer to the current question in the Akinator game.

        This method sends the user's answer to the Akinator API and retrieves the next question
        or the final guess.

        Args:
            id (str): The unique identifier for the current game session.
            answer (Answer): The user's answer to the current question.

        Returns:
            ResultStart: If there's another question, containing the new question and updated game info.
            ResultWin: If Akinator has made a guess, containing the guess details.
            ErrorResponse: If there's an error processing the answer.
        """
        cache = self.cache.get(id)
        if not cache:
            return ErrorResponse.parse({"ok": False, "error": "Invalid game ID"})

        try:
            response = requests.post(
                self.answer_url,
                headers=self.headers,
                data={
                    "step": cache["step"],
                    "progression": cache["progress"],
                    "answer": answer.value,
                    "session": cache["session"],
                    "signature": cache["signature"],
                    "question_filter": "string",
                    "sid": "NaN",
                    "cm": str(self.child_mode),
                    "step_last_proposition": "",
                },
                timeout=120,
            )
            result = response.json()

            if (
                response.status_code == 200
                and result["data"]["valide_contrainte"] is None
            ):
                updated_cache = {
                    "session": cache["session"],
                    "signature": cache["signature"],
                    "progress": result.get("progression"),
                    "step": result.get("step", ""),
                }
                self.cache.set(id, updated_cache)

                return ResultStart.parse(
                    {
                        "ok": True,
                        "result": {
                            "question": result.get("question"),
                            "id": id,
                            "progress": result.get("progression"),
                            "step": result.get("step", ""),
                        },
                    }
                )
            else:
                return ResultWin.parse(
                    {
                        "ok": True,
                        "result": {
                            "id": id,
                            "photo": result["data"]["photo"],
                            "description": result["data"]["description_proposition"],
                            "name": result["data"]["name_proposition"],
                        },
                    }
                )
        except (ApiException, requests.exceptions.RequestException) as e:
            return ErrorResponse.parse({"ok": False, "error": str(e)})

    def back(self, id: str) -> ResultStart | ErrorResponse:
        """
        Go back to the previous question in the Akinator game.

        This method allows the user to return to the previous question, undoing their last answer.

        Args:
            id (str): The unique identifier for the current game session.

        Returns:
            ResultStart: If successful, containing the previous question and updated game info.
            ErrorResponse: If there's an error going back or if it's not possible to go back further.
        """
        cache = self.cache.get(id)
        if not cache:
            return ErrorResponse.parse({"ok": False, "error": "Invalid game ID"})

        try:
            response = requests.post(
                self.back_url,
                headers=self.headers,
                data={
                    "session": cache["session"],
                    "signature": cache["signature"],
                    "step": cache["step"],
                    "progression": cache["progress"],
                    "cm": str(self.child_mode),
                },
                timeout=120,
            )
            result = response.json()

            if (
                response.status_code == 200
                and result["data"]["valide_contrainte"] is None
            ):
                updated_cache = {
                    "session": cache["session"],
                    "signature": cache["signature"],
                    "step": result["data"]["step"],
                    "progress": result["data"]["progression"],
                }
                self.cache.set(id, updated_cache)

                return ResultStart.parse(
                    {
                        "ok": True,
                        "result": {
                            "question": result["data"]["question"],
                            "id": id,
                            "progress": result["data"]["progression"],
                            "step": result["data"]["step"],
                        },
                    }
                )
            else:
                return ErrorResponse.parse({"ok": False, "error": "Unable to go back"})
        except (ApiException, requests.exceptions.RequestException) as e:
            return ErrorResponse.parse({"ok": False, "error": str(e)})


class AsyncAkinator:
    """
    An asynchronous class to interact with the Akinator game API.

    This class provides asynchronous methods to start a game, answer questions, and go back to previous questions.
    It uses asynchronous HTTP requests to communicate with the Akinator API.

    Attributes:
        language (Language): The language for the Akinator game.
        child_mode (bool): Whether to use child mode or not.
        id (str): A unique identifier for the current game session.
        cache (AkinatorCache): An instance of AkinatorCache to store game state.
    """

    def __init__(self, language: Language = Language.English, child_mode: bool = False):
        self.child_mode = child_mode
        self.language = language
        self.base_url = self._get_url(url_type.game)
        self.answer_url = self._get_url(url_type.answer)
        self.back_url = self._get_url(url_type.back)
        self.id = str(uuid.uuid4())
        self.headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36"
        }
        self.cache = AkinatorCache()
        self.question = ""
        self.signature = ""
        self.session = ""

    def _get_url(self, type_url: url_type) -> str:
        return f"https://{self.language.value}.akinator.com/{type_url.value}"

    async def start_game(self) -> ResultStart | ErrorResponse:
        """
        Start a new Akinator game session asynchronously.

        This method initializes a new game, retrieves the first question, and sets up the necessary
        session information using asynchronous HTTP requests.

        Returns:
            ResultStart: If the game starts successfully, containing the first question and game info.
            ErrorResponse: If there's an error starting the game.
        """
        try:
            return await self._start_game_internal()
        except (ApiException, aiohttp.ClientError) as e:
            return ErrorResponse.parse({"ok": False, "error": str(e)})

    async def _start_game_internal(self) -> ResultStart:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.base_url,
                headers=self.headers,
                data={"cm": str(self.child_mode), "sid": "1"},
                timeout=120,
            ) as response:
                response.raise_for_status()
                text = await response.text()

        soup = BeautifulSoup(text, "html.parser")

        self.question = soup.select_one("#question-label").text.strip()
        self.session = soup.select_one('form#askSoundlike input[name="session"]')[
            "value"
        ]
        self.signature = soup.select_one('form#askSoundlike input[name="signature"]')[
            "value"
        ]

        if not self.session or not self.signature:
            raise ApiException("Error starting game: Session or signature missing.")

        cache_data = {
            "session": self.session,
            "signature": self.signature,
            "progress": "0.00000",
            "step": 0,
        }
        self.cache.set(self.id, cache_data)

        return ResultStart.parse(
            {
                "ok": True,
                "result": {
                    "question": self.question,
                    "id": self.id,
                    "progress": "0.00000",
                    "step": 0,
                },
            }
        )

    async def answer_question(
        self, id: str, answer: Answer
    ) -> ResultStart | ResultWin | ErrorResponse:
        """
        Submit an answer to the current question in the Akinator game asynchronously.

        This method sends the user's answer to the Akinator API and retrieves the next question
        or the final guess using asynchronous HTTP requests.

        Args:
            id (str): The unique identifier for the current game session.
            answer (Answer): The user's answer to the current question.

        Returns:
            ResultStart: If there's another question, containing the new question and updated game info.
            ResultWin: If Akinator has made a guess, containing the guess details.
            ErrorResponse: If there's an error processing the answer.
        """
        cache = self.cache.get(id)
        if not cache:
            return ErrorResponse.parse({"ok": False, "error": "Invalid game ID"})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.answer_url,
                    headers=self.headers,
                    data={
                        "step": cache["step"],
                        "progression": cache["progress"],
                        "answer": answer.value,
                        "session": cache["session"],
                        "signature": cache["signature"],
                        "question_filter": "string",
                        "sid": "NaN",
                        "cm": str(self.child_mode),
                        "step_last_proposition": "",
                    },
                    timeout=120,
                ) as response:
                    result = await response.json()

            if response.status == 200 and result["data"]["valide_contrainte"] is None:
                updated_cache = {
                    "session": cache["session"],
                    "signature": cache["signature"],
                    "progress": result.get("progression"),
                    "step": result.get("step", ""),
                }
                self.cache.set(id, updated_cache)

                return ResultStart.parse(
                    {
                        "ok": True,
                        "result": {
                            "question": result.get("question"),
                            "id": id,
                            "progress": result.get("progression"),
                            "step": result.get("step", ""),
                        },
                    }
                )
            else:
                return ResultWin.parse(
                    {
                        "ok": True,
                        "result": {
                            "id": id,
                            "photo": result["data"]["photo"],
                            "description": result["data"]["description_proposition"],
                            "name": result["data"]["name_proposition"],
                        },
                    }
                )
        except (ApiException, aiohttp.ClientError) as e:
            return ErrorResponse.parse({"ok": False, "error": str(e)})

    async def back(self, id: str) -> ResultStart | ErrorResponse:
        """
        Go back to the previous question in the Akinator game asynchronously.

        This method allows the user to return to the previous question, undoing their last answer,
        using asynchronous HTTP requests.

        Args:
            id (str): The unique identifier for the current game session.

        Returns:
            ResultStart: If successful, containing the previous question and updated game info.
            ErrorResponse: If there's an error going back or if it's not possible to go back further.
        """
        cache = self.cache.get(id)
        if not cache:
            return ErrorResponse.parse({"ok": False, "error": "Invalid game ID"})

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.back_url,
                    headers=self.headers,
                    data={
                        "session": cache["session"],
                        "signature": cache["signature"],
                        "step": cache["step"],
                        "progression": cache["progress"],
                        "cm": str(self.child_mode),
                    },
                    timeout=120,
                ) as response:
                    result = await response.json()

            if response.status == 200 and result["data"]["valide_contrainte"] is None:
                updated_cache = {
                    "session": cache["session"],
                    "signature": cache["signature"],
                    "step": result["data"]["step"],
                    "progress": result["data"]["progression"],
                }
                self.cache.set(id, updated_cache)

                return ResultStart.parse(
                    {
                        "ok": True,
                        "result": {
                            "question": result["data"]["question"],
                            "id": id,
                            "progress": result["data"]["progression"],
                            "step": result["data"]["step"],
                        },
                    }
                )
            else:
                return ErrorResponse.parse({"ok": False, "error": "Unable to go back"})
        except (ApiException, aiohttp.ClientError) as e:
            return ErrorResponse.parse({"ok": False, "error": str(e)})
