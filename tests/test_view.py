import io
import sys
import unittest
from unittest.mock import patch

from models.record import Record
from views.monitor_view import MonitorView


def _make_record(record_id: int, **fields) -> Record:
    r = Record(fields=fields)
    r.id = record_id
    return r


class TestMonitorViewShowMessage(unittest.TestCase):
    def setUp(self):
        self.view = MonitorView()

    def test_show_message(self):
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.view.show_message('hello')
            self.assertIn('hello', mock_out.getvalue())


class TestMonitorViewShowRecord(unittest.TestCase):
    def setUp(self):
        self.view = MonitorView()

    def test_show_record_id(self):
        r = _make_record(3, name='Alice', dept='Eng')
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.view.show_record(r)
            output = mock_out.getvalue()
        self.assertIn('[ID: 3]', output)

    def test_show_record_fields(self):
        r = _make_record(1, name='Alice', dept='Eng')
        with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
            self.view.show_record(r)
            output = mock_out.getvalue()
        self.assertIn('name: Alice', output)
        self.assertIn('dept: Eng', output)


class TestMonitorViewShowDashboard(unittest.TestCase):
    def setUp(self):
        self.view = MonitorView()

    def _run_dashboard(self, records, ts='2026-01-01 00:00:00'):
        with patch.object(self.view, '_clear'):
            with patch('sys.stdout', new_callable=io.StringIO) as mock_out:
                self.view.show_dashboard(records, ts)
                return mock_out.getvalue()

    def test_dashboard_header(self):
        output = self._run_dashboard([])
        self.assertIn('DataMonitor', output)
        self.assertIn('2026-01-01 00:00:00', output)

    def test_dashboard_total_count(self):
        records = [_make_record(1, name='A'), _make_record(2, name='B')]
        output = self._run_dashboard(records)
        self.assertIn('2건', output)

    def test_dashboard_empty(self):
        output = self._run_dashboard([])
        self.assertIn('저장된 데이터가 없습니다', output)

    def test_dashboard_shows_records(self):
        records = [_make_record(1, name='Alice')]
        output = self._run_dashboard(records)
        self.assertIn('Alice', output)
        self.assertIn('ID: 1', output)

    def test_dashboard_collects_fields(self):
        records = [_make_record(1, name='A', dept='Eng')]
        output = self._run_dashboard(records)
        self.assertIn('name', output)
        self.assertIn('dept', output)

    def test_dashboard_commands_shown(self):
        output = self._run_dashboard([])
        self.assertIn('(s)', output)
        self.assertIn('(q)', output)


class TestMonitorViewGetInput(unittest.TestCase):
    def setUp(self):
        self.view = MonitorView()

    def test_get_input_strips(self):
        with patch('builtins.input', return_value='  hello  '):
            result = self.view.get_input('> ')
        self.assertEqual(result, 'hello')

    def test_get_input_empty(self):
        with patch('builtins.input', return_value=''):
            result = self.view.get_input('> ')
        self.assertEqual(result, '')


if __name__ == '__main__':
    unittest.main()
