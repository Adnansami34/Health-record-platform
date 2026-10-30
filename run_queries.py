"""
Step 4: Run the SQL queries and show the answers as simple tables.

Run:  python run_queries.py
Needs: health_record.db (made by pipeline.py) and queries.sql in the same folder.
Also saves everything to query_results.txt (good for your README).
"""
import re
import sqlite3

DB_FILE = "health_record.db"
QUERY_FILE = "queries.sql"
OUTPUT_FILE = "query_results.txt"


def format_table(columns, rows):
    """Make a plain-text table with aligned columns."""
    widths = [len(c) for c in columns]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    line = "  ".join(c.ljust(widths[i]) for i, c in enumerate(columns))
    divider = "  ".join("-" * w for w in widths)
    body = ["  ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)) for row in rows]
    return "\n".join([line, divider] + body)


def main():
    with open(QUERY_FILE, encoding="utf-8") as f:
        text = f.read()

    # split the file into blocks that start with "-- Q"
    blocks = re.split(r"(?m)^-- (?=Q\d)", text)[1:]

    conn = sqlite3.connect(DB_FILE)
    output = []
    for block in blocks:
        title, _, sql = block.partition("\n")
        cursor = conn.execute(sql)
        columns = [d[0] for d in cursor.description]
        rows = cursor.fetchall()
        output.append(f"{title}\n{format_table(columns, rows)}\n")
    conn.close()

    result = "\n".join(output)
    print(result)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)
    print(f"(Saved to {OUTPUT_FILE})")


if __name__ == "__main__":
    main()
