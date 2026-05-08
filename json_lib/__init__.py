from typing import Any
from json_lib.lexer import tokenize
from json_lib.parser import parse
from json_lib.serializer import serialize


def load(file_path: str) -> Any:
    with open(file_path, 'r', encoding='utf-8') as f:
        text = f.read()
    return parse(tokenize(text))


def dump(data: Any, file_path: str, indent: int | None = None) -> None:
    json_str = serialize(data, indent)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_str)
