from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent


class FoodShareHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def log_message(self, format, *args):
        print(f"[FoodShare] {self.address_string()} - {format % args}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    server = ThreadingHTTPServer(('0.0.0.0', port), FoodShareHandler)
    print(f"Serving FoodShare frontend on http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nStopping FoodShare frontend server...')
    finally:
        server.server_close()
