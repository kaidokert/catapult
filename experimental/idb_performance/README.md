# IndexedDB Performance Benchmarks

## Usage
```bash
python -m SimpleHTTPServer 8000
```

Benchmarks:
 - Nested vs. Flat data structure
   - Run at http://localhost:8000/open.html
 - Opening database connections with third party wrappers
   - Currently only supports [jakearchibald/idb][1]
   - Run at http://localhost:8000/flat.html

[1]: https://github.com/jakearchibald/idb
