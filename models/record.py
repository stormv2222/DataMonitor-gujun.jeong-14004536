import os
from dataclasses import dataclass, field
from typing import Optional

import json_lib


@dataclass
class Record:
    fields: dict
    id: int = field(default=0, init=False)


class RecordRepository:
    def __init__(self, file_path: str):
        self._file_path = file_path

    def _load_raw(self) -> dict:
        if not os.path.exists(self._file_path):
            return {'next_id': 1, 'records': []}
        raw = json_lib.load(self._file_path)
        if not isinstance(raw, dict) or 'records' not in raw:
            raise ValueError("데이터 파일 형식 오류: 'records' 키를 가진 객체여야 합니다.")
        if not isinstance(raw['records'], list):
            raise ValueError("데이터 파일 형식 오류: 'records' 값은 배열이어야 합니다.")
        return raw

    def _to_record(self, raw: dict) -> Record:
        r = Record(fields={k: v for k, v in raw.items() if k != 'id'})
        r.id = raw['id']
        return r

    def read_all(self) -> list[Record]:
        return [self._to_record(r) for r in self._load_raw()['records']]

    def read_one(self, record_id: int) -> Optional[Record]:
        for r in self._load_raw()['records']:
            if r['id'] == record_id:
                return self._to_record(r)
        return None

    def search(self, key: str, value: str) -> list[Record]:
        return [
            r for r in self.read_all()
            if str(r.fields.get(key, '')) == value
        ]
