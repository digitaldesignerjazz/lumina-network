#!/usr/bin/env python3
"""Lumina Network – Node-Prototyp v0.3.0 (Kademlia + Schwarm). pip install pynacl"""
from __future__ import annotations
import hashlib, json, struct, time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
try:
    from nacl.signing import SigningKey, VerifyKey
    from nacl.exceptions import BadSignatureError
except ImportError:
    raise SystemExit("Bitte zuerst ausführen:  pip install pynacl")
from kademlia import ALPHA, K, Contact, RoutingTable, contacts_from_wire, xor_distance
from swarm_overlay import ROLE_ELARA, ROLE_LYRA, ROLE_XEN, AgentPresence, SwarmDirectory, capabilities_for, normalize_role

MAGIC, VERSION = b"LN", 0x01
MSG_HELLO, MSG_HEARTBEAT, MSG_GOSSIP, MSG_DATA, MSG_ACK = 0x01, 0x02, 0x03, 0x04, 0x05
MSG_FIND_NODE, MSG_FIND_NODE_REPLY, MSG_PATH_PROBE = 0x10, 0x11, 0x20
MSG_NAMES = {1:"HELLO",2:"HEARTBEAT",3:"GOSSIP",4:"DATA",5:"ACK",0x10:"FIND_NODE",0x11:"FIND_NODE_REPLY",0x20:"PATH_PROBE"}

@dataclass
class SimulatedPacket:
    src_key: bytes
    dst_key: Optional[bytes]
    payload: bytes
    timestamp: float = field(default_factory=time.time)

class SimulatedIronwood:
    def __init__(self):
        self._nodes: Dict[bytes, "LuminaNode"] = {}
    def register(self, node: "LuminaNode") -> None:
        self._nodes[node.public_key] = node
    def unregister(self, node: "LuminaNode") -> None:
        self._nodes.pop(node.public_key, None)
    def send(self, src_key: bytes, dst_key: Optional[bytes], payload: bytes) -> None:
        pkt = SimulatedPacket(src_key, dst_key, payload)
        if dst_key is None:
            for key, node in list(self._nodes.items()):
                if key != src_key:
                    node._on_packet(pkt)
        else:
            target = self._nodes.get(dst_key)
            if target:
                target._on_packet(pkt)

NETWORK = SimulatedIronwood()

@dataclass
class PeerInfo:
    public_key: bytes
    node_id: bytes
    name: str = ""
    last_seen: float = field(default_factory=time.time)
    rtt_ms: float = 0.0
    capabilities: List[str] = field(default_factory=list)
    hello_replied: bool = False
    role: str = ""

@dataclass
class LuminaNode:
    name: str
    signing_key: SigningKey = field(default_factory=SigningKey.generate)
    peers: Dict[bytes, PeerInfo] = field(default_factory=dict)
    msg_counter: int = 0
    seq: int = 0
    start_time: float = field(default_factory=time.time)
    on_message: Optional[Callable] = None
    role: str = ""
    table: Optional[RoutingTable] = None
    swarm: SwarmDirectory = field(default_factory=SwarmDirectory)
    _pending_lrs: Dict[bytes, Contact] = field(default_factory=dict)
    def __post_init__(self):
        self.role = normalize_role(self.role)
        if self.table is None:
            object.__setattr__(self, "table", RoutingTable(self.node_id))
        NETWORK.register(self)
        if self.role:
            self.swarm.upsert(AgentPresence(self.role, self.node_id, self.public_key, self.name, self.capabilities))
    @property
    def public_key(self) -> bytes:
        return bytes(self.signing_key.verify_key)
    @property
    def node_id(self) -> bytes:
        return hashlib.sha256(self.public_key).digest()
    @property
    def short_id(self) -> str:
        return self.node_id.hex()[:12]
    @property
    def capabilities(self) -> List[str]:
        return capabilities_for(self.role) if self.role else ["routing", "gossip", "agent", "gateway"]
    def _next_msg_id(self) -> int:
        self.msg_counter += 1
        return (int(time.time_ns()) ^ self.msg_counter) & 0xFFFFFFFFFFFFFFFF
    def _build_signed_message(self, msg_type: int, body: dict, flags: int = 0) -> Tuple[bytes, int]:
        body_bytes = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        msg_id = self._next_msg_id()
        header = struct.pack(">2sBBHIQQ32s", MAGIC, VERSION, msg_type, flags, len(body_bytes), time.time_ns(), msg_id, self.node_id)
        sig = self.signing_key.sign(header + body_bytes).signature
        return header + sig + body_bytes, msg_id
    def _parse_and_verify(self, raw: bytes) -> Optional[Dict[str, Any]]:
        if len(raw) < 122:
            return None
        try:
            magic, version, msg_type, flags, length, timestamp, msg_id, sender_id = struct.unpack(">2sBBHIQQ32s", raw[:58])
        except struct.error:
            return None
        if magic != MAGIC or version != VERSION:
            return None
        signature, body = raw[58:122], raw[122:122 + length]
        if len(body) != length:
            return None
        verify_key = None
        for peer in self.peers.values():
            if peer.node_id == sender_id:
                verify_key = VerifyKey(peer.public_key)
                break
        try:
            body_data = json.loads(body.decode()) if body else {}
        except Exception:
            body_data = {}
        if verify_key is None and "public_key" in body_data:
            try:
                verify_key = VerifyKey(bytes.fromhex(body_data["public_key"]))
            except Exception:
                return None
        if verify_key is None:
            return None
        try:
            verify_key.verify(raw[:58] + body, signature)
        except BadSignatureError:
            return None
        return {"msg_type": msg_type, "msg_type_name": MSG_NAMES.get(msg_type, hex(msg_type)), "msg_id": msg_id, "sender_id": sender_id.hex(), "sender_key": bytes(verify_key), "timestamp": timestamp, "flags": flags, "body": body_data, "raw_length": len(raw)}
    def _remember(self, public_key: bytes, node_id: bytes, body: dict, rtt_ms: float = 0.0) -> PeerInfo:
        peer = self.peers.get(public_key)
        if peer is None:
            peer = PeerInfo(public_key, node_id, body.get("name", ""), capabilities=list(body.get("capabilities") or []), role=normalize_role(str(body.get("role") or "")))
            self.peers[public_key] = peer
        else:
            peer.last_seen = time.time()
            if body.get("name"):
                peer.name = body["name"]
            if body.get("capabilities"):
                peer.capabilities = list(body["capabilities"])
            if body.get("role"):
                peer.role = normalize_role(str(body["role"]))
        if rtt_ms:
            peer.rtt_ms = rtt_ms
        contact = Contact(node_id, public_key, name=peer.name, capabilities=peer.capabilities, rtt_ms=peer.rtt_ms)
        status, lrs = self.table.add(contact)
        if status == "full" and lrs is not None:
            self._pending_lrs[lrs.public_key] = contact
            self.send_heartbeat(dst_key=lrs.public_key)
        return peer
    def create_hello(self) -> bytes:
        msg, _ = self._build_signed_message(MSG_HELLO, {"node_id": self.node_id.hex(), "public_key": self.public_key.hex(), "name": self.name, "role": self.role, "capabilities": self.capabilities, "software_version": "0.3.0-proto", "uptime_s": int(time.time() - self.start_time)})
        return msg
    def create_heartbeat(self) -> bytes:
        self.seq += 1
        msg, _ = self._build_signed_message(MSG_HEARTBEAT, {"seq": self.seq, "peer_count": len(self.peers), "table_size": self.table.size(), "role": self.role})
        return msg
    def create_gossip(self, updates: List[dict]) -> bytes:
        msg, _ = self._build_signed_message(MSG_GOSSIP, {"origin_id": self.node_id.hex(), "seq": self.seq, "ttl": 8, "updates": updates})
        return msg
    def create_find_node(self, target_id: str) -> bytes:
        msg, _ = self._build_signed_message(MSG_FIND_NODE, {"target": target_id, "requester_id": self.node_id.hex()})
        return msg
    def create_find_node_reply(self, target_id: str) -> bytes:
        try:
            target = bytes.fromhex(target_id)
        except ValueError:
            target = self.node_id
        msg, _ = self._build_signed_message(MSG_FIND_NODE_REPLY, {"target": target_id, "contacts": [c.as_wire() for c in self.table.closest(target, n=K)]})
        return msg
    def send_to(self, dst_key: Optional[bytes], raw: bytes) -> None:
        NETWORK.send(self.public_key, dst_key, raw)
    def broadcast(self, raw: bytes) -> None:
        self.send_to(None, raw)
    def send_hello(self, dst_key: Optional[bytes] = None) -> None:
        self.send_to(dst_key, self.create_hello())
    def send_heartbeat(self, dst_key: Optional[bytes] = None) -> None:
        self.send_to(dst_key, self.create_heartbeat())
    def announce_agent(self) -> None:
        if not self.role:
            return
        p = AgentPresence(self.role, self.node_id, self.public_key, self.name, self.capabilities)
        self.swarm.upsert(p)
        self.broadcast(self.create_gossip([p.as_update()]))
    def iterative_find_node(self, target: bytes, alpha: int = ALPHA) -> List[Contact]:
        shortlist = list(self.table.closest(target, n=K))
        queried: Set[bytes] = set()
        improved, rounds = True, 0
        while improved and rounds < 8:
            rounds += 1
            improved = False
            candidates = [c for c in shortlist if c.node_id not in queried][:alpha]
            if not candidates:
                break
            best = xor_distance(shortlist[0].node_id, target) if shortlist else None
            for c in candidates:
                queried.add(c.node_id)
                self.send_to(c.public_key, self.create_find_node(target.hex()))
            shortlist = self.table.closest(target, n=K)
            if shortlist and best is not None and xor_distance(shortlist[0].node_id, target) < best:
                improved = True
            elif len([c for c in shortlist if c.node_id in queried]) < min(K, len(shortlist)):
                improved = True
        return self.table.closest(target, n=K)
    def _on_packet(self, pkt: SimulatedPacket) -> None:
        parsed = self._parse_and_verify(pkt.payload)
        if not parsed:
            return
        sender_key, sender_id = parsed["sender_key"], bytes.fromhex(parsed["sender_id"])
        is_new = sender_key not in self.peers
        peer = self._remember(sender_key, sender_id, parsed["body"], rtt_ms=max(0.0, (time.time() - pkt.timestamp) * 1000.0))
        if sender_key in self._pending_lrs:
            self.table.add(self._pending_lrs.pop(sender_key))
        if self.on_message:
            self.on_message(self, parsed)
        t, body = parsed["msg_type"], parsed["body"]
        if t == MSG_HELLO and is_new and not peer.hello_replied:
            peer.hello_replied = True
            self.send_hello(dst_key=sender_key)
        elif t == MSG_GOSSIP:
            for p in self.swarm.ingest_gossip(body.get("updates") or []):
                self._remember(p.public_key, p.node_id, {"name": p.name, "role": p.role, "capabilities": p.capabilities})
        elif t == MSG_FIND_NODE:
            self.send_to(sender_key, self.create_find_node_reply(body.get("target") or ""))
        elif t == MSG_FIND_NODE_REPLY:
            for c in contacts_from_wire(body.get("contacts") or []):
                if c.node_id != self.node_id:
                    self.table.add(c)
    def known_peers(self) -> List[str]:
        return [f"{(p.role or p.name or p.node_id.hex()[:8])} ({p.public_key.hex()[:8]}…)" for p in self.peers.values()]
    def shutdown(self) -> None:
        NETWORK.unregister(self)

def demo():
    print("Lumina Network – Node v0.3.0  ·  Kademlia + Schwarm")
    def on_msg(node, msg):
        print(f"[{node.name:8}] ← {msg['msg_type_name']:16} von {msg['sender_id'][:12]}…")
    lumia = LuminaNode("Lumia", on_message=on_msg, role=ROLE_ELARA)
    lyra = LuminaNode("Lyra", on_message=on_msg, role=ROLE_LYRA)
    xen = LuminaNode("Xen", on_message=on_msg, role=ROLE_XEN)
    hannover = LuminaNode("Hannover", on_message=on_msg)
    print(f"Lumia {lumia.short_id}…  Lyra {lyra.short_id}…  Xen {xen.short_id}…")
    lumia.send_hello(); lyra.send_hello(); xen.send_hello(); hannover.send_hello()
    lumia.announce_agent(); lyra.announce_agent(); xen.announce_agent()
    found = lumia.iterative_find_node(xen.node_id)
    print("FIND_NODE Treffer:", [(c.name, xor_distance(c.node_id, xen.node_id) == 0) for c in found])
    for n in (lumia, lyra, xen, hannover):
        print(n.name, n.known_peers(), n.table.snapshot(), n.swarm.summary())
        n.shutdown()

if __name__ == "__main__":
    demo()
