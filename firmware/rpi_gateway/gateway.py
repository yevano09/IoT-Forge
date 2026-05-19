import json, queue, signal, sys, threading, time, logging, os
from http.server import BaseHTTPRequestHandler, HTTPServer
import paho.mqtt.client as mqtt
import yaml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S"
)
log = logging.getLogger("gateway")


class UpstreamBuffer:
    def __init__(self, maxsize: int = 10_000):
        self._q = queue.Queue(maxsize=maxsize)
        self.dropped = 0

    def put(self, topic: str, payload: str):
        try:
            self._q.put_nowait((topic, payload))
        except queue.Full:
            self.dropped += 1

    def get_nowait(self) -> tuple | None:
        try:
            return self._q.get_nowait()
        except queue.Empty:
            return None

    def size(self) -> int:
        return self._q.qsize()


class Gateway:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.buffer = UpstreamBuffer(maxsize=cfg.get("buffer_size", 10_000))
        self._local = None
        self._upstream = None
        self._up_connected = False
        self._stop = threading.Event()
        self._stats = {"forwarded": 0, "buffered": 0}
        self._devices = {}
        self._start_ts = time.time()

    def _on_local_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except json.JSONDecodeError:
            log.warning(f"Bad JSON on {msg.topic}")
            return
        payload["_gw_ts"] = int(time.time() * 1000)
        payload["_gw_id"] = self.cfg["gateway"]["id"]
        payload["_gw_site"] = self.cfg["gateway"]["site_id"]
        if "device_id" in payload:
            self._devices[payload["device_id"]] = {
                "last_seen": payload["_gw_ts"],
                "topic": msg.topic
            }
        enriched = json.dumps(payload)
        if self._up_connected:
            self._upstream.publish(msg.topic, enriched, qos=0)
            self._stats["forwarded"] += 1
        else:
            self.buffer.put(msg.topic, enriched)
            self._stats["buffered"] += 1

    def _start_local(self):
        c = mqtt.Client(client_id=f"gw-{self.cfg['gateway']['id']}-local")
        c.on_message = self._on_local_message
        c.connect(self.cfg["local_broker"]["host"], self.cfg["local_broker"]["port"], keepalive=60)
        sub_topic = f"iot/{self.cfg['gateway']['org_id']}/{self.cfg['gateway']['site_id']}/#"
        c.subscribe(sub_topic, qos=0)
        log.info(f"Local subscribed  topic={sub_topic}")
        self._local = c
        c.loop_start()

    def _on_upstream_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._up_connected = True
            log.info("Upstream connected")
            self._flush_buffer()
        else:
            self._up_connected = False
            log.warning(f"Upstream connect failed rc={rc}")

    def _on_upstream_disconnect(self, client, userdata, rc):
        self._up_connected = False
        log.warning("Upstream disconnected — buffering enabled")

    def _flush_buffer(self):
        flushed = 0
        while True:
            item = self.buffer.get_nowait()
            if item is None:
                break
            topic, payload = item
            self._upstream.publish(topic, payload, qos=0)
            flushed += 1
        if flushed:
            log.info(f"Flushed {flushed} buffered messages to upstream")

    def _start_upstream(self):
        cfg_up = self.cfg.get("upstream_broker", {})
        if not cfg_up.get("enabled", False):
            log.info("Upstream broker disabled — local-only mode")
            return
        c = mqtt.Client(client_id=f"gw-{self.cfg['gateway']['id']}-upstream")
        c.on_connect = self._on_upstream_connect
        c.on_disconnect = self._on_upstream_disconnect
        if cfg_up.get("username"):
            c.username_pw_set(cfg_up["username"], cfg_up["password"])
        try:
            c.connect_async(cfg_up["host"], cfg_up["port"], keepalive=60)
            c.loop_start()
            log.info(f"Upstream connecting  host={cfg_up['host']}:{cfg_up['port']}")
        except Exception as e:
            log.warning(f"Upstream broker unreachable: {e}")
        self._upstream = c

    def _stats_loop(self):
        interval = self.cfg.get("stats_interval_s", 30)
        while not self._stop.wait(interval):
            log.info(
                f"stats  forwarded={self._stats['forwarded']}  "
                f"buffered={self._stats['buffered']}  "
                f"buf_size={self.buffer.size()}  "
                f"devices={len(self._devices)}"
            )

    def _api_loop(self):
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/health":
                    body = json.dumps({
                        "status": "ok",
                        "upstream_connected": gateway._up_connected,
                        "known_devices": len(gateway._devices),
                        "buffer_size": gateway.buffer.size(),
                        **gateway._stats
                    }).encode()
                    ctype = "application/json"
                elif self.path == "/devices":
                    body = json.dumps(gateway._devices, indent=2).encode()
                    ctype = "application/json"
                elif self.path == "/metrics":
                    ctype = "text/plain; version=0.0.4"
                    uptime = time.time() - gateway._start_ts
                    g = gateway
                    body = (
                        f'# HELP gateway_info Gateway metadata\n'
                        f'# TYPE gateway_info gauge\n'
                        f'gateway_info{{id="{g.cfg["gateway"]["id"]}",'
                        f'org_id="{g.cfg["gateway"]["org_id"]}",'
                        f'site_id="{g.cfg["gateway"]["site_id"]}"}} 1\n'
                        f'# HELP gateway_up_connected Upstream connection status\n'
                        f'# TYPE gateway_up_connected gauge\n'
                        f'gateway_up_connected {1 if g._up_connected else 0}\n'
                        f'# HELP gateway_known_devices Number of known devices\n'
                        f'# TYPE gateway_known_devices gauge\n'
                        f'gateway_known_devices {len(g._devices)}\n'
                        f'# HELP gateway_buffer_size Current buffered message count\n'
                        f'# TYPE gateway_buffer_size gauge\n'
                        f'gateway_buffer_size {g.buffer.size()}\n'
                        f'# HELP gateway_messages_forwarded_total Messages forwarded upstream\n'
                        f'# TYPE gateway_messages_forwarded_total counter\n'
                        f'gateway_messages_forwarded_total {g._stats["forwarded"]}\n'
                        f'# HELP gateway_messages_buffered_total Messages buffered when offline\n'
                        f'# TYPE gateway_messages_buffered_total counter\n'
                        f'gateway_messages_buffered_total {g._stats["buffered"]}\n'
                        f'# HELP gateway_buffer_dropped_total Messages dropped due to full buffer\n'
                        f'# TYPE gateway_buffer_dropped_total counter\n'
                        f'gateway_buffer_dropped_total {g.buffer.dropped}\n'
                        f'# HELP gateway_uptime_seconds Gateway process uptime\n'
                        f'# TYPE gateway_uptime_seconds gauge\n'
                        f'gateway_uptime_seconds {uptime}\n'
                    ).encode()
                else:
                    self.send_response(404); self.end_headers(); return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *args):
                pass

        port = self.cfg.get("api_port", 8080)
        server = HTTPServer(("", port), Handler)
        log.info(f"Gateway API  http://0.0.0.0:{port}/health")
        while not self._stop.is_set():
            server.handle_request()

    def start(self):
        self._start_local()
        self._start_upstream()
        threading.Thread(target=self._stats_loop, daemon=True).start()
        threading.Thread(target=self._api_loop, daemon=True).start()
        log.info("Gateway running — Ctrl+C to stop")

    def stop(self):
        self._stop.set()
        if self._local:
            self._local.loop_stop(); self._local.disconnect()
        if self._upstream:
            self._upstream.loop_stop(); self._upstream.disconnect()
        log.info("Gateway stopped")


def load_config(path="gateway_config.yaml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    gw = Gateway(cfg)

    def on_signal(sig, frame):
        log.info("Shutdown signal received")
        gw.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, on_signal)
    signal.signal(signal.SIGTERM, on_signal)

    gw.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
