from dataclasses import dataclass
from json import dumps
from typing import Any, Dict


class Base:
    @staticmethod
    def default(obj: "Base") -> Dict[str, Any]:
        return {
            attr: getattr(obj, attr)
            for attr in filter(lambda x: not x.startswith("__"), obj.__dict__)
        }

    def __str__(self) -> str:
        return dumps(self, indent=4, default=Base.default, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Base":
        return cls(**data)


@dataclass
class Result(Base):
    id: str
    question: str
    step: int
    progress: float


@dataclass
class ResultStart(Base):
    ok: bool
    result: Result

    @staticmethod
    def parse(data: Dict[str, Any]) -> "ResultStart":
        result_data = data.get("result", {})
        result = Result(
            id=result_data.get("id", ""),
            question=result_data.get("question", ""),
            step=result_data.get("step", ""),
            progress=result_data.get("progress", ""),
        )
        return ResultStart(ok=data.get("ok", False), result=result)


@dataclass
class WinDetails(Base):
    id: str
    photo: str
    description: str
    name: str


@dataclass
class ResultWin(Base):
    ok: bool
    result: WinDetails

    @staticmethod
    def parse(data: Dict[str, Any]) -> "ResultWin":
        result_data = data.get("result", {})
        result = WinDetails(
            id=result_data.get("id", ""),
            photo=result_data.get("photo", ""),
            description=result_data.get("description", ""),
            name=result_data.get("name", ""),
        )
        return ResultWin(ok=data.get("ok", False), result=result)


@dataclass
class ErrorResponse(Base):
    ok: bool
    error: str

    @staticmethod
    def parse(data: Dict[str, Any]) -> "ErrorResponse":
        return ErrorResponse(ok=data.get("ok", False), error=data.get("error", ""))
