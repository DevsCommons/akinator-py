from enum import Enum


class Language(Enum):
    English = "en"
    Arabic = "ar"
    Chinese = "cn"
    German = "de"
    Spanish = "es"
    French = "fr"
    Italian = "it"
    Japanese = "jp"
    Korean = "kr"
    Dutch = "nl"
    Polish = "pl"
    Portuguese = "pt"
    Russian = "ru"
    Turkish = "tr"
    Indonesian = "id"


class url_type(Enum):
    game = "game"
    answer = "answer"
    back = "back"


class Answer(Enum):
    YES = 0
    NO = 1
    IDK = 2
    PROBABLY = 3
    PROBABLYNOT = 4
    Y = YES
    N = NO
    P = PROBABLY
    PN = PROBABLYNOT
