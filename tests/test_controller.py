import io
import os
import tempfile
import unittest
from unittest.mock import patch

import json_lib
from models.record import RecordRepository
from views.monitor_view import MonitorView
from app.watcher import FileWatcher
from controllers.monitor_controller import MonitorController


def _seed_file(path: str, records: list) -> None:
    json_lib.dump({'next_id': len(records) + 1, 'records': records}, path, indent=2)


def _make_controller(records: list = None) -> tuple[MonitorController, RecordRepository, str]:
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    if records:
        _seed_file(path, records)
    else:
        os.unlink(path)
    repo    = RecordRepository(path)
    view    = MonitorView()
    watcher = FileWatcher(path, callback=lambda: None, interval=60.0)
    ctrl    = MonitorController(repo, view, watcher)
    return ctrl, repo, path


class TestMonitorControllerList(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller([
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'},
        ])

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_list_records_output(self):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.list_records()
            output = mock_out.getvalue()
        self.assertIn('Alice', output)
        self.assertIn('Bob', output)

    def test_list_empty(self):
        ctrl, _, path = _make_controller()
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            ctrl.list_records()
        self.assertIn('저장된 데이터가 없습니다', mock_out.getvalue())
        if os.path.exists(path):
            os.unlink(path)


class TestMonitorControllerSearch(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller([
            {'id': 1, 'name': 'Alice', 'dept': 'Eng'},
            {'id': 2, 'name': 'Bob', 'dept': 'Design'},
        ])

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_search_found(self):
        inputs = iter(['dept', 'Eng'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.search_records()
        self.assertIn('Alice', mock_out.getvalue())
        self.assertIn('1건', mock_out.getvalue())

    def test_search_not_found(self):
        inputs = iter(['dept', 'HR'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.search_records()
        self.assertIn('검색 결과가 없습니다', mock_out.getvalue())


if __name__ == '__main__':
    unittest.main()
