"""
SurrealDB backend for DecisionMemory Protocol.
Drop-in replacement for the SQLite Database class.
Tables are prefixed with tm_ to coexist with other data in the same namespace.

Set DECISIONMEMORY_BACKEND=surreal to activate via db_factory.
No encryption at rest.
"""

import json
import logging
import os
import re
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .exceptions import DecisionMemoryDBError

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# SurrealConnection — lightweight wrapper for ChainBuilder compatibility
# ---------------------------------------------------------------------------

class SurrealRow:
    """Dict-like row that also supports positional indexing for tuple unpacking."""

    def __init__(self, data: dict, columns: list[str]):
        self._data = data
        self._columns = columns

    def __getitem__(self, key):
        if isinstance(key, int):
            return self._data[self._columns[key]]
        return self._data[key]

    def __iter__(self):
        return iter(self._data[c] for c in self._columns)

    def __len__(self):
        return len(self._columns)

    def __repr__(self):
        return f"SurrealRow({self._data})"

    def keys(self):
        return self._data.keys()


class SurrealCursor:
    """Mimics sqlite3 cursor with fetchone/fetchall."""

    def __init__(self, rows: list[SurrealRow]):
        self._rows = rows
        self._idx = 0
        self.rowcount = len(rows)

    def fetchone(self):
        if self._idx < len(self._rows):
            row = self._rows[self._idx]
            self._idx += 1
            return row
        return None

    def fetchall(self):
        return self._rows[self._idx:]

    @property
    def lastrowid(self):
        return None


def _convert_record_ids(obj):
    """Recursively convert SurrealDB RecordID objects to strings."""
    from surrealdb import RecordID as _RecordID  # noqa: F811
    if isinstance(obj, _RecordID):
        return f"{obj.table_name}:{obj.id}"
    if isinstance(obj, dict):
        return {k: _convert_record_ids(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert_record_ids(i) for i in obj]
    return obj


class SurrealConnection:
    """Wraps a SurrealDB connection to mimic sqlite3.Connection for ChainBuilder.

    Handles the specific SQL patterns used by ChainBuilder:
    - SELECT cols FROM table WHERE ... ORDER BY ... LIMIT N
    - INSERT INTO table (cols) VALUES (...)
    - INSERT OR REPLACE INTO table (cols) VALUES (...)
    """

    def __init__(self, surreal_db):
        self._db = surreal_db
        self.row_factory = None  # Ignored, we always return SurrealRow

    @staticmethod
    def _bind(bindings: dict[str, Any], value: Any) -> str:
        name = f"p{len(bindings)}"
        bindings[name] = value
        return f"${name}"

    def _parse_condition(
        self, cond_str: str, params: tuple, bindings: dict[str, Any]
    ) -> str:
        """Convert a SQL WHERE condition to SurreQL."""
        cond = cond_str.strip()

        # col >= ? or col <= ? or col < ? or col > ?
        m = re.fullmatch(r'(\w+)\s*(>=|<=|<|>)\s*\?', cond)
        if m:
            col, op = m.group(1), m.group(2)
            return f"{col} {op} {self._bind(bindings, params[0])}"

        # col = ?
        m = re.fullmatch(r'(\w+)\s*=\s*\?', cond)
        if m:
            col = m.group(1)
            return f"{col} = {self._bind(bindings, params[0])}"

        raise ValueError(f"Unsupported compatibility WHERE condition: {cond!r}")

    def _translate_sql(self, sql: str, params: tuple) -> tuple[str, dict[str, Any]]:
        """Translate a SQL query to SurreQL. Handles ChainBuilder's patterns."""
        sql = sql.strip()
        bindings: dict[str, Any] = {}

        # INSERT OR REPLACE INTO table (cols) VALUES (?, ?, ...)
        m = re.fullmatch(
            r'INSERT\s+OR\s+REPLACE\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)',
            sql, re.IGNORECASE
        )
        if m:
            table = m.group(1)
            cols = [c.strip() for c in m.group(2).split(',')]
            placeholders = [p.strip() for p in m.group(3).split(',')]
            if placeholders != ['?'] * len(cols) or len(params) != len(cols):
                raise ValueError("INSERT columns, placeholders, and params must match")
            sets = []
            for i, col in enumerate(cols):
                val = params[i] if i < len(params) else None
                sets.append(f"{col} = {self._bind(bindings, val)}")
            return f"UPSERT tm_{table} SET {', '.join(sets)}", bindings

        # INSERT INTO table (cols) VALUES (?, ?, ...)
        m = re.fullmatch(
            r'INSERT\s+INTO\s+(\w+)\s*\(([^)]+)\)\s*VALUES\s*\(([^)]+)\)',
            sql, re.IGNORECASE
        )
        if m:
            table = m.group(1)
            cols = [c.strip() for c in m.group(2).split(',')]
            placeholders = [p.strip() for p in m.group(3).split(',')]
            if placeholders != ['?'] * len(cols) or len(params) != len(cols):
                raise ValueError("INSERT columns, placeholders, and params must match")
            sets = []
            for i, col in enumerate(cols):
                val = params[i] if i < len(params) else None
                sets.append(f"{col} = {self._bind(bindings, val)}")
            return f"CREATE tm_{table} SET {', '.join(sets)}", bindings

        # SELECT ... FROM table [WHERE ...] [ORDER BY ...] [LIMIT N]
        m = re.match(r'SELECT\s+(.+?)\s+FROM\s+(\w+)(.*)', sql, re.IGNORECASE)
        if m:
            select_cols = m.group(1).strip()
            if select_cols != '*' and not re.fullmatch(
                r'\w+(?:\s*,\s*\w+)*', select_cols
            ):
                raise ValueError("Unsupported SELECT projection")
            table = m.group(2)
            rest = m.group(3).strip()

            # Extract WHERE clause
            where_match = re.search(r'WHERE\s+(.+?)(?:ORDER\s+BY|LIMIT|$)', rest, re.IGNORECASE)
            where_clause = where_match.group(1).strip() if where_match else None

            # Extract ORDER BY
            order_match = re.search(r'ORDER\s+BY\s+(.+?)(?:LIMIT|$)', rest, re.IGNORECASE)
            order_clause = order_match.group(1).strip() if order_match else None
            if order_clause and not re.fullmatch(
                r'\w+(?:\s+(?:ASC|DESC))?(?:\s*,\s*\w+(?:\s+(?:ASC|DESC))?)*',
                order_clause,
                re.IGNORECASE,
            ):
                raise ValueError("Unsupported ORDER BY clause")

            # Extract LIMIT
            limit_match = re.search(r'LIMIT\s+(\d+)', rest, re.IGNORECASE)
            limit_val = int(limit_match.group(1)) if limit_match else None

            # Parse WHERE conditions
            param_idx = 0
            surreal_conds = []
            if where_clause and where_clause != '1=1':
                # Split on AND (not inside parens)
                conds = re.split(r'\s+AND\s+', where_clause, flags=re.IGNORECASE)
                for cond in conds:
                    n_qmarks = cond.count('?')
                    if n_qmarks > 0:
                        cond_params = tuple(params[param_idx:param_idx + n_qmarks])
                        param_idx += n_qmarks
                        surreal_conds.append(
                            self._parse_condition(cond, cond_params, bindings)
                        )
                    else:
                        if not re.fullmatch(r'\w+\s*=\s*(?:NONE|true|false|\d+)', cond):
                            raise ValueError(
                                f"Unsupported literal WHERE condition: {cond!r}"
                            )
                        surreal_conds.append(cond)

            # Build SurreQL — always SELECT * because SurrealDB requires
            # ORDER BY columns to appear in the SELECT projection.
            # Column filtering is done in execute() based on the original SQL.
            q = f"SELECT * FROM tm_{table}"
            if surreal_conds:
                q += " WHERE " + " AND ".join(surreal_conds)
            if order_clause:
                # Convert ORDER BY: "col DESC" → "col DESC", "col ASC" → "col ASC"
                q += " ORDER BY " + order_clause
            if limit_val:
                q += f" LIMIT {limit_val}"

            return q, bindings

        # DELETE FROM table
        m = re.fullmatch(r'DELETE\s+FROM\s+(\w+)', sql, re.IGNORECASE)
        if m:
            table = m.group(1)
            return f"DELETE FROM tm_{table}", bindings

        # UPDATE table SET ... WHERE ...
        m = re.match(r'UPDATE\s+(\w+)\s+SET\s+(.+?)(?:\s+WHERE\s+(.+))?$', sql, re.IGNORECASE)
        if m:
            table = m.group(1)
            set_part = m.group(2).strip()
            where_part = m.group(3).strip() if m.group(3) else None

            # Parse SET assignments
            param_idx = 0
            set_assigns = []
            # Split on comma (but not inside function calls)
            assignments = re.split(r',\s*(?![^()]*\))', set_part)
            for assign in assignments:
                assign = assign.strip()
                if '?' in assign:
                    # "col = ?" pattern
                    m2 = re.match(r'(\w+)\s*=\s*\?', assign)
                    if m2:
                        col = m2.group(1)
                        val = params[param_idx]
                        param_idx += 1
                        set_assigns.append(
                            f"{col} = {self._bind(bindings, val)}"
                        )
                else:
                    # "col = col + ?" or "col = value"
                    m2 = re.match(r'(\w+)\s*=\s*(.+)', assign)
                    if m2:
                        col = m2.group(1)
                        expr = m2.group(2).strip()
                        if '?' in expr:
                            val = params[param_idx]
                            param_idx += 1
                            if expr.count('?') != 1 or not re.fullmatch(
                                r'\w+\s*[+-]\s*\?', expr
                            ):
                                raise ValueError(
                                    f"Unsupported compatibility SET expression: {expr!r}"
                                )
                            expr = expr.replace('?', self._bind(bindings, val))
                        elif not re.fullmatch(r'\w+', expr):
                            raise ValueError(
                                f"Unsupported literal SET expression: {expr!r}"
                            )
                        set_assigns.append(f"{col} = {expr}")

            # Parse WHERE
            where_surreal = ""
            if where_part:
                n_qmarks = where_part.count('?')
                cond_params = tuple(params[param_idx:param_idx + n_qmarks])
                param_idx += n_qmarks
                where_surreal = " WHERE " + self._parse_condition(
                    where_part, cond_params, bindings
                )

            return (
                f"UPDATE tm_{table} SET {', '.join(set_assigns)}{where_surreal}",
                bindings,
            )

        raise ValueError("Unsupported SQL for Surreal compatibility backend")

    def execute(self, sql: str, params=()) -> SurrealCursor:
        """Execute SQL translated to SurreQL, return SurrealCursor."""
        if isinstance(params, dict):
            raise ValueError("Named SQL params are unsupported by compatibility layer")

        if not isinstance(params, (tuple, list)):
            params = tuple(params) if params else ()

        surrealql, bindings = self._translate_sql(sql, tuple(params))
        logger.debug("SurrealQL: %s", surrealql)

        try:
            result = self._db.query(surrealql, bindings)
            if not isinstance(result, list):
                result = result if result else []

            # Convert RecordIDs
            result = [_convert_record_ids(r) for r in result]

            # Build rows for ChainBuilder — preserve column order from SQL
            if result:
                # Extract requested columns from original SQL to preserve order
                select_match = re.match(
                    r'SELECT\s+(.+?)\s+FROM', sql, re.IGNORECASE
                )
                if select_match:
                    raw_cols = [
                        c.strip() for c in select_match.group(1).split(',')
                    ]
                    if raw_cols != ['*']:
                        cols = [c for c in raw_cols if c in result[0]]
                    else:
                        cols = list(result[0].keys())
                else:
                    cols = list(result[0].keys())
                rows = [SurrealRow(r, cols) for r in result]
            else:
                rows = []
            return SurrealCursor(rows)
        except Exception as e:
            logger.error("SurrealQL error: %s — query: %s", e, surrealql)
            raise

    def commit(self):
        """No-op — SurrealDB HTTP auto-commits."""
        pass

    def rollback(self):
        """No-op — SurrealDB HTTP auto-commits."""
        pass

    def close(self):
        """No-op."""
        pass


# ---------------------------------------------------------------------------
# SurrealDatabase — full replacement for the SQLite Database class
# ---------------------------------------------------------------------------

class SurrealDatabase:
    """SurrealDB-backed database manager for DecisionMemory.

    Tables use tm_ prefix to coexist with database-manager tables
    (concept, ocr_data, memory, etc.) in the same namespace.
    """

    def __init__(self, db_path: str | None = None):
        """Initialize SurrealDB connection.

        Args:
            db_path: Ignored (kept for API compatibility with Database())
        """
        try:
            from surrealdb import Surreal
        except ImportError:
            raise ImportError(
                'surrealdb package required for SurrealDB backend. '
                'Install with: pip install decisionmemory-protocol[surreal]'
            )

        host = os.environ.get("SURREAL_HOST", "http://localhost")
        port = os.environ.get("SURREAL_PORT", "8000")
        user = os.environ.get("SURREAL_USER", "")
        passwd = os.environ.get("SURREAL_PASS", "")
        ns = os.environ.get("SURREAL_NS", "antigravity")
        db_name = os.environ.get("SURREAL_DB", "unified")

        url = f"{host}:{port}"
        self._surreal = Surreal(url)
        # Authenticate when credentials are provided.
        # SurrealDB v2 requires auth by default; set SURREAL_USER + SURREAL_PASS.
        # Leave both empty for legacy unauthenticated deployments (SurrealDB v1).
        if user and passwd:
            self._surreal.signin({"username": user, "password": passwd})
        elif user or passwd:
            raise ValueError(
                "Both SURREAL_USER and SURREAL_PASS must be set, or neither"
            )
        self._surreal.use(ns, db_name)

    def _q(self, query: str, params=None) -> list[dict]:
        """Execute a SurreQL query, return list of dicts with RecordIDs converted.

        Args:
            query: SurreQL query string (may contain $param placeholders)
            params: Either a dict of named params, a list of positional params,
                    or None for no params.
        """
        try:
            result = self._surreal.query(query, params)
            if not isinstance(result, list):
                result = []
            return [_convert_record_ids(r) for r in result]
        except Exception as e:
            raise DecisionMemoryDBError(f"SurrealDB query failed: {e}") from e

    def _get_connection(self):
        """Return a SurrealConnection wrapper for ChainBuilder compatibility."""
        return SurrealConnection(self._surreal)

    @contextmanager
    def get_connection(self):
        """Context manager yielding a SurrealConnection. For ChainBuilder compat."""
        conn = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def _serialize_json(self, data: dict, key: str):
        """Serialize a dict/list value to JSON string for storage."""
        if key in data and isinstance(data[key], (dict, list)):
            data[key] = json.dumps(data[key])

    def _escape(self, val: Any) -> str:
        """Escape a value for SurreQL string interpolation.

        DEPRECATED: Use parameterized queries ($param) instead.
        Kept only for SurrealConnection SQL-to-SurreQL translation fallback.
        """
        if val is None:
            return "NONE"
        if isinstance(val, bool):
            return "true" if val else "false"
        if isinstance(val, (int, float)):
            return str(val)
        if isinstance(val, (dict, list)):
            return json.dumps(val)
        return "'" + str(val).replace("\\", "\\\\").replace("'", "\\'") + "'"

    def _escape_dict(self, data: dict) -> str:
        """Build SurreQL SET clause from a dict.

        DEPRECATED: Use CONTENT with bound params instead.
        Kept only for SurrealConnection SQL-to-SurreQL translation fallback.
        """
        parts = []
        for k, v in data.items():
            if v is None:
                parts.append(f"{k} = NONE")
            elif isinstance(v, bool):
                parts.append(f"{k} = {'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                parts.append(f"{k} = {v}")
            elif isinstance(v, (dict, list)):
                parts.append(f"{k} = {json.dumps(v)}")
            else:
                escaped = str(v).replace("\\", "\\\\").replace("'", "\\'")
                parts.append(f"{k} = '{escaped}'")
        return ", ".join(parts)

    def _upsert(self, table: str, record_id: str, data: dict) -> bool:
        """UPSERT (create-or-replace) a record by ID using bound params."""
        data = {k: v for k, v in data.items() if k != 'id'}
        self._q(
            'UPSERT type::thing($tbl, $rid) CONTENT $data',
            {'tbl': f'tm_{table}', 'rid': record_id, 'data': data}
        )
        return True

    def _create(self, table: str, record_id: str, data: dict) -> bool:
        """CREATE a record by ID using bound params."""
        data = {k: v for k, v in data.items() if k != 'id'}
        self._q(
            'CREATE type::thing($tbl, $rid) CONTENT $data',
            {'tbl': f'tm_{table}', 'rid': record_id, 'data': data}
        )
        return True

    def _record_exists(self, table: str, record_id: str) -> bool:
        """Check if a record exists using bound params."""
        result = self._q(
            'SELECT id FROM type::thing($tbl, $rid)',
            {'tbl': f'tm_{table}', 'rid': record_id}
        )
        return len(result) > 0

    @staticmethod
    def _decision_content_hash(
        decision: Dict[str, Any],
        decision_id: str | None = None,
    ) -> str:
        from .domain.tdr import DecisionMakingDecisionRecord

        market_context = decision.get('market_context', {})
        if isinstance(market_context, str):
            try:
                market_context = json.loads(market_context)
            except json.JSONDecodeError as exc:
                raise DecisionMemoryDBError(
                    "Stored decision has invalid market_context JSON"
                ) from exc
        return DecisionMakingDecisionRecord.compute_hash(
            decision_id=decision_id if decision_id is not None else decision.get('id', ''),
            timestamp=decision.get('timestamp', ''),
            symbol=decision.get('symbol', ''),
            direction=decision.get('direction', '') or '',
            strategy=decision.get('strategy', ''),
            confidence=decision.get('confidence', 0.0),
            reasoning=decision.get('reasoning', ''),
            market_context=market_context,
        )

    # ==================================================================
    # Decision Records
    # ==================================================================

    def insert_decision(self, decision_data: Dict[str, Any]) -> bool:
        """Insert a decision record with audit chain."""
        from .audit.chain import ChainBuilder
        try:
            # Convert datetime objects to ISO strings
            if isinstance(decision_data.get('timestamp'), datetime):
                decision_data['timestamp'] = decision_data['timestamp'].isoformat()
            if isinstance(decision_data.get('exit_timestamp'), datetime):
                decision_data['exit_timestamp'] = decision_data['exit_timestamp'].isoformat()

            # Compute content_hash from original market context
            raw_market_ctx = decision_data.get('market_context', {})
            content_hash = self._decision_content_hash(decision_data)

            # Serialize JSON fields for storage
            stored_data = dict(decision_data)
            stored_data['market_context'] = json.dumps(raw_market_ctx)
            stored_data['decision_references'] = json.dumps(decision_data.get('references', []))
            stored_data['tags'] = json.dumps(decision_data.get('tags', []))
            stored_data.setdefault('tenant_id', None)

            # Remove non-column fields
            stored_data.pop('references', None)

            decision_id = stored_data['id']

            # Check if already exists
            existing = self._q(
                'SELECT * FROM type::thing($tbl, $rid)',
                {'tbl': 'tm_decision_records', 'rid': decision_id},
            )
            if existing:
                # SurrealDB returns a qualified RecordID (table:id). Hash the
                # canonical caller ID so an identical retry remains idempotent.
                stored_hash = self._decision_content_hash(existing[0], decision_id)
                if stored_hash != content_hash:
                    raise DecisionMemoryDBError(
                        f"Decision {decision_id!r} already exists with different "
                        "immutable content; refusing overwrite"
                    )
                with self.get_connection() as conn:
                    builder = ChainBuilder(conn)
                    entry = builder.get_entry(decision_id)
                    if entry is None:
                        logger.warning(
                            "Decision %s exists but audit entry missing; repairing",
                            decision_id,
                        )
                        builder.append(decision_id, stored_hash)
                    elif entry.content_hash != stored_hash:
                        raise DecisionMemoryDBError(
                            f"Decision {decision_id!r} audit hash does not match "
                            "stored immutable content"
                        )
                return True

            # Insert the decision
            col_data = {k: v for k, v in stored_data.items() if k != 'id'}
            self._create('decision_records', decision_id, col_data)

            # Append to audit chain
            try:
                with self.get_connection() as conn:
                    builder = ChainBuilder(conn)
                    builder.append(
                        record_id=decision_id,
                        content_hash=content_hash,
                    )
            except Exception as chain_err:
                entry = None
                try:
                    with self.get_connection() as conn:
                        entry = ChainBuilder(conn).get_entry(decision_id)
                except Exception:
                    logger.exception("Could not verify failed audit append")
                if entry is None or entry.content_hash != content_hash:
                    try:
                        self._q(
                            'DELETE type::thing($tbl, $rid)',
                            {'tbl': 'tm_decision_records', 'rid': decision_id},
                        )
                    except Exception:
                        logger.exception(
                            "Failed to remove unchained decision %s", decision_id
                        )
                    raise DecisionMemoryDBError(
                        f"Audit append failed for decision {decision_id!r}; "
                        "decision creation was rolled back"
                    ) from chain_err
                logger.warning(
                    "Audit append for %s raised after commit; verified persisted entry",
                    decision_id,
                )

            return True
        except DecisionMemoryDBError:
            raise
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to insert decision: {e}") from e

    def update_decision_outcome(self, decision_id: str, outcome_data: Dict[str, Any]) -> bool:
        """Update decision with exit outcome."""
        if isinstance(outcome_data.get('exit_timestamp'), datetime):
            outcome_data['exit_timestamp'] = outcome_data['exit_timestamp'].isoformat()

        fields = {}
        for key in ['exit_timestamp', 'exit_price', 'pnl', 'pnl_r',
                     'hold_duration', 'exit_reasoning', 'slippage',
                     'execution_quality', 'lessons', 'grade']:
            if key in outcome_data:
                fields[key] = outcome_data[key]

        if not fields:
            return False

        try:
            result = self._q(
                'UPDATE type::thing($tbl, $rid) CONTENT $data',
                {'tbl': 'tm_decision_records', 'rid': decision_id, 'data': fields},
            )
            return True
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to update decision outcome: {e}") from e

    def get_decision(self, decision_id: str) -> Optional[Dict[str, Any]]:
        """Get a decision record by ID."""
        rows = self._q(
            'SELECT * FROM type::thing($tbl, $rid)',
            {'tbl': 'tm_decision_records', 'rid': decision_id},
        )
        if not rows:
            return None

        decision = dict(rows[0])
        # Remove SurrealDB record id format
        decision['market_context'] = json.loads(decision['market_context']) if isinstance(decision.get('market_context'), str) else decision.get('market_context', {})
        decision['references'] = json.loads(decision['decision_references']) if isinstance(decision.get('decision_references'), str) else decision.get('decision_references', [])
        decision.pop('decision_references', None)
        decision['tags'] = json.loads(decision['tags']) if isinstance(decision.get('tags'), str) else decision.get('tags', [])
        return decision

    def query_decisions(
        self,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query decision records with filters."""
        params = {}
        conds = []
        if strategy:
            conds.append("strategy = $strategy")
            params['strategy'] = strategy
        if symbol:
            conds.append("symbol = $symbol")
            params['symbol'] = symbol

        q = "SELECT * FROM tm_decision_records"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY timestamp DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        decisions = []
        for row in rows:
            decision = dict(row)
            decision['market_context'] = json.loads(decision['market_context']) if isinstance(decision.get('market_context'), str) else decision.get('market_context', {})
            decision['references'] = json.loads(decision['decision_references']) if isinstance(decision.get('decision_references'), str) else decision.get('decision_references', [])
            decision.pop('decision_references', None)
            decision['tags'] = json.loads(decision['tags']) if isinstance(decision.get('tags'), str) else decision.get('tags', [])
            decisions.append(decision)
        return decisions

    # ==================================================================
    # Session State
    # ==================================================================

    def save_session_state(self, state_data: Dict[str, Any]) -> bool:
        """Save agent session state."""
        try:
            if isinstance(state_data.get('last_active'), datetime):
                state_data['last_active'] = state_data['last_active'].isoformat()

            data = {
                'last_active': state_data['last_active'],
                'warm_memory': json.dumps(state_data.get('warm_memory', {})),
                'active_positions': json.dumps(state_data.get('active_positions', [])),
                'risk_constraints': json.dumps(state_data.get('risk_constraints', {})),
            }
            agent_id = state_data['agent_id']
            return self._upsert('session_state', agent_id, data)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to save session state: {e}") from e

    def load_session_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Load agent session state."""
        rows = self._q(
            'SELECT * FROM type::thing($tbl, $rid)',
            {'tbl': 'tm_session_state', 'rid': agent_id},
        )
        if not rows:
            return None

        state = dict(rows[0])
        state['warm_memory'] = json.loads(state['warm_memory']) if isinstance(state.get('warm_memory'), str) else state.get('warm_memory', {})
        state['active_positions'] = json.loads(state['active_positions']) if isinstance(state.get('active_positions'), str) else state.get('active_positions', [])
        state['risk_constraints'] = json.loads(state['risk_constraints']) if isinstance(state.get('risk_constraints'), str) else state.get('risk_constraints', {})
        return state

    # ==================================================================
    # Patterns (L2)
    # ==================================================================

    def insert_pattern(self, pattern_data: Dict[str, Any]) -> bool:
        """Insert or replace a pattern record."""
        try:
            data = dict(pattern_data)
            if isinstance(data.get('metrics'), (dict, list)):
                data['metrics'] = json.dumps(data['metrics'])
            pattern_id = data.pop('pattern_id', data.pop('id', None))
            if not pattern_id:
                raise ValueError("pattern_data must have pattern_id or id")
            # Store pattern_id as regular field for query compatibility
            data['pattern_id'] = pattern_id
            return self._upsert('patterns', pattern_id, data)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to insert pattern: {e}") from e

    def query_patterns(
        self,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        pattern_type: Optional[str] = None,
        source: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query patterns with filters."""
        params = {}
        conds = []
        if strategy:
            conds.append("strategy = $strategy")
            params['strategy'] = strategy
        if symbol:
            conds.append("symbol = $symbol")
            params['symbol'] = symbol
        if pattern_type:
            conds.append("pattern_type = $pattern_type")
            params['pattern_type'] = pattern_type
        if source:
            conds.append("source = $source")
            params['source'] = source

        q = "SELECT * FROM tm_patterns"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY discovered_at DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        patterns = []
        for row in rows:
            p = dict(row)
            p['metrics'] = json.loads(p['metrics']) if isinstance(p.get('metrics'), str) else p.get('metrics', {})
            patterns.append(p)
        return patterns

    def get_pattern(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Get a single pattern by ID."""
        rows = self._q(
            'SELECT * FROM type::thing($tbl, $rid)',
            {'tbl': 'tm_patterns', 'rid': pattern_id},
        )
        if not rows:
            return None
        p = dict(rows[0])
        p['metrics'] = json.loads(p['metrics']) if isinstance(p.get('metrics'), str) else p.get('metrics', {})
        return p

    # ==================================================================
    # Strategy Adjustments (L3)
    # ==================================================================

    def insert_adjustment(self, adjustment_data: Dict[str, Any]) -> bool:
        """Insert or replace a strategy adjustment record."""
        try:
            data = dict(adjustment_data)
            adj_id = data.pop('adjustment_id', data.pop('id', None))
            if not adj_id:
                raise ValueError("adjustment_data must have adjustment_id or id")
            # Store adjustment_id as regular field for query compatibility
            data['adjustment_id'] = adj_id
            return self._upsert('strategy_adjustments', adj_id, data)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to insert adjustment: {e}") from e

    def query_adjustments(
        self,
        status: Optional[str] = None,
        adjustment_type: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Query strategy adjustments with filters."""
        params = {}
        conds = []
        if status:
            conds.append("status = $status")
            params['status'] = status
        if adjustment_type:
            conds.append("adjustment_type = $adjustment_type")
            params['adjustment_type'] = adjustment_type

        q = "SELECT * FROM tm_strategy_adjustments"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY created_at DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        return [dict(row) for row in rows]

    def update_adjustment_status(
        self,
        adjustment_id: str,
        status: str,
        applied_at: Optional[str] = None,
    ) -> bool:
        """Update the status of a strategy adjustment."""
        try:
            fields = {'status': status}
            if applied_at:
                fields['applied_at'] = applied_at
            result = self._q(
                'UPDATE type::thing($tbl, $rid) MERGE $data',
                {'tbl': 'tm_strategy_adjustments', 'rid': adjustment_id, 'data': fields},
            )
            return len(result) > 0
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to update adjustment status: {e}") from e

    # ==================================================================
    # OWM: Episodic Memory
    # ==================================================================

    def insert_episodic(self, data: Dict[str, Any]) -> bool:
        """Insert an episodic memory record."""
        try:
            d = dict(data)
            if isinstance(d.get('tags'), (list, dict)):
                d['tags'] = json.dumps(d['tags'])
            if isinstance(d.get('context_json'), dict):
                d['context_json'] = json.dumps(d['context_json'])
            if 'created_at' not in d:
                d['created_at'] = datetime.now(timezone.utc).isoformat()

            mem_id = d.pop('id', None)
            if not mem_id:
                raise ValueError("episodic data must have an id")
            # Store id as regular field for query compatibility
            d['id'] = mem_id
            # Check existence — plain INSERT fails on duplicate (like SQLite)
            existing = self._q(
                'SELECT id FROM type::thing($tbl, $rid)',
                {'tbl': 'tm_episodic_memory', 'rid': mem_id},
            )
            if existing:
                return True  # Idempotent like INSERT OR IGNORE
            return self._create('episodic_memory', mem_id, d)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to insert episodic memory: {e}") from e

    def query_episodic(
        self,
        strategy: Optional[str] = None,
        regime: Optional[str] = None,
        direction: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query episodic memories with filters."""
        params = {}
        conds = []
        if strategy:
            conds.append("strategy = $strategy")
            params['strategy'] = strategy
        if regime:
            conds.append("context_regime = $regime")
            params['regime'] = regime
        if direction:
            conds.append("direction = $direction")
            params['direction'] = direction

        q = "SELECT * FROM tm_episodic_memory"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY timestamp DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        results = []
        for row in rows:
            d = dict(row)
            d['context_json'] = json.loads(d['context_json']) if isinstance(d.get('context_json'), str) else d.get('context_json', {})
            d['tags'] = json.loads(d['tags']) if isinstance(d.get('tags'), str) else d.get('tags', [])
            results.append(d)
        return results

    def update_episodic_retrieval(self, memory_id: str) -> bool:
        """Increment retrieval_count and update last_retrieved."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            result = self._q(
                'UPDATE type::thing($tbl, $rid) SET retrieval_count += 1, last_retrieved = $now',
                {'tbl': 'tm_episodic_memory', 'rid': memory_id, 'now': now},
            )
            return len(result) > 0
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to update episodic retrieval: {e}") from e

    def update_episodic_embedding(self, memory_id: str, embedding: list[float]) -> bool:
        """Store embedding vector for an episodic memory record."""
        try:
            result = self._q(
                'UPDATE type::thing($tbl, $rid) SET embedding = $embedding',
                {'tbl': 'tm_episodic_memory', 'rid': memory_id, 'embedding': embedding},
            )
            return len(result) > 0
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to update episodic embedding: {e}") from e

    # ==================================================================
    # OWM: Semantic Memory
    # ==================================================================

    def insert_semantic(self, data: Dict[str, Any]) -> bool:
        """Insert a semantic memory record."""
        try:
            d = dict(data)
            if isinstance(d.get('validity_conditions'), (dict, list)):
                d['validity_conditions'] = json.dumps(d['validity_conditions'])
            now = datetime.now(timezone.utc).isoformat()
            d.setdefault('alpha', 1.0)
            d.setdefault('beta', 1.0)
            d.setdefault('sample_size', 0)
            d.setdefault('retrieval_strength', 1.0)
            d.setdefault('created_at', now)
            d.setdefault('updated_at', now)

            mem_id = d.pop('id', None)
            if not mem_id:
                raise ValueError("semantic data must have an id")
            d['id'] = mem_id
            existing = self._q(
                'SELECT id FROM type::thing($tbl, $rid)',
                {'tbl': 'tm_semantic_memory', 'rid': mem_id},
            )
            if existing:
                raise DecisionMemoryDBError(f"Semantic memory {mem_id} already exists")
            return self._create('semantic_memory', mem_id, d)
        except DecisionMemoryDBError:
            raise
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to insert semantic memory: {e}") from e

    def query_semantic(
        self,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        regime: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query semantic memories with filters. Computes confidence/uncertainty in Python."""
        params = {}
        conds = []
        if strategy:
            conds.append("strategy = $strategy")
            params['strategy'] = strategy
        if symbol:
            conds.append("symbol = $symbol")
            params['symbol'] = symbol
        if regime:
            conds.append("regime = $regime")
            params['regime'] = regime

        q = "SELECT * FROM tm_semantic_memory"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY updated_at DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        results = []
        for row in rows:
            d = dict(row)
            d['validity_conditions'] = json.loads(d['validity_conditions']) if isinstance(d.get('validity_conditions'), str) else d.get('validity_conditions')
            a, b = d['alpha'], d['beta']
            d['confidence'] = a / (a + b) if (a + b) > 0 else 0.5
            d['uncertainty'] = (a * b) / ((a + b) ** 2 * (a + b + 1)) if (a + b) > 0 else 1.0
            results.append(d)
        return results

    def update_semantic_bayesian(
        self,
        memory_id: str,
        confirmed: bool,
        weight: float = 1.0,
        evidence_id: Optional[str] = None,
    ) -> bool:
        """Update semantic memory Bayesian parameters (alpha/beta)."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            ref = evidence_id or now
            if confirmed:
                result = self._q(
                    'UPDATE type::thing($tbl, $rid) SET alpha += $weight, sample_size += 1, '
                    'last_confirmed = $ref, updated_at = $now',
                    {'tbl': 'tm_semantic_memory', 'rid': memory_id, 'weight': weight, 'ref': ref, 'now': now},
                )
            else:
                result = self._q(
                    'UPDATE type::thing($tbl, $rid) SET beta += $weight, sample_size += 1, '
                    'last_contradicted = $ref, updated_at = $now',
                    {'tbl': 'tm_semantic_memory', 'rid': memory_id, 'weight': weight, 'ref': ref, 'now': now},
                )
            return len(result) > 0
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to update semantic bayesian: {e}") from e

    def update_semantic_validity_conditions(
        self, memory_id: str, validity_conditions: dict
    ) -> bool:
        """Update validity_conditions JSON for a semantic memory."""
        try:
            now = datetime.now(timezone.utc).isoformat()
            result = self._q(
                'UPDATE type::thing($tbl, $rid) SET validity_conditions = $vc, updated_at = $now',
                {'tbl': 'tm_semantic_memory', 'rid': memory_id, 'vc': validity_conditions, 'now': now},
            )
            return len(result) > 0
        except Exception as e:
            raise DecisionMemoryDBError(
                f"Failed to update semantic validity_conditions: {e}"
            ) from e

    # ==================================================================
    # OWM: Procedural Memory
    # ==================================================================

    def upsert_procedural(self, data: Dict[str, Any]) -> bool:
        """Insert or replace a procedural memory record."""
        try:
            d = dict(data)
            now = datetime.now(timezone.utc).isoformat()
            d.setdefault('created_at', now)
            d['updated_at'] = now

            mem_id = d.pop('id', None)
            if not mem_id:
                raise ValueError("procedural data must have an id")
            return self._upsert('procedural_memory', mem_id, d)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to upsert procedural memory: {e}") from e

    def query_procedural(
        self,
        strategy: Optional[str] = None,
        symbol: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query procedural memory records with filters."""
        params = {}
        conds = []
        if strategy:
            conds.append("strategy = $strategy")
            params['strategy'] = strategy
        if symbol:
            conds.append("symbol = $symbol")
            params['symbol'] = symbol

        q = "SELECT * FROM tm_procedural_memory"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY updated_at DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        return [dict(row) for row in rows]

    # ==================================================================
    # OWM: Affective State
    # ==================================================================

    def init_affective(self, peak_score: float, current_score: float) -> bool:
        """Initialize affective state if not exists."""
        try:
            existing = self._q(
                'SELECT id FROM type::thing($tbl, $rid)',
                {'tbl': 'tm_affective_state', 'rid': 'current'},
            )
            if existing:
                return False

            now = datetime.now(timezone.utc).isoformat()
            self._create('affective_state', 'current', {
                'confidence_level': 0.5, 'risk_appetite': 1.0, 'momentum_bias': 0.0,
                'peak_score': peak_score, 'current_score': current_score,
                'drawdown_state': 0.0, 'max_acceptable_drawdown': 0.20,
                'consecutive_wins': 0, 'consecutive_losses': 0,
                'last_updated': now, 'history_json': '[]',
            })
            return True
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to initialize affective state: {e}") from e

    def load_affective(self) -> Optional[Dict[str, Any]]:
        """Load the current affective state."""
        rows = self._q(
            'SELECT * FROM type::thing($tbl, $rid)',
            {'tbl': 'tm_affective_state', 'rid': 'current'},
        )
        if not rows:
            return None
        d = dict(rows[0])
        d['history_json'] = json.loads(d['history_json']) if isinstance(d.get('history_json'), str) else d.get('history_json', [])
        return d

    def save_affective(self, data: Dict[str, Any]) -> bool:
        """Save (upsert) the current affective state."""
        try:
            d = dict(data)
            if isinstance(d.get('history_json'), (list, dict)):
                d['history_json'] = json.dumps(d['history_json'])
            d.setdefault('last_updated', datetime.now(timezone.utc).isoformat())

            # Store as 'current'
            d.pop('id', None)
            return self._upsert('affective_state', 'current', d)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to save affective state: {e}") from e

    # ==================================================================
    # OWM: Changepoint Detection State
    # ==================================================================

    def save_changepoint_state(
        self,
        cp_id: str,
        strategy: str,
        symbol: str,
        state_json: str,
        observation_count: int,
        changepoint_prob: float,
        changepoint_at: Optional[int] = None,
    ) -> None:
        """Save (upsert) changepoint detector state."""
        try:
            data = {
                'strategy': strategy,
                'symbol': symbol,
                'state_json': state_json,
                'last_observation_count': observation_count,
                'last_changepoint_prob': changepoint_prob,
                'last_changepoint_at': changepoint_at,
                'updated_at': datetime.now(timezone.utc).isoformat(),
            }
            self._upsert('changepoint_state', cp_id, data)
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to save changepoint state: {e}") from e

    def load_changepoint_state(
        self, strategy: str, symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Load changepoint detector state for a strategy+symbol pair."""
        rows = self._q(
            'SELECT * FROM tm_changepoint_state WHERE strategy = $strategy AND symbol = $symbol',
            {'strategy': strategy, 'symbol': symbol},
        )
        if not rows:
            return None
        return dict(rows[0])

    # ==================================================================
    # OWM: Prospective Memory
    # ==================================================================

    def insert_prospective(self, data: Dict[str, Any]) -> bool:
        """Insert a prospective memory record."""
        try:
            d = dict(data)
            if isinstance(d.get('trigger_condition'), (dict, list)):
                d['trigger_condition'] = json.dumps(d['trigger_condition'])
            if isinstance(d.get('planned_action'), (dict, list)):
                d['planned_action'] = json.dumps(d['planned_action'])
            if isinstance(d.get('source_episodic_ids'), list):
                d['source_episodic_ids'] = json.dumps(d['source_episodic_ids'])
            if isinstance(d.get('source_semantic_ids'), list):
                d['source_semantic_ids'] = json.dumps(d['source_semantic_ids'])
            d.setdefault('status', 'active')
            d.setdefault('priority', 0.5)
            d.setdefault('created_at', datetime.now(timezone.utc).isoformat())

            mem_id = d.pop('id', None)
            if not mem_id:
                raise ValueError("prospective data must have an id")
            d['id'] = mem_id
            existing = self._q(
                'SELECT id FROM type::thing($tbl, $rid)',
                {'tbl': 'tm_prospective_memory', 'rid': mem_id},
            )
            if existing:
                raise DecisionMemoryDBError(f"Prospective memory {mem_id} already exists")
            return self._create('prospective_memory', mem_id, d)
        except DecisionMemoryDBError:
            raise
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to insert prospective memory: {e}") from e

    def query_prospective(
        self,
        status: Optional[str] = None,
        trigger_type: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query prospective memories with filters."""
        params = {}
        conds = []
        if status:
            conds.append("status = $status")
            params['status'] = status
        if trigger_type:
            conds.append("trigger_type = $trigger_type")
            params['trigger_type'] = trigger_type

        q = "SELECT * FROM tm_prospective_memory"
        if conds:
            q += " WHERE " + " AND ".join(conds)
        q += f" ORDER BY priority DESC, created_at DESC LIMIT {limit}"

        rows = self._q(q, params if params else None)
        results = []
        for row in rows:
            d = dict(row)
            d['trigger_condition'] = json.loads(d['trigger_condition']) if isinstance(d.get('trigger_condition'), str) else d.get('trigger_condition', {})
            d['planned_action'] = json.loads(d['planned_action']) if isinstance(d.get('planned_action'), str) else d.get('planned_action', {})
            d['source_episodic_ids'] = json.loads(d['source_episodic_ids']) if isinstance(d.get('source_episodic_ids'), str) else d.get('source_episodic_ids', [])
            d['source_semantic_ids'] = json.loads(d['source_semantic_ids']) if isinstance(d.get('source_semantic_ids'), str) else d.get('source_semantic_ids', [])
            results.append(d)
        return results

    def update_prospective_status(
        self,
        memory_id: str,
        status: str,
        triggered_at: Optional[str] = None,
        outcome_pnl_r: Optional[float] = None,
        outcome_reflection: Optional[str] = None,
    ) -> bool:
        """Update prospective memory status and optional outcome fields."""
        try:
            fields = {'status': status}
            if triggered_at:
                fields['triggered_at'] = triggered_at
            if outcome_pnl_r is not None:
                fields['outcome_pnl_r'] = outcome_pnl_r
            if outcome_reflection is not None:
                fields['outcome_reflection'] = outcome_reflection

            result = self._q(
                'UPDATE type::thing($tbl, $rid) MERGE $data',
                {'tbl': 'tm_prospective_memory', 'rid': memory_id, 'data': fields},
            )
            return len(result) > 0
        except Exception as e:
            raise DecisionMemoryDBError(f"Failed to update prospective status: {e}") from e
