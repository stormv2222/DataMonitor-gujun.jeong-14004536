import os
import tempfile
import unittest

from models.record import Record, RecordRepository


def _make_repo() -> tuple[RecordRepository, str]:
    fd, path = tempfile.mkstemp(suffix='.json')
    os.close(fd)
    os.unlink(path)  # 파일 없는 상태로 시작 (RecordRepository가 자동 처리)
    return RecordRepository(path), path


class TestRecord(unittest.TestCase):
    def test_record_id_default(self):
        r = Record(fields={'name': 'Alice'})
        self.assertEqual(r.id, 0)

    def test_record_fields(self):
        r = Record(fields={'name': 'Bob', 'age': '25'})
        self.assertEqual(r.fields['name'], 'Bob')
        self.assertEqual(r.fields['age'], '25')


class TestRecordRepositoryCreate(unittest.TestCase):
    def setUp(self):
        self.repo, self.path = _make_repo()

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_create_returns_record_with_id(self):
        r = self.repo.create({'name': 'Alice'})
        self.assertEqual(r.id, 1)
        self.assertEqual(r.fields['name'], 'Alice')

    def test_create_increments_id(self):
        r1 = self.repo.create({'name': 'Alice'})
        r2 = self.repo.create({'name': 'Bob'})
        self.assertEqual(r1.id, 1)
        self.assertEqual(r2.id, 2)

    def test_create_persists_to_file(self):
        self.repo.create({'name': 'Alice'})
        repo2 = RecordRepository(self.path)
        records = repo2.read_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].fields['name'], 'Alice')


class TestRecordRepositoryRead(unittest.TestCase):
    def setUp(self):
        self.repo, self.path = _make_repo()
        self.repo.create({'name': 'Alice', 'dept': 'Eng'})
        self.repo.create({'name': 'Bob',   'dept': 'Design'})

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_read_all_returns_all(self):
        records = self.repo.read_all()
        self.assertEqual(len(records), 2)

    def test_read_all_empty(self):
        repo, path = _make_repo()
        self.assertEqual(repo.read_all(), [])
        # path는 파일이 생성되지 않으므로 cleanup 불필요

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


class TestRecordRepositoryUpdate(unittest.TestCase):
    def setUp(self):
        self.repo, self.path = _make_repo()
        self.repo.create({'name': 'Alice', 'level': 'Junior'})

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_update_existing(self):
        updated = self.repo.update(1, {'level': 'Senior'})
        self.assertIsNotNone(updated)
        self.assertEqual(updated.fields['level'], 'Senior')
        self.assertEqual(updated.fields['name'], 'Alice')

    def test_update_not_found(self):
        result = self.repo.update(999, {'level': 'Senior'})
        self.assertIsNone(result)

    def test_update_persists(self):
        self.repo.update(1, {'level': 'Senior'})
        r = RecordRepository(self.path).read_one(1)
        self.assertEqual(r.fields['level'], 'Senior')


class TestRecordRepositorySearch(unittest.TestCase):
    def setUp(self):
        self.repo, self.path = _make_repo()
        self.repo.create({'name': 'Alice', 'dept': 'Eng'})
        self.repo.create({'name': 'Bob',   'dept': 'Design'})
        self.repo.create({'name': 'Carol', 'dept': 'Eng'})

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


class TestRecordRepositoryDelete(unittest.TestCase):
    def setUp(self):
        self.repo, self.path = _make_repo()
        self.repo.create({'name': 'Alice'})
        self.repo.create({'name': 'Bob'})

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_delete_existing(self):
        result = self.repo.delete(1)
        self.assertTrue(result)
        self.assertIsNone(self.repo.read_one(1))
        self.assertEqual(len(self.repo.read_all()), 1)

    def test_delete_not_found(self):
        result = self.repo.delete(999)
        self.assertFalse(result)

    def test_delete_persists(self):
        self.repo.delete(1)
        records = RecordRepository(self.path).read_all()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].fields['name'], 'Bob')


if __name__ == '__main__':
    unittest.main()
