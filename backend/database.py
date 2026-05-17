# ============================================================
# Database class with all async methods
# SQLite dev, TimescaleDB prod. Create schema on init().
# Index on (device_id, ts DESC).
# ============================================================

import aiosqlite
import time
from typing import List, Optional, Dict, Any


class Database:
    def __init__(self, db_path: str = "iot_data.db"):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
        self._start_time = time.time()

    async def init(self):
        self.db = await aiosqlite.connect(self.db_path)
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self._create_schema()
        print(f"[DB] Initialized at {self.db_path}")

    async def _create_schema(self):
        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id TEXT NOT NULL,
                org_id TEXT,
                site_id TEXT,
                sensor TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                quality INTEGER DEFAULT 1,
                ts INTEGER NOT NULL,
                seq INTEGER,
                fw_version TEXT,
                gateway_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.db.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_device_ts
            ON readings(device_id, ts DESC)
        """)

        await self.db.execute("""
            CREATE TABLE IF NOT EXISTS device_status (
                device_id TEXT PRIMARY KEY,
                status TEXT,
                last_seen INTEGER,
                rssi INTEGER,
                heap_free INTEGER,
                uptime_s INTEGER,
                fw_version TEXT,
                org_id TEXT,
                site_id TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await self.db.commit()

    async def insert_reading(self, reading: Dict[str, Any]):
        await self.db.execute("""
            INSERT INTO readings (device_id, org_id, site_id, sensor, value, unit, quality, ts, seq, fw_version, gateway_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reading.get("device_id"),
            reading.get("org_id"),
            reading.get("site_id"),
            reading.get("sensor"),
            reading.get("value"),
            reading.get("unit"),
            reading.get("quality", 1),
            reading.get("ts"),
            reading.get("seq"),
            reading.get("fw_version"),
            reading.get("gateway_id")
        ))
        await self.db.commit()

    async def insert_readings_batch(self, readings: List[Dict[str, Any]]):
        for reading in readings:
            await self.insert_reading(reading)

    async def get_readings(
        self,
        device_id: Optional[str] = None,
        sensor: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        query = "SELECT * FROM readings WHERE 1=1"
        params = []

        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        if sensor:
            query += " AND sensor = ?"
            params.append(sensor)

        query += " ORDER BY ts DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_latest_reading(self, device_id: str, sensor: str) -> Optional[Dict[str, Any]]:
        cursor = await self.db.execute("""
            SELECT * FROM readings
            WHERE device_id = ? AND sensor = ?
            ORDER BY ts DESC LIMIT 1
        """, (device_id, sensor))
        row = await cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    async def get_latest_readings(self, device_id: Optional[str] = None) -> List[Dict[str, Any]]:
        query = """
            SELECT r1.* FROM readings r1
            INNER JOIN (
                SELECT device_id, sensor, MAX(ts) as max_ts
                FROM readings
        """
        params = []
        if device_id:
            query += " WHERE device_id = ?"
            params.append(device_id)
            query += " GROUP BY device_id, sensor"
        else:
            query += " GROUP BY device_id, sensor"
        query += """) r2 ON r1.device_id = r2.device_id AND r1.sensor = r2.sensor AND r1.ts = r2.max_ts
            ORDER BY r1.ts DESC"""

        cursor = await self.db.execute(query, params)
        rows = await cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def update_device_status(self, status: Dict[str, Any]):
        await self.db.execute("""
            INSERT OR REPLACE INTO device_status
            (device_id, status, last_seen, rssi, heap_free, uptime_s, fw_version, org_id, site_id, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (
            status.get("device_id"),
            status.get("status"),
            status.get("last_seen"),
            status.get("rssi"),
            status.get("heap_free"),
            status.get("uptime_s"),
            status.get("fw_version"),
            status.get("org_id"),
            status.get("site_id")
        ))
        await self.db.commit()

    async def get_devices(self) -> List[Dict[str, Any]]:
        cursor = await self.db.execute("SELECT * FROM device_status ORDER BY last_seen DESC")
        rows = await cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    async def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        cursor = await self.db.execute("SELECT * FROM device_status WHERE device_id = ?", (device_id,))
        row = await cursor.fetchone()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None

    async def get_readings_count(self) -> int:
        cursor = await self.db.execute("SELECT COUNT(*) FROM readings")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def get_devices_count(self) -> int:
        cursor = await self.db.execute("SELECT COUNT(*) FROM device_status")
        row = await cursor.fetchone()
        return row[0] if row else 0

    async def close(self):
        if self.db:
            await self.db.close()
            print("[DB] Closed")

    def get_uptime(self) -> float:
        return time.time() - self._start_time