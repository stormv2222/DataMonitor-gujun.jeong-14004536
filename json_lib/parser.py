from typing import Any
from json_lib.lexer import Token, TokenType


class ParseError(Exception):
    def __init__(self, message: str, pos: int):
        super().__init__(f"{message} (token position {pos})")
        self.pos = pos


class Parser:
    def __init__(self, tokens: list[Token]):
        self._tokens = tokens
        self._pos    = 0

    def parse(self) -> Any:
        result = self._parse_value()
        if self._current() is not None:
            raise ParseError(
                f"Unexpected token after value: {self._current().type}",
                self._current().pos,
            )
        return result

    def _current(self) -> Token | None:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return None

    def _consume(self, expected_type: TokenType) -> Token:
        token = self._current()
        if token is None:
            raise ParseError(f"Unexpected end of tokens, expected {expected_type}", -1)
        if token.type != expected_type:
            raise ParseError(
                f"Expected {expected_type}, got {token.type}",
                token.pos,
            )
        self._pos += 1
        return token

    def _parse_value(self) -> Any:
        token = self._current()
        if token is None:
            raise ParseError("Unexpected end of tokens", -1)
        if token.type == TokenType.LBRACE:
            return self._parse_object()
        if token.type == TokenType.LBRACKET:
            return self._parse_array()
        if token.type in (TokenType.STRING, TokenType.NUMBER, TokenType.BOOL, TokenType.NULL):
            self._pos += 1
            return token.value
        raise ParseError(f"Unexpected token: {token.type}", token.pos)

    def _parse_object(self) -> dict:
        self._consume(TokenType.LBRACE)
        result = {}
        if self._current() is not None and self._current().type == TokenType.RBRACE:
            self._pos += 1
            return result
        while True:
            key_token = self._consume(TokenType.STRING)
            self._consume(TokenType.COLON)
            value = self._parse_value()
            result[key_token.value] = value
            cur = self._current()
            if cur is None:
                raise ParseError("Unexpected end of tokens, expected '}' or ','", -1)
            if cur.type == TokenType.RBRACE:
                self._pos += 1
                break
            if cur.type == TokenType.COMMA:
                self._pos += 1
            else:
                raise ParseError(f"Expected ',' or '}}', got {cur.type}", cur.pos)
        return result

    def _parse_array(self) -> list:
        self._consume(TokenType.LBRACKET)
        result = []
        if self._current() is not None and self._current().type == TokenType.RBRACKET:
            self._pos += 1
            return result
        while True:
            result.append(self._parse_value())
            cur = self._current()
            if cur is None:
                raise ParseError("Unexpected end of tokens, expected ']' or ','", -1)
            if cur.type == TokenType.RBRACKET:
                self._pos += 1
                break
            if cur.type == TokenType.COMMA:
                self._pos += 1
            else:
                raise ParseError(f"Expected ',' or ']', got {cur.type}", cur.pos)
        return result


def parse(tokens: list[Token]) -> Any:
    return Parser(tokens).parse()
