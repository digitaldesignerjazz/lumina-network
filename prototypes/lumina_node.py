#!/usr/bin/env python3
"""
Lumina Network – Vertiefter Node-Prototyp
=========================================

Kapitel-Bezug:
  - Nachrichtenformate (Kapitel 4)
  - Yggdrasil / Ironwood Integration (Kapitel 5 + 6)

Features dieses Prototyps:
  • Vollständiger signierter Header + Body (Ed25519)
  • Alle Kern-Nachrichtentypen: HELLO, HEARTBEAT, GOSSIP, DATA, ACK, FIND_NODE
  • Echte Signatur-Verifikation
  • Simulierte Ironwood/Yggdrasil-Transportschicht (PacketConn-ähnlich)
  • Multi-Node-Simulation mit shared Network-Bus
  • Peer-Management + einfache Discovery
  • Path-Notify-ähnliche Callbacks
  • Konfigurierbare Timeouts & Metriken

Abhängigkeit: pip install pynacl

Späterer Ausbau:
  - Echte Anbindung an ironwood / yggdrasil-ng / ygg_stream
  - CBOR statt JSON
  - Async (asyncio / trio)
"""

from __future__ import annotations

import hashlib
import json
import struct
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

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
    """Ein Paket, das über die simulierte PacketConn geht."""
    src_key: bytes          # 32-byte public key
    dst_key: Optional[bytes]  # None = Broadcast
    payload: bytes
    timestamp: float = field(default_factory=time.time)


class SimulatedIronwood:
    """
    Sehr vereinfachte Simulation einer Ironwood PacketConn.
    Alle Nodes teilen sich denselben Bus (für Standalone-Tests).
    """

    def __init__(self):
        self._nodes: Dict[bytes, "LuminaNode"] = {}  # pubkey -> node
        self._path_notify_callbacks: List[Callable[[bytes, bytes], None]] = []

    def register(self, node: "LuminaNode") -> None:
        self._nodes[node.public_key] = node

    def unregister(self, node: "LuminaNode") -> None:
        self._nodes.pop(node.public_key, None)

    def send(self, src_key: bytes, dst_key: Optional[bytes], payload: bytes) -> None:
        pkt = SimulatedPacket(src_key=src_key, dst_key=dst_key, payload=payload)

        if dst_key is None:
            # Broadcast an alle außer dem Sender
            for key, node in self._nodes.items():
                if key != src_key:
                    node._on_packet(pkt)
        else:
            target = self._nodes.get(dst_key)
            if target:
                target._on_packet(pkt)
                # Simuliere path_notify
                for cb in self._path_notify_callbacks:
                    cb(src_key, dst_key)

    def add_path_notify(self, callback: Callable[[bytes, bytes], None]) -> None:
        self._path_notify_callbacks.append(callback)

    def get_peers(self, exclude: bytes) -> List[bytes]:
        return [k for k in self._nodes if k != exclude]


# Globaler Bus für die Demo
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


# ---------------------------------------------------------------------------
# Lumina Node
# ---------------------------------------------------------------------------

@dataclass
class LuminaNode:
    name: str
    signing_key: SigningKey = field(default_factory=SigningKey.generate)
    peers: Dict[bytes, PeerInfo] = field(default_factory=dict)  # pubkey -> PeerInfo
    msg_counter: int = 0
    seq: int = 0
    start_time: float = field(default_factory=time.time)
    on_message: Optional[Callable[["LuminaNode", Dict[str, Any]], None]] = None

    def __post_init__(self):
        NETWORK.register(self)

    # ------------------------------------------------------------------
    # Identität
    # ------------------------------------------------------------------

    @property
    def public_key(self) -> bytes:
        return bytes(self.signing_key.verify_key)

    @property
    def node_id(self) -> bytes:
        return hashlib.sha256(self.public_key).digest()

    @property
    def short_id(self) -> str:
        return self.node_id.hex()[:12]

    # ------------------------------------------------------------------
    # Header + Signatur (Kapitel 4)
    # ------------------------------------------------------------------

    def _next_msg_id(self) -> int:
        self.msg_counter += 1
        return (int(time.time_ns()) ^ self.msg_counter) & 0xFFFFFFFFFFFFFFFF

    def _build_signed_message(self, msg_type: int, body: dict, flags: int = 0) -> Tuple[bytes, int]:
        body_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        msg_id = self._next_msg_id()
        timestamp = time.time_ns()

        # Header ohne Signatur (58 Bytes)
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
        signature = self.signing_key.sign(to_sign).signature  # 64 Bytes

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

        # Signatur prüfen – wir brauchen den Public Key des Senders
        # In der echten Welt kommt er aus dem DHT / Peer-Store.
        # Hier suchen wir zuerst in bekannten Peers, sonst akzeptieren wir
        # den Key aus dem Body (bei HELLO) oder lehnen ab.
        verify_key: Optional[VerifyKey] = None

        # Versuch 1: bereits bekannter Peer
        for peer in self.peers.values():
            if peer.node_id == sender_id:
                verify_key = VerifyKey(peer.public_key)
                break

        # Versuch 2: Body enthält public_key (typisch bei HELLO)
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
            # Unbekannter Sender ohne Key → vorerst ablehnen
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

    # ------------------------------------------------------------------
    # Nachrichten erstellen
    # ------------------------------------------------------------------

    def create_hello(self) -> bytes:
        body = {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "name": self.name,
            "capabilities": ["routing", "gossip", "agent", "gateway"],
            "software_version": "0.2.0-proto",
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

    # ------------------------------------------------------------------
    # Senden über simulierte Ironwood-Schicht
    # ------------------------------------------------------------------

    def send_to(self, dst_key: Optional[bytes], raw: bytes) -> None:
        NETWORK.send(self.public_key, dst_key, raw)

    def broadcast(self, raw: bytes) -> None:
        self.send_to(None, raw)

    def send_hello(self, dst_key: Optional[bytes] = None) -> None:
        self.send_to(dst_key, self.create_hello())

    def send_heartbeat(self, dst_key: Optional[bytes] = None) -> None:
        self.send_to(dst_key, self.create_heartbeat())

    # ------------------------------------------------------------------
    # Empfang
    # ------------------------------------------------------------------

    def _on_packet(self, pkt: SimulatedPacket) -> None:
        parsed = self._parse_and_verify(pkt.payload)
        if not parsed:
            return

        # Peer aktualisieren / anlegen
        sender_key = parsed["sender_key"]
        if sender_key not in self.peers:
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

        # Optionales User-Callback
        if self.on_message:
            self.on_message(self, parsed)

        # Automatische Antworten
        if parsed["msg_type"] == MSG_HELLO:
            # Höflichkeits-HELLO zurück
            self.send_hello(dst_key=sender_key)

        elif parsed["msg_type"] == MSG_HEARTBEAT:
            # ACK zurück
            ack = self.create_ack(parsed["msg_id"])
            self.send_to(sender_key, ack)

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------

    def known_peers(self) -> List[str]:
        return [f"{p.name or p.node_id.hex()[:8]} ({p.public_key.hex()[:8]}…)" for p in self.peers.values()]

    def shutdown(self) -> None:
        NETWORK.unregister(self)


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------

def pretty(msg: Dict[str, Any]) -> str:
    return json.dumps(msg, indent=2, ensure_ascii=False)


def demo():
    print("=" * 64)
    print("  Lumina Network – Vertiefter Node-Prototyp (v0.2)")
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

    # 1. Alice broadcastet HELLO → Bob & Carol lernen sie kennen
    print("— Alice broadcastet HELLO —")
    alice.send_hello()
    print()

    # 2. Bob sendet HEARTBEAT an Alice
    print("— Bob sendet HEARTBEAT an Alice —")
    bob.send_heartbeat(dst_key=alice.public_key)
    print()

    # 3. Carol sendet DATA an Bob
    print("— Carol sendet DATA an Bob —")
    data_msg = carol.create_data("text/plain", "Hallo vom Nexus-Schwarm, Sir.")
    carol.send_to(bob.public_key, data_msg)
    print()

    # 4. Gossip von Alice
    print("— Alice sendet GOSSIP —")
    gossip = alice.create_gossip([
        {"type": "peer_up", "node_id": bob.node_id.hex(), "data": {"name": "Bob"}},
        {"type": "metric", "node_id": alice.node_id.hex(), "data": {"load": 0.11}},
    ])
    alice.broadcast(gossip)
    print()

    # Status
    print("=" * 64)
    print("Aktuelle Peer-Tabellen:")
    print(f"  Alice kennt : {alice.known_peers()}")
    print(f"  Bob   kennt : {bob.known_peers()}")
    print(f"  Carol kennt : {carol.known_peers()}")
    print("=" * 64)

    # Aufräumen
    alice.shutdown()
    bob.shutdown()
    carol.shutdown()


if __name__ == "__main__":
    demo()
