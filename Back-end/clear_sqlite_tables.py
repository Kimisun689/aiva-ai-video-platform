#!/usr/bin/env python3
"""
Utility to clear all data from every user-defined table in a SQLite database
without dropping the tables themselves.

Default target database: ../prompts.db relative to this script's directory.

Usage:
  python clear_sqlite_tables.py                    # uses default prompts.db
  python clear_sqlite_tables.py --db /path/to.db   # specify db path
  python clear_sqlite_tables.py --yes              # skip confirmation
"""

import argparse
import os
import sqlite3
import sys
from typing import List


def resolve_default_db_path() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Project root appears to contain prompts.db alongside Back-end/
    project_root = os.path.abspath(os.path.join(script_dir, os.pardir))
    return os.path.join(project_root, "prompts.db")


def get_user_tables(connection: sqlite3.Connection) -> List[str]:
    query = (
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name;"
    )
    cursor = connection.execute(query)
    return [row[0] for row in cursor.fetchall()]


def clear_tables(connection: sqlite3.Connection, table_names: List[str]) -> None:
    # Disable foreign key checks to avoid dependency order issues while clearing.
    connection.execute("PRAGMA foreign_keys=OFF;")
    try:
        with connection:
            for table_name in table_names:
                connection.execute(f"DELETE FROM \"{table_name}\";")
            # If AUTOINCREMENT was used, reset sequences
            try:
                connection.execute("DELETE FROM sqlite_sequence;")
            except sqlite3.DatabaseError:
                # sqlite_sequence may not exist; ignore if so
                pass
    finally:
        connection.execute("PRAGMA foreign_keys=ON;")


def main() -> int:
    parser = argparse.ArgumentParser(description="Clear all rows from all tables in a SQLite DB (non-destructive to schema)")
    parser.add_argument("--db", dest="db_path", default=resolve_default_db_path(), help="Path to SQLite database file (default: prompts.db at project root)")
    parser.add_argument("--yes", dest="assume_yes", action="store_true", help="Proceed without interactive confirmation")
    args = parser.parse_args()

    db_path = os.path.abspath(args.db_path)
    if not os.path.exists(db_path):
        print(f"Error: database file not found: {db_path}")
        return 1

    print(f"Target database: {db_path}")
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.Error as e:
        print(f"Failed to connect to database: {e}")
        return 1

    try:
        tables = get_user_tables(conn)
        if not tables:
            print("No user tables found; nothing to clear.")
            return 0

        print("The following tables will be cleared (rows deleted, schema preserved):")
        for t in tables:
            print(f"  - {t}")

        if not args.assume_yes:
            answer = input("Proceed to delete ALL rows from these tables? [y/N]: ").strip().lower()
            if answer not in {"y", "yes"}:
                print("Aborted.")
                return 0

        clear_tables(conn, tables)
        print("All specified tables have been cleared.")
        return 0
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return 1
    finally:
        try:
            conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    sys.exit(main())


