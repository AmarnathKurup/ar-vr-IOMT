import json
import os
import ssl
from pathlib import Path
from typing import Any, Optional

import paho.mqtt.client as mqtt


TRUE_VALUES = {"1", "true", "yes", "on"}


def _load_env_file(env_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not env_path.exists():
        return values

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value

    return values


def _read_setting(name: str, env_values: dict[str, str], default: Optional[str] = None) -> Optional[str]:
    return os.getenv(name, env_values.get(name, default))


class SecureMQTTPublisher:
    def __init__(
        self,
        broker: str,
        port: int,
        client_id: str,
        username: str,
        password: str,
        keepalive: int = 60,
        tls_enabled: bool = False,
        tls_ca_cert: Optional[str] = None,
        tls_certfile: Optional[str] = None,
        tls_keyfile: Optional[str] = None,
        tls_insecure: bool = False,
    ) -> None:
        if not username or not password:
            raise ValueError("MQTT_USERNAME and MQTT_PASSWORD are required for secure MQTT connection.")

        self.broker = broker
        self.port = port
        self.client_id = client_id
        self.username = username
        self.password = password
        self.keepalive = keepalive
        self.tls_enabled = tls_enabled
        self.tls_ca_cert = tls_ca_cert
        self.tls_certfile = tls_certfile
        self.tls_keyfile = tls_keyfile
        self.tls_insecure = tls_insecure
        self.client: Optional[mqtt.Client] = None

    @classmethod
    def from_env(cls, env_path: str = ".env") -> "SecureMQTTPublisher":
        env_values = _load_env_file(Path(env_path))

        broker = _read_setting("MQTT_BROKER", env_values, "localhost")
        port = int(_read_setting("MQTT_PORT", env_values, "1883") or "1883")
        keepalive = int(_read_setting("MQTT_KEEPALIVE", env_values, "60") or "60")
        client_id = _read_setting("MQTT_CLIENT_ID", env_values, "spo2-sensor-publisher") or "spo2-sensor-publisher"
        username = _read_setting("MQTT_USERNAME", env_values, "") or ""
        password = _read_setting("MQTT_PASSWORD", env_values, "") or ""

        tls_enabled_raw = (_read_setting("MQTT_TLS_ENABLED", env_values, "false") or "false").strip().lower()
        tls_enabled = tls_enabled_raw in TRUE_VALUES

        tls_insecure_raw = (_read_setting("MQTT_TLS_INSECURE", env_values, "false") or "false").strip().lower()
        tls_insecure = tls_insecure_raw in TRUE_VALUES

        tls_ca_cert = _read_setting("MQTT_TLS_CA_CERT", env_values)
        tls_certfile = _read_setting("MQTT_TLS_CERTFILE", env_values)
        tls_keyfile = _read_setting("MQTT_TLS_KEYFILE", env_values)

        return cls(
            broker=broker or "localhost",
            port=port,
            client_id=client_id,
            username=username,
            password=password,
            keepalive=keepalive,
            tls_enabled=tls_enabled,
            tls_ca_cert=tls_ca_cert,
            tls_certfile=tls_certfile,
            tls_keyfile=tls_keyfile,
            tls_insecure=tls_insecure,
        )

    def connect(self) -> None:
        client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        client.username_pw_set(self.username, self.password)
        client.enable_logger()

        if self.tls_enabled:
            client.tls_set(
                ca_certs=self.tls_ca_cert,
                certfile=self.tls_certfile,
                keyfile=self.tls_keyfile,
                tls_version=ssl.PROTOCOL_TLS_CLIENT,
            )
            client.tls_insecure_set(self.tls_insecure)

        client.connect(self.broker, self.port, self.keepalive)
        client.loop_start()
        self.client = client

    def publish_json(self, topic: str, payload: dict[str, Any], qos: int = 1, retain: bool = False) -> None:
        if self.client is None:
            raise RuntimeError("MQTT client is not connected.")

        payload_str = json.dumps(payload)
        result = self.client.publish(topic, payload_str, qos=qos, retain=retain)
        result.wait_for_publish()

    def disconnect(self) -> None:
        if self.client is None:
            return
        self.client.loop_stop()
        self.client.disconnect()
        self.client = None
