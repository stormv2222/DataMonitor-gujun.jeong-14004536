from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenType(Enum):
    STRING   = "STRING"
    NUMBER   = "NUMBER"
    BOOL     = "BOOL"
    NULL     = "NULL"
    LBRACE   = "LBRACE"
    RBRACE   = "RBRACE"
    LBRACKET = "LBRACKET"
    RBRACKET = "RBRACKET"
    COLON    = "COLON"
    COMMA    = "COMMA"


@dataclass
class Token:
    type:  TokenType
    value: Any
    pos:   int


class LexError(Exception):
    def __init__(self, message: str, pos: int):
        super().__init__(f"{message} (position {pos})")
        self.pos = pos


_ESCAPE_MAP = {
    '"':  '"',
    '\\': '\\',
    '/':  '/',
    'n':  '\n',
    't':  '\t',
    'r':  '\r',
    'b':  '\b',
    'f':  '\f',
}

_STRUCTURAL = {
    '{': TokenType.LBRACE,
    '}': TokenType.RBRACE,
    '[': TokenType.LBRACKET,
    ']': TokenType.RBRACKET,
    ':': TokenType.COLON,
    ',': TokenType.COMMA,
}


class Lexer:
    def __init__(self, text: str):
        self._text = text
        self._pos  = 0

    def tokenize(self) -> list[Token]:
        tokens = []
        while self._pos < len(self._text):
            ch = self._current()
            if ch in ' \t\n\r':
                self._skip_whitespace()
            elif ch == '"':
                tokens.append(self._read_string())
            elif ch == '-' or ch.isdigit():
                tokens.append(self._read_number())
            elif ch in 'tfn':
                tokens.append(self._read_keyword())
            elif ch in _STRUCTURAL:
                tokens.append(Token(_STRUCTURAL[ch], ch, self._pos))
                self._advance()
            else:
                raise LexError(f"Unexpected character: {ch!r}", self._pos)
        return tokens

    def _current(self) -> str | None:
        if self._pos < len(self._text):
            return self._text[self._pos]
        return None

    def _advance(self) -> None:
        self._pos += 1

    def _skip_whitespace(self) -> None:
        while self._pos < len(self._text) and self._text[self._pos] in ' \t\n\r':
            self._pos += 1

    def _read_string(self) -> Token:
        start = self._pos
        self._advance()
        buf = []
        while True:
            ch = self._current()
            if ch is None:
                raise LexError("Unterminated string", start)
            if ch == '"':
                self._advance()
                break
            if ch == '\\':
                self._advance()
                esc = self._current()
                if esc is None:
                    raise LexError("Unterminated escape sequence", self._pos)
                if esc not in _ESCAPE_MAP:
                    raise LexError(f"Invalid escape sequence: \\{esc}", self._pos)
                buf.append(_ESCAPE_MAP[esc])
                self._advance()
            else:
                buf.append(ch)
                self._advance()
        return Token(TokenType.STRING, ''.join(buf), start)

    def _read_number(self) -> Token:
        start = self._pos
        buf = []
        if self._current() == '-':
            buf.append('-')
            self._advance()
            if self._current() is None or not self._current().isdigit():
                raise LexError("Invalid number: expected digit after '-'", start)
        while self._current() is not None and self._current().isdigit():
            buf.append(self._current())
            self._advance()
        is_float = False
        if self._current() == '.':
            is_float = True
            buf.append('.')
            self._advance()
            while self._current() is not None and self._current().isdigit():
                buf.append(self._current())
                self._advance()
        raw = ''.join(buf)
        value = float(raw) if is_float else int(raw)
        return Token(TokenType.NUMBER, value, start)

    def _read_keyword(self) -> Token:
        start = self._pos
        buf = []
        while self._current() is not None and self._current().isalpha():
            buf.append(self._current())
            self._advance()
        word = ''.join(buf)
        if word == 'true':
            return Token(TokenType.BOOL, True, start)
        if word == 'false':
            return Token(TokenType.BOOL, False, start)
        if word == 'null':
            return Token(TokenType.NULL, None, start)
        raise LexError(f"Unknown keyword: {word!r}", start)


def tokenize(text: str) -> list[Token]:
    return Lexer(text).tokenize()
