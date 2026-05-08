from typing import Any


class SerializeError(Exception):
    def __init__(self, value: Any):
        super().__init__(f"Unsupported type: {type(value).__name__} ({value!r})")
        self.value = value


_STRING_ESCAPE_MAP = {
    '"':  '\\"',
    '\\': '\\\\',
    '\n': '\\n',
    '\t': '\\t',
    '\r': '\\r',
    '\b': '\\b',
    '\f': '\\f',
}


class Serializer:
    def __init__(self, indent: int | None = None):
        self._indent = indent

    def serialize(self, value: Any) -> str:
        return self._serialize_value(value, level=0)

    def _serialize_value(self, value: Any, level: int) -> str:
        if isinstance(value, bool):
            return 'true' if value else 'false'
        if value is None:
            return 'null'
        if isinstance(value, str):
            return self._serialize_string(value)
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            return str(value)
        if isinstance(value, dict):
            return self._serialize_object(value, level)
        if isinstance(value, list):
            return self._serialize_array(value, level)
        raise SerializeError(value)

    def _serialize_string(self, s: str) -> str:
        buf = ['"']
        for ch in s:
            buf.append(_STRING_ESCAPE_MAP.get(ch, ch))
        buf.append('"')
        return ''.join(buf)

    def _serialize_object(self, obj: dict, level: int) -> str:
        if not obj:
            return '{}'
        if self._indent is None:
            items = ', '.join(
                f'{self._serialize_string(k)}: {self._serialize_value(v, level)}'
                for k, v in obj.items()
            )
            return '{' + items + '}'
        child_pad = ' ' * (self._indent * (level + 1))
        close_pad = ' ' * (self._indent * level)
        lines = []
        keys = list(obj.keys())
        for i, k in enumerate(keys):
            comma = ',' if i < len(keys) - 1 else ''
            lines.append(f'{child_pad}{self._serialize_string(k)}: {self._serialize_value(obj[k], level + 1)}{comma}')
        return '{\n' + '\n'.join(lines) + '\n' + close_pad + '}'

    def _serialize_array(self, arr: list, level: int) -> str:
        if not arr:
            return '[]'
        if self._indent is None:
            items = ', '.join(self._serialize_value(v, level) for v in arr)
            return '[' + items + ']'
        child_pad = ' ' * (self._indent * (level + 1))
        close_pad = ' ' * (self._indent * level)
        lines = []
        for i, v in enumerate(arr):
            comma = ',' if i < len(arr) - 1 else ''
            lines.append(f'{child_pad}{self._serialize_value(v, level + 1)}{comma}')
        return '[\n' + '\n'.join(lines) + '\n' + close_pad + ']'


def serialize(value: Any, indent: int | None = None) -> str:
    return Serializer(indent).serialize(value)
