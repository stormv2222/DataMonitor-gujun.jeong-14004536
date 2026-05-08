import os
import tempfile
import unittest

import json_lib
from models.record import Record, RecordRepository


def _make_repo() -> tuple[RecordRepository, str]:
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(path)
    return RecordRepository(path), path


def _seed_file(path: str, records: list) -> None:
    json_lib.dump({'next_id': len(records) + 1, 'records': records}, path, indent=2)


class TestRecord(unittest.TestCase):
    def test_record_id_default(self):
        r = Record(fields={'name': 'Alice'})
        self.assertEqual(r.id, 0)

    def test_record_fields(self):
        r = Record(fields={'name': 'Bob', 'age': '25'})
        self.assertEqual(r.fields['name'], 'Bob')
        self.assertEqual(r.fields['age'], '25')


class TestRecordRepositoryRead(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        self.path = path
        _seed_file(path, [
            {'id': 1, 'name': 'Alice', 'dept': 'Eng'},
            {'id': 2, 'name': 'Bob', 'dept': 'Design'},
        ])
        self.repo = RecordRepository(path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_read_all_returns_all(self):
        records = self.repo.read_all()
        self.assertEqual(len(records), 2)

    def test_read_all_empty(self):
        repo, _ = _make_repo()
        self.assertEqual(repo.read_all(), [])

    def test_read_one_found(self):
        r = self.repo.read_one(1)
        self.assertIsNotNone(r)
        self.assertEqual(r.fields['name'], 'Alice')

    def test_read_one_not_found(self):
        r = self.repo.read_one(999)
        self.assertIsNone(r)

    def test_id_not_in_fields(self):
        r = self.repo.read_one(1)
        self.assertNotIn('id', r.fields)


class TestRecordRepositorySearch(unittest.TestCase):
    def setUp(self):
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        self.path = path
        _seed_file(path, [
            {'id': 1, 'name': 'Alice', 'dept': 'Eng'},
            {'id': 2, 'name': 'Bob', 'dept': 'Design'},
            {'id': 3, 'name': 'Carol', 'dept': 'Eng'},
        ])
        self.repo = RecordRepository(path)

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_search_found(self):
        results = self.repo.search('dept', 'Eng')
        self.assertEqual(len(results), 2)
        names = {r.fields['name'] for r in results}
        self.assertEqual(names, {'Alice', 'Carol'})

    def test_search_not_found(self):
        results = self.repo.search('dept', 'HR')
        self.assertEqual(results, [])

    def test_search_missing_key(self):
        results = self.repo.search('nonexistent', 'value')
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()
