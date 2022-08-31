import unittest
from mopidy_jukebox.frontend.rfid.tag_registry import TagRegistry
from tempfile import TemporaryDirectory
from pathlib import Path


class TagRegistryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = TemporaryDirectory()
        self.db_path = Path(self.tmp_dir.name) / 'tagRegistry.db'

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test__init_db(self):
        assert self.db_path.exists() == False
        registry = TagRegistry(self.db_path)
        assert self.db_path.exists()

    def test_create(self):
        registry = TagRegistry(self.db_path)
        registry.create(0)
        res = registry.get(0)
        assert res['tag_uid'] == 0
        assert res['mopidy_uuid'] == ""
        assert res['active'] == False
        assert res['req_count'] == 0

    def test_get(self):
        registry = TagRegistry(self.db_path)
        res = registry.get(0)
        assert res == None



