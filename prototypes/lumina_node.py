#!/usr/bin/env python3
"""
Lumina Network – Erster minimaler Node-Skeleton
================================================

Demonstriert:
- Einheitlichen Nachrichten-Header + Body (Kapitel 4)
- Ed25519-Signatur
- Einfache HELLO / HEARTBEAT / ACK Logik
- Simulierte Yggdrasil-Schicht (für Standalone-Tests)

Später: echte Anbindung an yggdrasil-go / ironwood.
"""

from __future__ import annotations

import hashlib
import json
import os
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.encoding import HexEncoder
except ImportError:
    print("Bitte 'pip install pynacl' ausführen.")
    raise


MAGIC = b"LN"
VERSION = 0x01

MSG_HELLO = 0x01
MSG_HEARTBEAT = 0x02
MSG_GOSSIP = 0x03
MSG_DATA = 0x04
MSG_ACK = 0x05


@dataclass
class LuminaNode:
    name: str
    signing_key: SigningKey = field(default_factory=SigningKey.generate)
    peers: Dict[str, VerifyKey] = field(default_factory=dict)
    msg_counter: int = 0

    @property
    def public_key(self) -> bytes:
        return bytes(self.signing_key.verify_key)

    @property
    def node_id(self) -> bytes:
        return hashlib.sha256(self.public_key).digest()

    def _next_msg_id(self) -> int:
        self.msg_counter += 1
        return int(time.time_ns()) ^ self.msg_counter

    def build_header(
        self,
        msg_type: int,
        body: bytes,
        flags: int = 0,
    ) -> bytes:
        msg_id = self._next_msg_id()
        timestamp = time.time_ns()

        # Header ohne Signature (Platzhalter 64 Nullen)
        header = struct.pack(
            ">2sBBHIQQ32s",
            MAGIC,
            VERSION,
            msg_type,
            flags,
            len(body),
            timestamp,
            msg_id,
            self.node_id,
        )
        # 64-Byte Signature-Platzhalter wird später ersetzt
        return header + b"\x00" * 64, msg_id

    def sign_message(self, header_without_sig: bytes, body: bytes) -> bytes:
        to_sign = header_without_sig + body
        signature = self.signing_key.sign(to_sign).signature
        # Signature an die richtige Stelle schreiben
        return header_without_sig + signature + body

    def create_hello(self) -> bytes:
        body_dict = {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "capabilities": ["routing", "gossip", "agent"],
            "software_version": "0.1.0-proto",
            "name": self.name,
        }
        body = json.dumps(body_dict, separators=(",", ":")).encode()
        header, _ = self.build_header(MSG_HELLO, body)
        return self.sign_message(header[:58], body)  # 58 = bis vor signature

    def create_heartbeat(self, seq: int = 0) -> bytes:
        body_dict = {
            "uptime_s": int(time.time()) % 100000,
            "load": 0.1,
            "peer_count": len(self.peers),
            "seq": seq,
        }
        body = json.dumps(body_dict, separators=(",", ":")).encode()
        header, _ = self.build_header(MSG_HEARTBEAT, body)
        return self.sign_message(header[:58], body)

    def create_ack(self, acked_msg_id: int, status: str = "ok") -> bytes:
        body_dict = {"acked_msg_id": acked_msg_id, "status": status}
        body = json.dumps(body_dict, separators=(",", ":")).encode()
        header, _ = self.build_header(MSG_ACK, body)
        return self.sign_message(header[:58], body)

    def parse_message(self, raw: bytes) -> Optional[Dict[str, Any]]:
        if len(raw) < 122:  # min header size
            return None
        magic, version, msg_type, flags, length, timestamp, msg_id, sender_id = struct.unpack(
            ">2sBBHIQQ32s", raw[:58]
        )
        if magic != MAGIC or version != VERSION:
            return None
        signature = raw[58:122]
        body = raw[122:122 + length]

        # Signatur prüfen (in Produktion: VerifyKey des Senders aus DHT holen)
        try:
            # Für Demo: wir nehmen an, der Sender ist bekannt
            to_verify = raw[:58] + body
            # In echter Implementierung: VerifyKey(sender_pubkey).verify(...)
            pass
        except Exception:
            return None

        try:
            body_data = json.loads(body.decode()) if body else {}
        except Exception:
            body_data = {"raw": body.hex()}

        return {
            "msg_type": msg_type,
            "msg_id": msg_id,
            "sender_id": sender_id.hex(),
            "timestamp": timestamp,
            "body": body_data,
            "raw_length": len(raw),
        }


def demo():
    print("=== Lumina Node Prototype ===\n")
    alice = LuminaNode("Alice")
    bob = LuminaNode("Bob")

    print(f"Alice Node-ID : {alice.node_id.hex()[:16]}...")
    print(f"Bob   Node-ID : {bob.node_id.hex()[:16]}...\n")

    hello = alice.create_hello()
    print(f"HELLO von Alice ({len(hello)} Bytes)")
    parsed = bob.parse_message(hello)
    print("Bob empfängt:", json.dumps(parsed, indent=2) if parsed else "FEHLER")

    hb = alice.create_heartbeat(seq=1)
    print(f"\nHEARTBEAT von Alice ({len(hb)} Bytes)")
    parsed = bob.parse_message(hb)
    print("Bob empfängt:", json.dumps(parsed, indent=2) if parsed else "FEHLER")

    if parsed:
        ack = bob.create_ack(parsed["msg_id"])
        print(f"\nACK von Bob ({len(ack)} Bytes)")
        parsed_ack = alice.parse_message(ack)
        print("Alice empfängt ACK:", json.dumps(parsed_ack, indent=2) if parsed_ack else "FEHLER")


if __name__ == "__main__":
    demo()
