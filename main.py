import os

from models.record import RecordRepository
from views.monitor_view import MonitorView
from app.watcher import FileWatcher
from controllers.monitor_controller import MonitorController

DATA_FILE = 'data/records.json'


def _ensure_data_file(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        import json_lib
        json_lib.dump({'next_id': 1, 'records': []}, path, indent=2)


if __name__ == '__main__':
    _ensure_data_file(DATA_FILE)

    repo    = RecordRepository(DATA_FILE)
    view    = MonitorView()
    watcher = FileWatcher(DATA_FILE, callback=lambda: None)  # callback은 Controller가 재설정
    ctrl    = MonitorController(repo, view, watcher)
    ctrl.run()
