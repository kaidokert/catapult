"""A modified version of SimpleHTTPServer which adds a CORS header.

This is useful to avoid CORS errors when trying to access local
files from a browser.
This will server files at the localhost address on port 8000.
This will serve the files in the directory in which it is invoked.

  Usage:

  python server.py
"""

import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler

class CORSRequestHandler(SimpleHTTPRequestHandler):
  def end_headers(self):
    self.send_header('Access-Control-Allow-Origin', '*')
    SimpleHTTPRequestHandler.end_headers(self)

if __name__ == '__main__':
  BaseHTTPServer.HTTPServer(('', 8000), CORSRequestHandler).serve_forever()
