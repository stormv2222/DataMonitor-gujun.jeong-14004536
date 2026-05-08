from datetime import datetime

from models.record import Record, RecordRepository
from views.monitor_view import MonitorView
from app.watcher import FileWatcher


class MonitorController:
    def __init__(self, repository: RecordRepository, view: MonitorView, watcher: FileWatcher):
        self._repo = repository
        self._view = view
        self._watcher = watcher
        self._crud_active = False
        # 파일 변경 감지 시 대시보드 자동 갱신
        self._watcher._callback = self._on_file_changed

    def _on_file_changed(self) -> None:
        # CRUD 입력 중에는 화면을 건드리지 않음
        if not self._crud_active:
            self._do_refresh()

    def _do_refresh(self) -> None:
        records = self._repo.read_all()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._view.show_dashboard(records, now)

    def create_record(self) -> None:
        self._crud_active = True
        try:
            self._view.show_message('필드를 입력하세요. (완료: 필드명을 빈 줄로 입력)')
            fields: dict = {}
            while True:
                key = self._view.get_input('필드명: ')
                if not key:
                    break
                value = self._view.get_input('값: ')
                fields[key] = value
            if not fields:
                self._view.show_message('입력된 필드가 없어 저장하지 않습니다.')
                return
            record = self._repo.create(fields)
            self._view.show_message('추가되었습니다.')
            self._view.show_record(record)
        finally:
            self._crud_active = False

    def list_records(self) -> None:
        records = self._repo.read_all()
        if not records:
            self._view.show_message('저장된 데이터가 없습니다.')
            return
        for r in records:
            self._view.show_record(r)

    def update_record(self) -> None:
        self._crud_active = True
        try:
            raw_id = self._view.get_input('수정할 ID: ')
            if not raw_id.isdigit():
                self._view.show_message('숫자로 입력하세요.')
                return
            record_id = int(raw_id)
            record = self._repo.read_one(record_id)
            if record is None:
                self._view.show_message(f'ID {record_id} 에 해당하는 데이터가 없습니다.')
                return
            self._view.show_message('현재 데이터:')
            self._view.show_record(record)
            self._view.show_message('수정할 필드를 입력하세요. (완료: 필드명을 빈 줄로 입력)')
            valid_keys = set(record.fields.keys())
            fields: dict = {}
            while True:
                key = self._view.get_input('필드명: ')
                if not key:
                    break
                if key not in valid_keys:
                    self._view.show_message(f'"{key}" 필드가 존재하지 않습니다.')
                    continue
                value = self._view.get_input('값: ')
                fields[key] = value
            if not fields:
                self._view.show_message('변경 사항이 없습니다.')
                return
            updated = self._repo.update(record_id, fields)
            self._view.show_message('수정되었습니다.')
            self._view.show_record(updated)
        finally:
            self._crud_active = False

    def delete_record(self) -> None:
        self._crud_active = True
        try:
            raw_id = self._view.get_input('삭제할 ID: ')
            if not raw_id.isdigit():
                self._view.show_message('숫자로 입력하세요.')
                return
            record_id = int(raw_id)
            record = self._repo.read_one(record_id)
            if record is None:
                self._view.show_message(f'ID {record_id} 에 해당하는 데이터가 없습니다.')
                return
            self._view.show_message('삭제할 데이터:')
            self._view.show_record(record)
            confirm = self._view.get_input('정말 삭제하시겠습니까? (y/n): ')
            if confirm.lower() != 'y':
                self._view.show_message('삭제를 취소했습니다.')
                return
            self._repo.delete(record_id)
            self._view.show_message(f'ID {record_id} 를 삭제했습니다.')
        finally:
            self._crud_active = False

    def search_records(self) -> None:
        self._crud_active = True
        try:
            key = self._view.get_input('검색할 필드명: ')
            value = self._view.get_input('검색할 값: ')
            results = self._repo.search(key, value)
            if not results:
                self._view.show_message('검색 결과가 없습니다.')
                return
            self._view.show_message(f'{len(results)}건 검색되었습니다.')
            for r in results:
                self._view.show_record(r)
        finally:
            self._crud_active = False

    def run(self) -> None:
        self._watcher.start()
        try:
            self._do_refresh()
            while True:
                cmd = self._view.get_input('> ')
                if cmd == 'q':
                    self._view.show_message('종료합니다.')
                    break
                elif cmd == 'a':
                    self.create_record()
                    self._do_refresh()
                elif cmd == 'u':
                    self.update_record()
                    self._do_refresh()
                elif cmd == 'd':
                    self.delete_record()
                    self._do_refresh()
                elif cmd == 's':
                    self.search_records()
                else:
                    self._view.show_message('올바른 명령어를 입력하세요. (a/u/d/s/q)')
        finally:
            self._watcher.stop()
