import asyncio
import os
import time
import aiosqlite
from typing import Optional


DB_PATH = os.environ.get("DB_PATH", "edge_sense.db")


class Database:
    _conn: aiosqlite.Connection | None = None

    async def _get_conn(self) -> aiosqlite.Connection:
        if self._conn is None:
            self._conn = await aiosqlite.connect(DB_PATH)
            self._conn.row_factory = aiosqlite.Row
            await self._conn.execute("PRAGMA journal_mode=WAL")
            await self._conn.execute("PRAGMA foreign_keys=ON")
        return self._conn

    async def init(self):
        conn = await self._get_conn()
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS readings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id   TEXT    NOT NULL,
                org_id      TEXT,
                site_id     TEXT,
                sensor      TEXT    NOT NULL,
                value       REAL,
                unit        TEXT,
                quality     INTEGER DEFAULT 1,
                ts          INTEGER NOT NULL,
                seq         INTEGER,
                fw_version  TEXT,
                received_at INTEGER NOT NULL
            )
        """)
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_readings_device_ts
            ON readings (device_id, ts DESC)
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS devices (
                device_id   TEXT PRIMARY KEY,
                org_id      TEXT,
                site_id     TEXT,
                status      TEXT DEFAULT 'unknown',
                last_seen   INTEGER,
                fw_version  TEXT,
                rssi        INTEGER
            )
        """)
        await conn.commit()

    async def close(self):
        if self._conn is not None:
            await self._conn.close()
            self._conn = None

    async def insert_reading(self, payload: dict):
        conn = await self._get_conn()
        await conn.execute("""
            INSERT INTO readings
                (device_id, org_id, site_id, sensor, value, unit,
                 quality, ts, seq, fw_version, received_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            payload.get("device_id"),
            payload.get("org_id", ""),
            payload.get("site_id", ""),
            payload.get("sensor"),
            payload.get("value"),
            payload.get("unit", ""),
            payload.get("quality", 1),
            payload.get("ts", int(time.time() * 1000)),
            payload.get("seq"),
            payload.get("fw_version"),
            int(time.time() * 1000),
        ))
        await conn.commit()

    async def upsert_device(self, payload: dict):
        conn = await self._get_conn()
        await conn.execute("""
            INSERT INTO devices (device_id, org_id, site_id, status, last_seen, fw_version, rssi)
            VALUES (?,?,?,?,?,?,?)
            ON CONFLICT(device_id) DO UPDATE SET
                status     = excluded.status,
                last_seen  = excluded.last_seen,
                fw_version = excluded.fw_version,
                rssi       = excluded.rssi
        """, (
            payload.get("device_id"),
            payload.get("org_id", ""),
            payload.get("site_id", ""),
            payload.get("status", "online"),
            payload.get("ts", int(time.time() * 1000)),
            payload.get("fw_version"),
            payload.get("rssi"),
        ))
        await conn.commit()

    async def get_readings(
        self,
        device_id: Optional[str] = None,
        sensor:    Optional[str] = None,
        limit:     int           = 200,
        since_ts:  Optional[int] = None,
    ) -> list[dict]:
        query = "SELECT device_id, sensor, value, unit, quality, ts, fw_version FROM readings WHERE 1=1"
        params = []
        if device_id:
            query += " AND device_id = ?"
            params.append(device_id)
        if sensor:
            query += " AND sensor = ?"
            params.append(sensor)
        if since_ts:
            query += " AND ts >= ?"
            params.append(since_ts)
        query += " ORDER BY ts DESC LIMIT ?"
        params.append(min(limit, 5000))

        conn = await self._get_conn()
        async with conn.execute(query, params) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_latest_readings(self) -> list[dict]:
        query = """
            SELECT r.device_id, r.sensor, r.value, r.unit, r.quality, r.ts
            FROM readings r
            INNER JOIN (
                SELECT device_id, sensor, MAX(ts) AS max_ts
                FROM readings GROUP BY device_id, sensor
            ) latest
              ON r.device_id = latest.device_id
             AND r.sensor    = latest.sensor
             AND r.ts        = latest.max_ts
            ORDER BY r.device_id, r.sensor
        """
        conn = await self._get_conn()
        async with conn.execute(query) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_devices(self) -> list[dict]:
        conn = await self._get_conn()
        async with conn.execute(
            "SELECT device_id, org_id, site_id, status, last_seen, fw_version, rssi "
            "FROM devices ORDER BY last_seen DESC"
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def device_count(self) -> int:
        conn = await self._get_conn()
        async with conn.execute("SELECT COUNT(*) FROM devices") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0

    async def reading_count(self) -> int:
        conn = await self._get_conn()
        async with conn.execute("SELECT COUNT(*) FROM readings") as cur:
            row = await cur.fetchone()
            return row[0] if row else 0


db = Database()
