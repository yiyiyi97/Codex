from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "ehs.db"


def init_db() -> None:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS hazards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            area TEXT NOT NULL,
            level TEXT NOT NULL,
            found_at TEXT NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '待整改'
        );
        CREATE TABLE IF NOT EXISTS interlocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            requester TEXT NOT NULL,
            area TEXT NOT NULL,
            start_at TEXT NOT NULL,
            end_at TEXT NOT NULL,
            level TEXT NOT NULL,
            reason TEXT NOT NULL,
            approve_status TEXT NOT NULL DEFAULT '待审批',
            shield_status TEXT NOT NULL DEFAULT '未生效'
        );
        """
    )

    if db.execute("SELECT COUNT(*) FROM hazards").fetchone()[0] == 0:
        db.execute(
            """
            INSERT INTO hazards (title, area, level, found_at, description, status)
            VALUES
            ('消防通道堵塞', '包装车间', '高', '2026-02-01 10:20', '杂物堆放影响通行', '待验收'),
            ('配电箱警示缺失', '动力站', '中', '2026-02-03 14:05', '安全警示标识脱落', '待整改')
            """
        )
    if db.execute("SELECT COUNT(*) FROM interlocks").fetchone()[0] == 0:
        db.execute(
            """
            INSERT INTO interlocks (code, requester, area, start_at, end_at, level, reason, approve_status, shield_status)
            VALUES
            ('IL-2026-0019', '李工', '反应釜R-2201', '2026-02-12 08:00', '2026-02-13 20:00', '一级', '仪表临时检修需要', '已批准', '屏蔽中'),
            ('IL-2026-0020', '周工', '压缩机C-08', '2026-02-13 08:00', '2026-02-14 08:00', '二级', '联锁功能联调测试', '待审批', '未生效')
            """
        )
    db.commit()
    db.close()


class Handler(BaseHTTPRequestHandler):
    def _db(self):
        db = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
        return db

    def _send_json(self, payload, status=200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        length = int(self.headers.get("Content-Length", "0"))
        return json.loads(self.rfile.read(length).decode("utf-8")) if length else {}

    def _serve_file(self, path: Path):
        if not path.exists() or not path.is_file():
            self.send_error(404)
            return
        ctype = "text/plain; charset=utf-8"
        if path.suffix == ".html":
            ctype = "text/html; charset=utf-8"
        elif path.suffix == ".css":
            ctype = "text/css; charset=utf-8"
        elif path.suffix == ".js":
            ctype = "application/javascript; charset=utf-8"
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/" or route == "/index.html":
            return self._serve_file(BASE_DIR / "index.html")
        if route in {"/styles.css", "/script.js"}:
            return self._serve_file(BASE_DIR / route.lstrip("/"))

        if route == "/api/dashboard":
            db = self._db()
            payload = {
                "todoHazard": db.execute("SELECT COUNT(*) FROM hazards WHERE status IN ('待整改','待验收')").fetchone()[0],
                "closedHazard": db.execute("SELECT COUNT(*) FROM hazards WHERE status = '已闭环'").fetchone()[0],
                "lotoActive": 11,
                "interlockShield": db.execute("SELECT COUNT(*) FROM interlocks WHERE shield_status='屏蔽中'").fetchone()[0],
                "pendingInterlock": db.execute("SELECT COUNT(*) FROM interlocks WHERE approve_status='待审批'").fetchone()[0],
                "abnormalEvents": 3,
                "whiteListCount": 42,
            }
            db.close()
            return self._send_json(payload)

        if route == "/api/hazards":
            db = self._db()
            rows = db.execute("SELECT id, title, area, level, found_at, status FROM hazards ORDER BY id DESC").fetchall()
            db.close()
            return self._send_json([dict(r) for r in rows])

        if route == "/api/interlocks":
            db = self._db()
            rows = db.execute("SELECT code, area, requester, approve_status, shield_status, end_at FROM interlocks ORDER BY id DESC").fetchall()
            db.close()
            return self._send_json([dict(r) for r in rows])

        self.send_error(404)

    def do_POST(self):
        route = urlparse(self.path).path
        data = self._read_json()

        if route == "/api/hazards":
            fields = [data.get("title", "").strip(), data.get("area", "").strip(), data.get("level", "").strip(), data.get("description", "").strip()]
            found_at = data.get("found_at", "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M")
            if not all(fields):
                return self._send_json({"error": "参数不完整"}, 400)
            db = self._db()
            db.execute(
                "INSERT INTO hazards (title, area, level, found_at, description) VALUES (?, ?, ?, ?, ?)",
                (fields[0], fields[1], fields[2], found_at, fields[3]),
            )
            db.commit()
            db.close()
            return self._send_json({"message": "隐患提交成功"})

        if route == "/api/interlocks":
            keys = ["code", "requester", "area", "start_at", "end_at", "level", "reason"]
            values = [data.get(k, "").strip() for k in keys]
            if not all(values):
                return self._send_json({"error": "参数不完整"}, 400)
            db = self._db()
            db.execute(
                "INSERT INTO interlocks (code, requester, area, start_at, end_at, level, reason) VALUES (?, ?, ?, ?, ?, ?, ?)",
                tuple(values),
            )
            db.commit()
            db.close()
            return self._send_json({"message": "安全连锁申请已提交"})

        self.send_error(404)


if __name__ == "__main__":
    init_db()
    server = ThreadingHTTPServer(("0.0.0.0", 8000), Handler)
    print("Server started on http://0.0.0.0:8000")
    server.serve_forever()
