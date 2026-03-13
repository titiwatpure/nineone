# -*- coding: utf-8 -*-

"""Fuel repository (SQLite)

เก็บข้อมูลการเติมน้ำมันเชื้อเพลิงของเครื่องจักร และช่วยสรุปรายวัน/เดือน/ปี
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping


def _to_iso_date(value: Any) -> str:
    if value is None:
        raise ValueError("วันที่ เป็นค่าว่าง")

    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()

    text = str(value).strip()
    if not text:
        raise ValueError("วันที่ เป็นค่าว่าง")

    # รองรับ YYYY-MM-DD เป็นหลัก และลอง parse แบบทั่วไป
    try:
        return datetime.fromisoformat(text[:10]).date().isoformat()
    except Exception:
        pass

    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except Exception:
            continue

    raise ValueError(f"รูปแบบวันที่ไม่ถูกต้อง: {text}")


def _to_float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text == "":
        return None
    try:
        return float(text)
    except Exception:
        return None


def _to_text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


@dataclass(frozen=True)
class FuelEntry:
    entry_date: str
    machine_code: str
    liters: float
    price_per_liter: float | None = None
    amount: float | None = None
    receipt_no: str | None = None
    driver: str | None = None
    recorder: str | None = None
    vendor: str | None = None
    location: str | None = None
    hour_meter: float | None = None
    remark: str | None = None


class FuelRepository:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fuel_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_date TEXT NOT NULL,               -- YYYY-MM-DD
                    machine_code TEXT NOT NULL,
                    liters REAL NOT NULL,
                    price_per_liter REAL,
                    amount REAL,
                    receipt_no TEXT,
                    driver TEXT,
                    recorder TEXT,
                    vendor TEXT,
                    location TEXT,
                    hour_meter REAL,
                    remark TEXT,
                    created_at TEXT NOT NULL DEFAULT (datetime('now'))
                );
                """
            )

            # กันซ้ำเมื่อมีเลขที่ใบเสร็จ/ใบเติม
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_fuel_machine_receipt
                ON fuel_entries(machine_code, receipt_no)
                WHERE receipt_no IS NOT NULL AND receipt_no <> '';
                """
            )

            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS ix_fuel_entry_date
                ON fuel_entries(entry_date);
                """
            )

    def normalize_entry(self, raw: Mapping[Any, Any]) -> FuelEntry:
        entry_date = _to_iso_date(raw.get("วันที่") or raw.get(
            "entry_date") or raw.get("date"))
        machine_code = str(raw.get("รหัสเครื่องจักร")
                           or raw.get("machine_code") or "").strip()
        if not machine_code:
            raise ValueError("รหัสเครื่องจักร เป็นค่าว่าง")

        liters = _to_float_or_none(
            raw.get("ปริมาณ(ลิตร)") or raw.get("liters"))
        if liters is None or liters <= 0:
            raise ValueError("ปริมาณ(ลิตร) ต้องมากกว่า 0")

        price_per_liter = _to_float_or_none(
            raw.get("ราคา/ลิตร(บาท)") or raw.get("price_per_liter"))
        amount = _to_float_or_none(
            raw.get("ยอดเงิน(บาท)") or raw.get("amount"))

        # priority: amount > liters*price
        if amount is None and price_per_liter is not None:
            amount = round(liters * price_per_liter, 4)
        if price_per_liter is None and amount is not None:
            price_per_liter = round(amount / liters, 6) if liters else None

        return FuelEntry(
            entry_date=entry_date,
            machine_code=machine_code,
            liters=float(liters),
            price_per_liter=price_per_liter,
            amount=amount,
            receipt_no=_to_text_or_none(raw.get("เลขที่ใบเสร็จ") or raw.get(
                "เลขที่ใบเติม") or raw.get("receipt_no")),
            driver=_to_text_or_none(raw.get("ผู้ขับ") or raw.get("driver")),
            recorder=_to_text_or_none(
                raw.get("ผู้บันทึก") or raw.get("recorder")),
            vendor=_to_text_or_none(
                raw.get("ปั๊ม/ผู้ขาย") or raw.get("vendor")),
            location=_to_text_or_none(
                raw.get("สถานที่เติม") or raw.get("location")),
            hour_meter=_to_float_or_none(
                raw.get("ชั่วโมงเครื่อง") or raw.get("hour_meter")),
            remark=_to_text_or_none(raw.get("หมายเหตุ") or raw.get("remark")),
        )

    def _exists_duplicate_no_receipt(self, conn: sqlite3.Connection, entry: FuelEntry) -> bool:
        # กรณีไม่มี receipt_no: ใช้ key ง่าย ๆ กันซ้ำแบบพื้นฐาน
        liters = round(entry.liters, 3)
        amount = None if entry.amount is None else round(entry.amount, 2)
        row = conn.execute(
            """
            SELECT id
            FROM fuel_entries
            WHERE entry_date = ?
              AND machine_code = ?
              AND ROUND(liters, 3) = ?
              AND ( (amount IS NULL AND ? IS NULL) OR (ROUND(amount, 2) = ?) )
            LIMIT 1;
            """,
            (entry.entry_date, entry.machine_code, liters, amount, amount),
        ).fetchone()
        return row is not None

    def add_entry(self, entry: FuelEntry) -> tuple[bool, str]:
        """เพิ่มรายการเติมน้ำมัน

        คืนค่า (inserted, message)
        """

        with self._connect() as conn:
            if not entry.receipt_no and self._exists_duplicate_no_receipt(conn, entry):
                return False, "พบรายการซ้ำ (ไม่มีเลขที่ใบเสร็จ) จึงข้าม"

            try:
                conn.execute(
                    """
                    INSERT INTO fuel_entries (
                        entry_date, machine_code, liters, price_per_liter, amount,
                        receipt_no, driver, recorder, vendor, location, hour_meter, remark
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        entry.entry_date,
                        entry.machine_code,
                        entry.liters,
                        entry.price_per_liter,
                        entry.amount,
                        entry.receipt_no,
                        entry.driver,
                        entry.recorder,
                        entry.vendor,
                        entry.location,
                        entry.hour_meter,
                        entry.remark,
                    ),
                )
                return True, "บันทึกสำเร็จ"
            except sqlite3.IntegrityError:
                return False, "พบเลขที่ใบเสร็จซ้ำ จึงข้าม"

    def import_entries(self, entries: Iterable[FuelEntry]) -> dict[str, Any]:
        inserted = 0
        skipped = 0
        errors: list[str] = []

        for idx, entry in enumerate(entries, start=1):
            try:
                ok, _msg = self.add_entry(entry)
                if ok:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as exc:
                errors.append(f"แถวที่ {idx}: {exc}")

        return {"inserted": inserted, "skipped": skipped, "errors": errors}

    def totals_for_range(self, start: str, end: str) -> dict[str, Any]:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS entries,
                    COALESCE(SUM(liters), 0) AS liters,
                    COALESCE(SUM(COALESCE(amount, liters * price_per_liter)), 0) AS amount
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?;
                """,
                (start, end),
            ).fetchone()
            return {"entries": int(row["entries"]), "liters": float(row["liters"]), "amount": float(row["amount"])}

    def top_machine_for_range(self, start: str, end: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT machine_code,
                       COALESCE(SUM(liters), 0) AS liters,
                       COALESCE(SUM(COALESCE(amount, liters * price_per_liter)), 0) AS amount
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?
                GROUP BY machine_code
                ORDER BY liters DESC
                LIMIT 1;
                """,
                (start, end),
            ).fetchone()
            if row is None:
                return None
            return {"machine_code": row["machine_code"], "liters": float(row["liters"]), "amount": float(row["amount"])}

    def summary_daily(self, start: str, end: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT entry_date AS date,
                       COALESCE(SUM(liters), 0) AS liters,
                       COALESCE(SUM(COALESCE(amount, liters * price_per_liter)), 0) AS amount,
                       COUNT(*) AS entries
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?
                GROUP BY entry_date
                ORDER BY entry_date;
                """,
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]

    def list_details(self, start: str, end: str) -> list[dict[str, Any]]:
        """ดึงรายละเอียดรายการเติมน้ำมัน (ใช้สำหรับส่งออก)"""

        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    entry_date AS วันที่,
                    machine_code AS รหัสเครื่องจักร,
                    liters AS [ปริมาณ(ลิตร)],
                    price_per_liter AS [ราคา/ลิตร(บาท)],
                    amount AS [ยอดเงิน(บาท)],
                    receipt_no AS เลขที่ใบเสร็จ,
                    driver AS ผู้ขับ,
                    recorder AS ผู้บันทึก,
                    vendor AS [ปั๊ม/ผู้ขาย],
                    location AS สถานที่เติม,
                    hour_meter AS ชั่วโมงเครื่อง,
                    remark AS หมายเหตุ
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?
                ORDER BY entry_date, machine_code, id;
                """,
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]

    def summary_monthly(self, start: str, end: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT strftime('%Y-%m', entry_date) AS month,
                       COALESCE(SUM(liters), 0) AS liters,
                       COALESCE(SUM(COALESCE(amount, liters * price_per_liter)), 0) AS amount,
                       COUNT(*) AS entries
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?
                GROUP BY strftime('%Y-%m', entry_date)
                ORDER BY month;
                """,
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]

    def summary_yearly(self, start: str, end: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT strftime('%Y', entry_date) AS year,
                       COALESCE(SUM(liters), 0) AS liters,
                       COALESCE(SUM(COALESCE(amount, liters * price_per_liter)), 0) AS amount,
                       COUNT(*) AS entries
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?
                GROUP BY strftime('%Y', entry_date)
                ORDER BY year;
                """,
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]

    def summary_by_machine(self, start: str, end: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT machine_code,
                       COALESCE(SUM(liters), 0) AS liters,
                       COALESCE(SUM(COALESCE(amount, liters * price_per_liter)), 0) AS amount,
                       COUNT(*) AS entries
                FROM fuel_entries
                WHERE entry_date BETWEEN ? AND ?
                GROUP BY machine_code
                ORDER BY liters DESC, machine_code;
                """,
                (start, end),
            ).fetchall()
            return [dict(r) for r in rows]
