# ============================================================
# LocalBuffer - Offline data queue using btree (or simple list fallback)
# Survives power loss via filesystem, drops oldest when full (500 records)
# ============================================================

import ujson
import os
import uos

MAX_RECORDS = 500
BUFFER_FILE = "buffer.dat"


class LocalBuffer:
    def __init__(self, max_records=MAX_RECORDS):
        self.max_records = max_records
        self.records = []
        self._load()

    def _load(self):
        try:
            if BUFFER_FILE in uos.listdir():
                with open(BUFFER_FILE, "r") as f:
                    data = f.read()
                    if data:
                        self.records = ujson.loads(data)
                    if not isinstance(self.records, list):
                        self.records = []
        except Exception:
            self.records = []

    def _save(self):
        try:
            with open(BUFFER_FILE, "w") as f:
                f.write(ujson.dumps(self.records))
        except Exception:
            pass

    def add(self, payload):
        if len(self.records) >= self.max_records:
            self.records.pop(0)
        self.records.append(payload)
        self._save()

    def get_all(self):
        return list(self.records)

    def clear(self):
        self.records = []
        self._save()

    def __len__(self):
        return len(self.records)