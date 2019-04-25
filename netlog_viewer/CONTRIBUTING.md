Running locally
--------------

```
git clone https://chromium.googlesource.com/catapult
cd catapult/netlog_viewer/netlog_viewer
ln -s ../../third_party/polymer/components/
python -m SimpleHTTPServer 8080
```

You can serve the static files using whatever web server you like (python's
SimpleHTTPServer used in example above), as there is no server side dependency
other than loading the static files.

Running tests
--------------

Startup a dev server to serve the HTML:

```
bin/run_dev_server --no-install-hooks --port 8111
```

Navigate to [http://localhost:8111/netlog_viewer/tests.html](http://localhost:8111/netlog_viewer/tests.html).

Alternately to run the tests in a headless mode from console can use `netlog_viewer/bin/run_dev_server_tests`, however this is inconvenient for debugging since the browser window is closed immediately upon completion.

Reporting bugs
--------------

To report bugs please use the [Chromium bug tracker](http://crbug.com/new). Prefix the bug title with `[NetLogViewer]`. If you have the ability to change the component, set it to `Internals>Network>Logging`.

Contributing changes
--------------

Changes should be sumitted using a Gerrit code review, with the reviewer set to one of the [NetLog OWNERS](OWNERS). For instructions on how to use the code review system, see [catapult/CONTRIBUTING.md](../CONTRIBUTING.md).

Known issues
--------------

The viewer code was extracted from Chromium and has not been modernized yet.
 * Not properly converted to components/Polymer.
 * The custom layout code should be replaced by modern CSS (e.g. flexbox).
