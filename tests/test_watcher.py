import os
import tempfile
import threading
import time
import unittest

from app.watcher import FileWatcher


class TestFileWatcher(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        with open(self.path, 'w') as f:
            f.write('{}')

    def tearDown(self):
        if os.path.exists(self.path):
            os.unlink(self.path)

    def test_callback_called_on_change(self):
        called = threading.Event()
        watcher = FileWatcher(self.path, callback=called.set, interval=0.1)
        watcher.start()
        try:
            time.sleep(0.15)
            with open(self.path, 'w') as f:
                f.write('{"updated": true}')
            triggered = called.wait(timeout=2.0)
            self.assertTrue(triggered, '파일 변경 후 callback이 호출되어야 합니다.')
        finally:
            watcher.stop()

    def test_callback_not_called_without_change(self):
        call_count = [0]

        def on_change():
            call_count[0] += 1

        watcher = FileWatcher(self.path, callback=on_change, interval=0.1)
        watcher.start()
        try:
            time.sleep(0.5)
            self.assertEqual(call_count[0], 0, '변경 없으면 callback이 호출되면 안 됩니다.')
        finally:
            watcher.stop()

    def test_stop_terminates_thread(self):
        watcher = FileWatcher(self.path, callback=lambda: None, interval=0.1)
        watcher.start()
        self.assertTrue(watcher._thread.is_alive())
        watcher.stop()
        self.assertFalse(watcher._thread.is_alive())

    def test_missing_file_does_not_raise(self):
        missing = self.path + '_missing.json'
        called = threading.Event()
        watcher = FileWatcher(missing, callback=called.set, interval=0.1)
        watcher.start()
        try:
            time.sleep(0.3)
            # 파일이 없어도 예외 없이 실행되어야 함
        finally:
            watcher.stop()

    def test_callback_on_file_creation(self):
        """파일이 없다가 생성되면 callback이 호출되어야 한다."""
        missing = self.path + '_new.json'
        called = threading.Event()
        watcher = FileWatcher(missing, callback=called.set, interval=0.1)
        watcher.start()
        try:
            time.sleep(0.15)
            with open(missing, 'w') as f:
                f.write('{}')
            triggered = called.wait(timeout=2.0)
            self.assertTrue(triggered, '파일 생성 시 callback이 호출되어야 합니다.')
        finally:
            watcher.stop()
            if os.path.exists(missing):
                os.unlink(missing)


if __name__ == '__main__':
    unittest.main()
