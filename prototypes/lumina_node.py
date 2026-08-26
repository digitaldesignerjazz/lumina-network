#!/usr/bin/env python3
"""
Lumina Network – Vertiefter Node-Prototyp (v0.2.1)
=================================================

Kapitel-Bezug:
  - Nachrichtenformate (Kapitel 4)
  - Yggdrasil / Ironwood Integration (Kapitel 5 + 6)

Features:
  • Vollständiger signierter Header + Body (Ed25519)
  • Alle Kern-Nachrichtentypen: HELLO, HEARTBEAT, GOSSIP, DATA, ACK, FIND_NODE
  • Echte Signatur-Verifikation
  • Simulierte Ironwood/Yggdrasil-Transportschicht
  • Multi-Node-Simulation mit shared Network-Bus
  • Peer-Management + einfache Discovery
  • Path-Notify-ähnliche Callbacks
  • Stabile Auto-Reply-Logik (kein HELLO-Ping-Pong mehr)

Abhängigkeit: pip install pynacl
"""

from __future__ import annotations

import hashlib
import json
import struct
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
except ImportError:
    raise SystemExit("Bitte zuerst ausführen:  pip install pynacl")


# ---------------------------------------------------------------------------
# Konstanten (Kapitel 4)
# ---------------------------------------------------------------------------

MAGIC = b"LN"
VERSION = 0x01

MSG_HELLO = 0x01
MSG_HEARTBEAT = 0x02
MSG_GOSSIP = 0x03
MSG_DATA = 0x04
MSG_ACK = 0x05
MSG_FIND_NODE = 0x10
MSG_FIND_NODE_REPLY = 0x11
MSG_PATH_PROBE = 0x20

MSG_NAMES = {
    MSG_HELLO: "HELLO",
    MSG_HEARTBEAT: "HEARTBEAT",
    MSG_GOSSIP: "GOSSIP",
    MSG_DATA: "DATA",
    MSG_ACK: "ACK",
    MSG_FIND_NODE: "FIND_NODE",
    MSG_FIND_NODE_REPLY: "FIND_NODE_REPLY",
    MSG_PATH_PROBE: "PATH_PROBE",
}


# ---------------------------------------------------------------------------
# Simulierte Ironwood / Yggdrasil Transportschicht
# ---------------------------------------------------------------------------

@dataclass
class SimulatedPacket:
    src_key: bytes
    dst_key: Optional[bytes]
    payload: bytes
    timestamp: float = field(default_factory=time.time)


class SimulatedIronwood:
    def __init__(self):
        self._nodes: Dict[bytes, "LuminaNode"] = {}
        self._path_notify_callbacks: List[Callable[[bytes, bytes], None]] = []

    def register(self, node: "LuminaNode") -> None:
        self._nodes[node.public_key] = node

    def unregister(self, node: "LuminaNode") -> None:
        self._nodes.pop(node.public_key, None)

    def send(self, src_key: bytes, dst_key: Optional[bytes], payload: bytes) -> None:
        pkt = SimulatedPacket(src_key=src_key, dst_key=dst_key, payload=payload)

        if dst_key is None:
            for key, node in list(self._nodes.items()):
                if key != src_key:
                    node._on_packet(pkt)
        else:
            target = self._nodes.get(dst_key)
            if target:
                target._on_packet(pkt)
                for cb in self._path_notify_callbacks:
                    cb(src_key, dst_key)

    def add_path_notify(self, callback: Callable[[bytes, bytes], None]) -> None:
        self._path_notify_callbacks.append(callback)

    def get_peers(self, exclude: bytes) -> List[bytes]:
        return [k for k in self._nodes if k != exclude]


NETWORK = SimulatedIronwood()


# ---------------------------------------------------------------------------
# Peer-Informationen
# ---------------------------------------------------------------------------

@dataclass
class PeerInfo:
    public_key: bytes
    node_id: bytes
    name: str = ""
    last_seen: float = field(default_factory=time.time)
    rtt_ms: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    hello_replied: bool = False   # verhindert HELLO-Ping-Pong


# ---------------------------------------------------------------------------
# Lumina Node
# ---------------------------------------------------------------------------

@dataclass
class LuminaNode:
    name: str
    signing_key: SigningKey = field(default_factory=SigningKey.generate)
    peers: Dict[bytes, PeerInfo] = field(default_factory=dict)
    msg_counter: int = 0
    seq: int = 0
    start_time: float = field(default_factory=time.time)
    on_message: Optional[Callable[["LuminaNode", Dict[str, Any]], None]] = None

    def __post_init__(self):
        NETWORK.register(self)

    @property
    def public_key(self) -> bytes:
        return bytes(self.signing_key.verify_key)

    @property
    def node_id(self) -> bytes:
        return hashlib.sha256(self.public_key).digest()

    @property
    def short_id(self) -> str:
        return self.node_id.hex()[:12]

    def _next_msg_id(self) -> int:
        self.msg_counter += 1
        return (int(time.time_ns()) ^ self.msg_counter) & 0xFFFFFFFFFFFFFFFF

    def _build_signed_message(self, msg_type: int, body: dict, flags: int = 0) -> Tuple[bytes, int]:
        body_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        msg_id = self._next_msg_id()
        timestamp = time.time_ns()

        header_wo_sig = struct.pack(
            ">2sBBHIQQ32s",
            MAGIC,
            VERSION,
            msg_type,
            flags,
            len(body_bytes),
            timestamp,
            msg_id,
            self.node_id,
        )

        to_sign = header_wo_sig + body_bytes
        signature = self.signing_key.sign(to_sign).signature

        full = header_wo_sig + signature + body_bytes
        return full, msg_id

    def _parse_and_verify(self, raw: bytes) -> Optional[Dict[str, Any]]:
        if len(raw) < 122:
            return None

        try:
            magic, version, msg_type, flags, length, timestamp, msg_id, sender_id = struct.unpack(
                ">2sBBHIQQ32s", raw[:58]
            )
        except struct.error:
            return None

        if magic != MAGIC or version != VERSION:
            return None

        signature = raw[58:122]
        body = raw[122:122 + length]

        if len(body) != length:
            return None

        verify_key: Optional[VerifyKey] = None

        for peer in self.peers.values():
            if peer.node_id == sender_id:
                verify_key = VerifyKey(peer.public_key)
                break

        body_data: Dict[str, Any] = {}
        try:
            body_data = json.loads(body.decode()) if body else {}
        except Exception:
            body_data = {"raw": body.hex()}

        if verify_key is None and "public_key" in body_data:
            try:
                pk = bytes.fromhex(body_data["public_key"])
                verify_key = VerifyKey(pk)
            except Exception:
                pass

        if verify_key is None:
            return None

        try:
            verify_key.verify(raw[:58] + body, signature)
        except BadSignatureError:
            return None

        return {
            "msg_type": msg_type,
            "msg_type_name": MSG_NAMES.get(msg_type, f"0x{msg_type:02x}"),
            "msg_id": msg_id,
            "sender_id": sender_id.hex(),
            "sender_key": bytes(verify_key),
            "timestamp": timestamp,
            "flags": flags,
            "body": body_data,
            "raw_length": len(raw),
        }

    def create_hello(self) -> bytes:
        body = {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "name": self.name,
            "capabilities": ["routing", "gossip", "agent", "gateway"],
            "software_version": "0.2.1-proto",
            "uptime_s": int(time.time() - self.start_time),
        }
        msg, _ = self._build_signed_message(MSG_HELLO, body)
        return msg

    def create_heartbeat(self) -> bytes:
        self.seq += 1
        body = {
            "seq": self.seq,
            "uptime_s": int(time.time() - self.start_time),
            "load": 0.12,
            "peer_count": len(self.peers),
            "metrics": {"avg_rtt_ms": 12.4, "packet_loss": 0.001},
        }
        msg, _ = self._build_signed_message(MSG_HEARTBEAT, body)
        return msg

    def create_gossip(self, updates: List[dict]) -> bytes:
        body = {
            "origin_id": self.node_id.hex(),
            "seq": self.seq,
            "ttl": 8,
            "updates": updates,
        }
        msg, _ = self._build_signed_message(MSG_GOSSIP, body)
        return msg

    def create_data(self, content_type: str, payload: str, priority: int = 0) -> bytes:
        body = {
            "content_type": content_type,
            "payload": payload,
            "priority": priority,
            "ttl_hops": 16,
        }
        msg, _ = self._build_signed_message(MSG_DATA, body)
        return msg

    def create_ack(self, acked_msg_id: int, status: str = "ok") -> bytes:
        body = {"acked_msg_id": acked_msg_id, "status": status}
        msg, _ = self._build_signed_message(MSG_ACK, body)
        return msg

    def create_find_node(self, target_id: str) -> bytes:
        body = {"target": target_id}
        msg, _ = self._build_signed_message(MSG_FIND_NODE, body)
        return msg

    def send_to(self, dst_key: Optional[bytes], raw: bytes) -> None:
        NETWORK.send(self.public_key, dst_key, raw)

    def broadcast(self, raw: bytes) -> None:
        self.send_to(None, raw)

    def send_hello(self, dst_key: Optional[bytes] = None) -> None:
        self.send_to(dst_key, self.create_hello())

    def send_heartbeat(self, dst_key: Optional[bytes] = None) -> None:
        self.send_to(dst_key, self.create_heartbeat())

    def _on_packet(self, pkt: SimulatedPacket) -> None:
        parsed = self._parse_and_verify(pkt.payload)
        if not parsed:
            return

        sender_key = parsed["sender_key"]
        is_new_peer = sender_key not in self.peers

        if is_new_peer:
            self.peers[sender_key] = PeerInfo(
                public_key=sender_key,
                node_id=bytes.fromhex(parsed["sender_id"]),
                name=parsed["body"].get("name", ""),
                capabilities=parsed["body"].get("capabilities", []),
            )
        else:
            self.peers[sender_key].last_seen = time.time()
            if "name" in parsed["body"]:
                self.peers[sender_key].name = parsed["body"]["name"]

        if self.on_message:
            self.on_message(self, parsed)

        # Stabile Auto-Reply-Logik
        if parsed["msg_type"] == MSG_HELLO and is_new_peer:
            # Nur beim allerersten Kontakt einmal antworten
            peer = self.peers[sender_key]
            if not peer.hello_replied:
                peer.hello_replied = True
                self.send_hello(dst_key=sender_key)

        elif parsed["msg_type"] == MSG_HEARTBEAT:
            ack = self.create_ack(parsed["msg_id"])
            self.send_to(sender_key, ack)

    def known_peers(self) -> List[str]:
        return [f"{p.name or p.node_id.hex()[:8]} ({p.public_key.hex()[:8]}…)" for p in self.peers.values()]

    def shutdown(self) -> None:
        NETWORK.unregister(self)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def demo():
    print("=" * 64)
    print("  Lumina Network – Vertiefter Node-Prototyp (v0.2.1)")
    print("=" * 64)
    print()

    def on_msg(node: LuminaNode, msg: Dict[str, Any]):
        print(f"[{node.name:8}] ← {msg['msg_type_name']:12} von {msg['sender_id'][:12]}…  "
              f"({msg['raw_length']} Bytes)")

    alice = LuminaNode("Alice", on_message=on_msg)
    bob   = LuminaNode("Bob",   on_message=on_msg)
    carol = LuminaNode("Carol", on_message=on_msg)

    print(f"Alice  Node-ID : {alice.short_id}…")
    print(f"Bob    Node-ID : {bob.short_id}…")
    print(f"Carol  Node-ID : {carol.short_id}…")
    print()

    print("— Alice broadcastet HELLO —")
    alice.send_hello()
    print()

    print("— Bob sendet HEARTBEAT an Alice —")
    bob.send_heartbeat(dst_key=alice.public_key)
    print()

    print("— Carol sendet DATA an Bob —")
    data_msg = carol.create_data("text/plain", "Hallo vom Nexus-Schwarm, Sir.")
    carol.send_to(bob.public_key, data_msg)
    print()

    print("— Alice sendet GOSSIP —")
    gossip = alice.create_gossip([
        {"type": "peer_up", "node_id": bob.node_id.hex(), "data": {"name": "Bob"}},
        {"type": "metric", "node_id": alice.node_id.hex(), "data": {"load": 0.11}},
    ])
    alice.broadcast(gossip)
    print()

    print("=" * 64)
    print("Aktuelle Peer-Tabellen:")
    print(f"  Alice kennt : {alice.known_peers()}")
    print(f"  Bob   kennt : {bob.known_peers()}")
    print(f"  Carol kennt : {carol.known_peers()}")
    print("=" * 64)

    alice.shutdown()
    bob.shutdown()
    carol.shutdown()


if __name__ == "__main__":
    demo()
