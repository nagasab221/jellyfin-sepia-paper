#!/usr/bin/env python3
"""Drive a running Jellyfin web client over the Chrome DevTools protocol.

Start the client with remote debugging, e.g. Jellyfin Desktop (Flatpak):
  flatpak run --env=QTWEBENGINE_REMOTE_DEBUGGING=127.0.0.1:9222 org.jellyfin.JellyfinDesktop
or Chromium with --remote-debugging-port=9222.

  jfdebug.py eval  "<js>"         print the result of an expression
  jfdebug.py go    "#/home"       navigate inside the app (hash route)
  jfdebug.py shot  out.png        screenshot of the page
  jfdebug.py css   file.css       load this local stylesheet in place of the server's
                                  Custom CSS (for testing before publishing)
  jfdebug.py size  1920 1080      emulate a viewport size (0 0 to reset)
"""
import base64, json, sys, time, urllib.request
import websocket

PORT = 9222


def target():
    tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{PORT}/json/list"))
    pages = [t for t in tabs if t["type"] == "page"]
    web = [t for t in pages if "/web/" in t["url"] or "web-client" not in t["url"]]
    return (web or pages)[0]


class CDP:
    def __init__(self):
        self.ws = websocket.create_connection(target()["webSocketDebuggerUrl"], timeout=60,
                                              suppress_origin=True)
        self.n = 0

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(msg["error"])
                return msg.get("result", {})

    def eval(self, expr):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=True, replMode=True)
        if r.get("exceptionDetails"):
            raise RuntimeError(r["exceptionDetails"].get("exception", {}).get("description", r["exceptionDetails"]))
        return r.get("result", {}).get("value")


def main():
    cmd, *args = sys.argv[1:]
    c = CDP()
    if cmd == "eval":
        v = c.eval(args[0])
        print(v if isinstance(v, str) else json.dumps(v, indent=1))
    elif cmd == "go":
        c.eval(f"location.hash = {json.dumps(args[0].lstrip('#'))}")
        time.sleep(float(args[1]) if len(args) > 1 else 2.5)
    elif cmd == "shot":
        data = c.call("Page.captureScreenshot", format="png")["data"]
        open(args[0], "wb").write(base64.b64decode(data))
        print(args[0])
    elif cmd == "css":
        css = open(args[0]).read()
        c.eval("""(css => {
            let s = document.getElementById('sp-dev');
            if (!s) { s = document.createElement('style'); s.id = 'sp-dev'; document.head.appendChild(s); }
            s.textContent = css;
            // switch off the server copy so only the local file applies
            document.querySelectorAll('style, link[rel=stylesheet]').forEach(e => {
              if (e.id !== 'sp-dev' && (e.textContent || '').includes('sepia-paper')) e.disabled = true;
            });
            return 'ok';
        })(%s)""" % json.dumps(css))
        print("local css applied")
    elif cmd == "size":
        w, h = int(args[0]), int(args[1])
        if w:
            c.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=1, mobile=False)
        else:
            c.call("Emulation.clearDeviceMetricsOverride")
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
