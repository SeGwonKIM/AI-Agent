"""
standalone_demo.py - Zero-Dependency Local Web Server for HITL Dashboard
Uses pure Python standard library (http.server) to run without pip dependencies.

실행: python standalone_demo.py
브라우저 접속: http://localhost:8501
"""

import os
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pipeline import TikTokPublishingGraph, InMemoryCheckpointer

PORT = 8501
HERE = os.path.dirname(os.path.abspath(__file__))

checkpointer = InMemoryCheckpointer()
graph = TikTokPublishingGraph(checkpointer=checkpointer)

# 초기 샘플 데이터 로드 및 초기 실행
sample_path = os.path.join(HERE, "sample_data.json")
with open(sample_path, "r", encoding="utf-8") as f:
    sample_cases = json.load(f)

for case in sample_cases:
    graph.run(case)


class HITLRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/", "/index.html"]:
            html_path = os.path.join(HERE, "web_demo.html")
            with open(html_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        elif parsed.path == "/api/tasks":
            tasks = []
            for item in sample_cases:
                tid = item["task_id"]
                st = checkpointer.load(tid)
                if st:
                    tasks.append(st.__dict__)
            
            payload = json.dumps({"tasks": tasks}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        if parsed.path == "/api/run_batch":
            for case in sample_cases:
                graph.run(case)
            self._send_json({"status": "ok", "message": "Batch pipeline re-executed"})
        elif parsed.path == "/api/resume":
            try:
                data = json.loads(body)
                task_id = data["task_id"]
                action = data["action"]
                comment = data.get("comment", "")
                edited_caption = data.get("edited_caption")
                edited_hashtags = data.get("edited_hashtags")

                graph.resume(task_id, action=action, comment=comment,
                             edited_caption=edited_caption, edited_hashtags=edited_hashtags)
                self._send_json({"status": "ok", "task_id": task_id})
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, status_code=400)
        else:
            self.send_error(404, "Endpoint Not Found")

    def _send_json(self, data: dict, status_code: int = 200):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        # 간결한 콘솔 로그
        print(f"[HTTP {self.address_string()}] {args[0]} -> {args[1]}")


def run_server():
    server = HTTPServer(("0.0.0.0", PORT), HITLRequestHandler)
    print("=" * 70)
    print(f"🚀 TikTok HITL 관제센터 웹 데모 서버 실행 중!")
    print(f"👉 브라우저 접속 주소: http://localhost:{PORT}")
    print("=" * 70)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n서버를 종료합니다.")
        server.server_close()


if __name__ == "__main__":
    run_server()
