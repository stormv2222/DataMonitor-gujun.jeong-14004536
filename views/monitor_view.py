import os
import platform
from datetime import datetime
from models.record import Record


class MonitorView:
    def show_dashboard(self, records: list[Record], last_modified: str) -> None:
        self._clear()
        fields = self._collect_fields(records)
        field_str = ', '.join(fields) if fields else '-'
        print(f'=== DataMonitor === [갱신: {last_modified}]')
        print(f'총 레코드: {len(records)}건  |  필드: {field_str}')
        print()
        if not records:
            print('  저장된 데이터가 없습니다.')
        else:
            for r in records:
                self._print_record_inline(r)
        print()
        print('명령어: (s)검색  (q)종료')

    def show_record(self, record: Record) -> None:
        print(f'[ID: {record.id}]')
        for k, v in record.fields.items():
            print(f'  {k}: {v}')

    def show_message(self, message: str) -> None:
        print(message)

    def get_input(self, prompt: str) -> str:
        return input(prompt).strip()

    def _clear(self) -> None:
        if platform.system() == 'Windows':
            os.system('cls')
        else:
            os.system('clear')

    def _collect_fields(self, records: list[Record]) -> list[str]:
        seen: list[str] = []
        for r in records:
            for k in r.fields:
                if k not in seen:
                    seen.append(k)
        return seen

    def _print_record_inline(self, record: Record) -> None:
        parts = [f'[ID: {record.id}]'] + [f'{k}={v}' for k, v in record.fields.items()]
        print('  ' + '  '.join(parts))
