from threading import Thread
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            body = b"Bot est online e rodando 24/7!"
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass

def run():
    # Pega a porta que o Render quer, ou usa 8080 como fallback local.
    port = int(os.environ.get('PORT', 8080))
    server = ThreadingHTTPServer(('0.0.0.0', port), HealthHandler)
    server.serve_forever()

def keep_alive():
    t = Thread(target=run)
    t.start()