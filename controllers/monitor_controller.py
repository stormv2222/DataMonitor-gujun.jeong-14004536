from datetime import datetime

from models.record import RecordRepository
from views.monitor_view import MonitorView
from app.watcher import FileWatcher


class MonitorController:
    def __init__(self, repository: RecordRepository, view: MonitorView, watcher: FileWatcher):
        self._repo = repository
        self._view = view
        self._watcher = watcher
        self._watcher._callback = self._on_file_changed

    def _on_file_changed(self) -> None:
        self._do_refresh()

    def _do_refresh(self) -> None:
        records = self._repo.read_all()
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self._view.show_dashboard(records, now)

    def list_records(self) -> None:
        records = self._repo.read_all()
        if not records:
            self._view.show_message('저장된 데이터가 없습니다.')
            return
        for r in records:
            self._view.show_record(r)

    def search_records(self) -> None:
        key = self._view.get_input('검색할 필드명: ')
        value = self._view.get_input('검색할 값: ')
        results = self._repo.search(key, value)
        if not results:
            self._view.show_message('검색 결과가 없습니다.')
            return
        self._view.show_message(f'{len(results)}건 검색되었습니다.')
        for r in results:
            self._view.show_record(r)

    def run(self) -> None:
        self._watcher.start()
        try:
            self._do_refresh()
            while True:
                cmd = self._view.get_input('> ')
                if cmd == 'q':
                    self._view.show_message('종료합니다.')
                    break
                elif cmd == 's':
                    self.search_records()
                else:
                    self._view.show_message('올바른 명령어를 입력하세요. (s/q)')
        finally:
            self._watcher.stop()
