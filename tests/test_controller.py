import io
import os
import tempfile
import unittest
from unittest.mock import patch

from models.record import RecordRepository
from views.monitor_view import MonitorView
from app.watcher import FileWatcher
from controllers.monitor_controller import MonitorController


def _make_controller() -> tuple[MonitorController, RecordRepository, str]:
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(path)
    repo    = RecordRepository(path)
    view    = MonitorView()
    watcher = FileWatcher(path, callback=lambda: None, interval=60.0)  # 테스트 중 자동 감지 비활성
    ctrl    = MonitorController(repo, view, watcher)
    return ctrl, repo, path


class TestMonitorControllerCreate(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller()

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_record(self):
        inputs = iter(['name', 'Alice', 'dept', 'Eng', ''])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.create_record()
        records = self.repo.read_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].fields['name'], 'Alice')
        self.assertEqual(records[0].fields['dept'], 'Eng')

    def test_create_empty_fields_not_saved(self):
        inputs = iter([''])  # 바로 빈 줄 입력
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.create_record()
        self.assertEqual(self.repo.read_all(), [])

    def test_create_sets_auto_id(self):
        inputs = iter(['name', 'Bob', ''])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.create_record()
        r = self.repo.read_one(1)
        self.assertIsNotNone(r)
        self.assertEqual(r.id, 1)


class TestMonitorControllerList(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller()
        self.repo.create({'name': 'Alice'})
        self.repo.create({'name': 'Bob'})

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
        repo2 = RecordRepository(self.path + '_empty')
        view  = MonitorView()
        w     = FileWatcher(self.path, callback=lambda: None, interval=60.0)
        ctrl  = MonitorController(repo2, view, w)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            ctrl.list_records()
        self.assertIn('저장된 데이터가 없습니다', mock_out.getvalue())


class TestMonitorControllerUpdate(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller()
        self.repo.create({'name': 'Alice', 'level': 'Junior'})

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_update_record(self):
        inputs = iter(['1', 'level', 'Senior', ''])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.update_record()
        r = self.repo.read_one(1)
        self.assertEqual(r.fields['level'], 'Senior')

    def test_update_invalid_id(self):
        inputs = iter(['abc'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.update_record()
        self.assertIn('숫자로 입력하세요', mock_out.getvalue())

    def test_update_not_found(self):
        inputs = iter(['999'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.update_record()
        self.assertIn('해당하는 데이터가 없습니다', mock_out.getvalue())

    def test_update_invalid_field_rejected(self):
        # 존재하지 않는 필드명 입력 후 빈 줄로 종료
        inputs = iter(['1', 'nonexistent', '', ''])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.update_record()
            output = mock_out.getvalue()
        self.assertIn('존재하지 않습니다', output)


class TestMonitorControllerDelete(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller()
        self.repo.create({'name': 'Alice'})

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_delete_confirmed(self):
        inputs = iter(['1', 'y'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.delete_record()
        self.assertIsNone(self.repo.read_one(1))

    def test_delete_cancelled(self):
        inputs = iter(['1', 'n'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.delete_record()
        self.assertIsNotNone(self.repo.read_one(1))

    def test_delete_invalid_id(self):
        inputs = iter(['abc'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.delete_record()
        self.assertIn('숫자로 입력하세요', mock_out.getvalue())

    def test_delete_not_found(self):
        inputs = iter(['999'])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.ctrl.delete_record()
        self.assertIn('해당하는 데이터가 없습니다', mock_out.getvalue())


class TestMonitorControllerSearch(unittest.TestCase):
    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller()
        self.repo.create({'name': 'Alice', 'dept': 'Eng'})
        self.repo.create({'name': 'Bob',   'dept': 'Design'})

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


class TestMonitorControllerCrudActive(unittest.TestCase):
    """CRUD 실행 중 _crud_active 플래그가 올바르게 관리되는지 검증."""

    def setUp(self):
        self.ctrl, self.repo, self.path = _make_controller()

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_crud_active_false_after_create(self):
        inputs = iter([''])
        self.ctrl._view.get_input = lambda prompt: next(inputs)
        with patch('sys.stdout', new_callable=io.StringIO):
            self.ctrl.create_record()
        self.assertFalse(self.ctrl._crud_active)

    def test_crud_active_false_after_exception(self):
        def raise_error(prompt):
            raise RuntimeError('simulate error')
        self.ctrl._view.get_input = raise_error
        with self.assertRaises(RuntimeError):
            self.ctrl.create_record()
        self.assertFalse(self.ctrl._crud_active)


if __name__ == '__main__':
    unittest.main()
