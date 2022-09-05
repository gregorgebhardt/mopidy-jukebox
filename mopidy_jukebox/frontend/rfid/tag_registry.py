import sqlite3
import os
from pathlib import Path
import logging


DATABASE = 'tag_registry.db'

logger = logging.getLogger("mopidy_jukebox.RFID")


class TagRegistry:
    def __init__(self, db_path=None):
        if db_path is None:
            app_data = Path.home() / ".jukebox"
            app_data.mkdir(parents=True, exist_ok=True)
            db_path = app_data / "tagRegistry.db"
        self.con = sqlite3.connect(database=db_path)
        self.con.row_factory = sqlite3.Row
        self._init_db()

    def __del__(self):
        self.con.close()

    def _init_db(self):
        res = self.con.execute("SELECT name FROM sqlite_master")
        if 'tag_registry' in res.fetchall():
            return

        self.con.execute("CREATE TABLE tag_registry(tag_uid integer primary key, mopidy_uuid varchar, active boolean, req_count integer)")
        self.con.execute("CREATE TABLE tag_log(datetime, tag_uid)")

    def create(self, tag_uid):
        with self.con:
            cur = self.con.cursor()
            try:
                cur.execute("INSERT INTO tag_registry VALUES (?, '', FALSE, 0)", (tag_uid,))
            except sqlite3.IntegrityError as e:
                logger.warning(e)

    def get(self, tag_uid):
        with self.con:
            cur = self.con.execute("SELECT tag_uid, mopidy_uuid, active, req_count FROM tag_registry where tag_uid=?", (tag_uid,))
            self.con.execute("UPDATE tag_registry SET req_count = req_count + 1 WHERE tag_uid=?", (tag_uid,))
        return cur.fetchone()

