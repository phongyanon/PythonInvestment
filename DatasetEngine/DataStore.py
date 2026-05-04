"""
SQLite access layer for OHLCV (Dataset) and closed trades (TradeLog).
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple, Union

Row = Dict[str, Any]


class DataStore:
    """Connect to SQLite, run CRUD for Dataset / TradeLog, or inject arbitrary SQL."""

    def __init__(
        self,
        db_path: Union[str, Path],
        *,
        initSchema: bool = False,
    ) -> None:
        self.db_path = Path(db_path)
        self._conn: Optional[sqlite3.Connection] = None
        if initSchema:
            self.initSchema()

    # --- connection lifecycle ---

    @property
    def connection(self) -> sqlite3.Connection:
        return self.connect()

    def connect(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.row_factory = sqlite3.Row
            self._conn.execute("PRAGMA foreign_keys = ON;")
        return self._conn

    def close(self) -> None:
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "DataStore":
        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._conn is None:
            return
        if exc_type is not None:
            self._conn.rollback()
        else:
            self._conn.commit()
        self.close()

    def commit(self) -> None:
        if self._conn is not None:
            self._conn.commit()

    def rollback(self) -> None:
        if self._conn is not None:
            self._conn.rollback()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit on success, rollback on exception."""
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    # --- schema ---

    def initSchema(self) -> None:
        self.executeScript(
            """
            CREATE TABLE IF NOT EXISTS Dataset (
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                adjClose REAL,
                volume REAL,
                PRIMARY KEY (symbol, timestamp)
            );

            CREATE INDEX IF NOT EXISTS idx_dataset_symbol_timestamp
                ON Dataset (symbol, timestamp);

            CREATE TABLE IF NOT EXISTS TradeLog (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product TEXT NOT NULL,
                side TEXT NOT NULL CHECK (side IN ('long', 'short')),
                entry_timestamp TIMESTAMP NOT NULL,
                exit_timestamp TIMESTAMP NOT NULL,
                entry_price REAL NOT NULL,
                exit_price REAL NOT NULL,
                result TEXT NOT NULL CHECK (result IN ('TP', 'SL', 'BE')),
                tp_pips REAL NOT NULL,
                sl_pips REAL NOT NULL,
                rr REAL GENERATED ALWAYS AS (tp_pips / NULLIF(sl_pips, 0)) STORED,
                real_tp_pips REAL NOT NULL,
                actual_rr REAL GENERATED ALWAYS AS (real_tp_pips / NULLIF(sl_pips, 0)) STORED,
                entry_strategy TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                entry_to_exit_minutes REAL NOT NULL,
                percent_risk REAL NOT NULL,
                pnl_percent REAL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE INDEX IF NOT EXISTS idx_tradelog_product_exit
                ON TradeLog (product, exit_timestamp);
            """
        )

    # --- inject SQL (parameterized) ---

    def execute(
        self,
        sql: str,
        params: Union[Sequence[Any], Tuple] = (),
    ) -> sqlite3.Cursor:
        """Single statement. Use ? placeholders; never concatenate user input into sql."""
        return self.connection.execute(sql, tuple(params))

    def executeMany(self, sql: str, seq_of_params: Sequence[Sequence[Any]]) -> None:
        self.connection.executemany(sql, seq_of_params)

    def executeScript(self, script: str) -> None:
        """Multiple statements in one string (migrations, PRAGMA batches)."""
        self.connection.executescript(script)
        self.commit()

    def fetchAll(self, sql: str, params: Union[Sequence[Any], Tuple] = ()) -> List[Row]:
        cur = self.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]

    def fetchOne(self, sql: str, params: Union[Sequence[Any], Tuple] = ()) -> Optional[Row]:
        cur = self.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row is not None else None

    # --- Dataset CRUD ---

    def datasetUpsertBar(
        self,
        symbol: str,
        timestamp: str,
        open_: float,
        high: float,
        low: float,
        close: float,
        adjClose: float,
        volume: float,
    ) -> None:
        self.execute(
            """
            INSERT INTO Dataset (symbol, timestamp, open, high, low, close, adjClose, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, timestamp) DO UPDATE SET
                open=excluded.open,
                high=excluded.high,
                low=excluded.low,
                close=excluded.close,
                adjClose=excluded.adjClose,
                volume=excluded.volume;
            """,
            (symbol, timestamp, open_, high, low, close, adjClose, volume),
        )

    def datasetGetBars(
        self,
        symbol: str,
        start_ts: Optional[str] = None,
        end_ts: Optional[str] = None,
        *,
        limit: Optional[int] = None,
    ) -> List[Row]:
        clauses: List[str] = ["symbol = ?"]
        params: List[Any] = [symbol]
        if start_ts is not None:
            clauses.append("timestamp >= ?")
            params.append(start_ts)
        if end_ts is not None:
            clauses.append("timestamp <= ?")
            params.append(end_ts)
        sql = (
            "SELECT * FROM Dataset WHERE "
            + " AND ".join(clauses)
            + " ORDER BY timestamp ASC"
        )
        if limit is not None:
            sql += f" LIMIT {int(limit)}"
        return self.fetchAll(sql, tuple(params))

    def datasetDeleteBar(self, symbol: str, timestamp: str) -> int:
        cur = self.execute(
            "DELETE FROM Dataset WHERE symbol = ? AND timestamp = ?",
            (symbol, timestamp),
        )
        return cur.rowcount

    def datasetDeleteSymbol(self, symbol: str) -> int:
        cur = self.execute("DELETE FROM Dataset WHERE symbol = ?", (symbol,))
        return cur.rowcount

    # --- TradeLog CRUD ---

    def tradelogCreate(
        self,
        *,
        product: str,
        side: str,
        entry_timestamp: str,
        exit_timestamp: str,
        entry_price: float,
        exit_price: float,
        result: str,
        tp_pips: float,
        sl_pips: float,
        real_tp_pips: float,
        entry_strategy: str,
        timeframe: str,
        entry_to_exit_minutes: float,
        percent_risk: float,
        pnl_percent: Optional[float] = None,
        notes: Optional[str] = None,
    ) -> int:
        """Insert a trade; ``rr`` and ``actual_rr`` are computed by SQLite."""
        cur = self.execute(
            """
            INSERT INTO TradeLog (
                product, side, entry_timestamp, exit_timestamp,
                entry_price, exit_price, result,
                tp_pips, sl_pips, real_tp_pips,
                entry_strategy, timeframe, entry_to_exit_minutes,
                percent_risk, pnl_percent, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                product,
                side,
                entry_timestamp,
                exit_timestamp,
                entry_price,
                exit_price,
                result,
                tp_pips,
                sl_pips,
                real_tp_pips,
                entry_strategy,
                timeframe,
                entry_to_exit_minutes,
                percent_risk,
                pnl_percent,
                notes,
            ),
        )
        return int(cur.lastrowid)

    def getTradeLog(self, trade_id: int) -> Optional[Row]:
        return self.fetchOne("SELECT * FROM TradeLog WHERE id = ?", (trade_id,))

    def tradelogList(
        self,
        product: Optional[str] = None,
        *,
        limit: int = 100,
        order: str = "DESC",
    ) -> List[Row]:
        order = "DESC" if order.upper() == "DESC" else "ASC"
        if product is None:
            sql = f"SELECT * FROM TradeLog ORDER BY id {order} LIMIT ?"
            return self.fetchAll(sql, (limit,))
        sql = f"SELECT * FROM TradeLog WHERE product = ? ORDER BY id {order} LIMIT ?"
        return self.fetchAll(sql, (product, limit))

    def tradelogUpdate(
        self,
        trade_id: int,
        *,
        exit_price: Optional[float] = None,
        result: Optional[str] = None,
        tp_pips: Optional[float] = None,
        sl_pips: Optional[float] = None,
        real_tp_pips: Optional[float] = None,
        pnl_percent: Optional[float] = None,
        notes: Optional[str] = None,
        entry_timestamp: Optional[str] = None,
        exit_timestamp: Optional[str] = None,
        entry_strategy: Optional[str] = None,
        timeframe: Optional[str] = None,
        entry_to_exit_minutes: Optional[float] = None,
        percent_risk: Optional[float] = None,
    ) -> int:
        fields: List[str] = []
        params: List[Any] = []
        if exit_price is not None:
            fields.append("exit_price = ?")
            params.append(exit_price)
        if result is not None:
            fields.append("result = ?")
            params.append(result)
        if tp_pips is not None:
            fields.append("tp_pips = ?")
            params.append(tp_pips)
        if sl_pips is not None:
            fields.append("sl_pips = ?")
            params.append(sl_pips)
        if real_tp_pips is not None:
            fields.append("real_tp_pips = ?")
            params.append(real_tp_pips)
        if pnl_percent is not None:
            fields.append("pnl_percent = ?")
            params.append(pnl_percent)
        if notes is not None:
            fields.append("notes = ?")
            params.append(notes)
        if entry_timestamp is not None:
            fields.append("entry_timestamp = ?")
            params.append(entry_timestamp)
        if exit_timestamp is not None:
            fields.append("exit_timestamp = ?")
            params.append(exit_timestamp)
        if entry_strategy is not None:
            fields.append("entry_strategy = ?")
            params.append(entry_strategy)
        if timeframe is not None:
            fields.append("timeframe = ?")
            params.append(timeframe)
        if entry_to_exit_minutes is not None:
            fields.append("entry_to_exit_minutes = ?")
            params.append(entry_to_exit_minutes)
        if percent_risk is not None:
            fields.append("percent_risk = ?")
            params.append(percent_risk)
        if not fields:
            return 0
        fields.append("updated_at = CURRENT_TIMESTAMP")
        params.append(trade_id)
        sql = "UPDATE TradeLog SET " + ", ".join(fields) + " WHERE id = ?"
        cur = self.execute(sql, tuple(params))
        return cur.rowcount

    def tradelogDelete(self, trade_id: int) -> int:
        cur = self.execute("DELETE FROM TradeLog WHERE id = ?", (trade_id,))
        return cur.rowcount
