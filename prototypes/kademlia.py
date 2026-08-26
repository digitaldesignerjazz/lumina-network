#!/usr/bin/env python3
"""Lumina Network – Kademlia Routing Table (M0.2)."""
from __future__ import annotations
import hashlib, os, time
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Tuple

ID_BITS = 256
K = 20
ALPHA = 3
BUCKET_COUNT = ID_BITS

def sha256_id(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()

def xor_distance(a: bytes, b: bytes) -> int:
    if len(a) != 32 or len(b) != 32:
        raise ValueError("Node-IDs müssen 32 Byte (256 Bit) sein")
    return int.from_bytes(a, "big") ^ int.from_bytes(b, "big")

def bucket_index(distance: int) -> int:
    if distance <= 0:
        return 0
    return min(distance.bit_length() - 1, BUCKET_COUNT - 1)

def random_id_in_bucket(local_id: bytes, index: int) -> bytes:
    local = int.from_bytes(local_id, "big")
    if index <= 0:
        return local_id
    lo = 1 << index
    hi = (1 << (index + 1)) if index < ID_BITS - 1 else (1 << ID_BITS)
    dist = lo + (int.from_bytes(os.urandom(32), "big") % (hi - lo))
    return (local ^ dist).to_bytes(32, "big")

@dataclass
class Contact:
    node_id: bytes
    public_key: bytes
    last_seen: float = field(default_factory=time.time)
    rtt_ms: float = 0.0
    name: str = ""
    capabilities: List[str] = field(default_factory=list)
    fail_count: int = 0
    def touch(self, rtt_ms: Optional[float] = None) -> None:
        self.last_seen = time.time()
        self.fail_count = 0
        if rtt_ms is not None and rtt_ms >= 0:
            self.rtt_ms = rtt_ms
    def as_wire(self) -> dict:
        return {
            "node_id": self.node_id.hex(),
            "public_key": self.public_key.hex(),
            "last_seen": int(self.last_seen),
            "rtt_ms": round(self.rtt_ms, 2),
            "name": self.name,
            "capabilities": list(self.capabilities),
        }

class KBucket:
    def __init__(self, index: int, k: int = K):
        self.index = index
        self.k = k
        self.contacts: List[Contact] = []
    def __len__(self) -> int:
        return len(self.contacts)
    def get(self, node_id: bytes) -> Optional[Contact]:
        for c in self.contacts:
            if c.node_id == node_id:
                return c
        return None
    def add(self, contact: Contact) -> Tuple[str, Optional[Contact]]:
        existing = self.get(contact.node_id)
        if existing:
            existing.touch(contact.rtt_ms or None)
            if contact.name:
                existing.name = contact.name
            if contact.capabilities:
                existing.capabilities = list(contact.capabilities)
            if contact.public_key:
                existing.public_key = contact.public_key
            self.contacts.remove(existing)
            self.contacts.append(existing)
            return "updated", None
        if len(self.contacts) < self.k:
            self.contacts.append(contact)
            return "inserted", None
        return "full", self.contacts[0]
    def replace_lrs(self, new_contact: Contact) -> None:
        if self.contacts:
            self.contacts.pop(0)
        self.contacts.append(new_contact)
    def remove(self, node_id: bytes) -> bool:
        before = len(self.contacts)
        self.contacts = [c for c in self.contacts if c.node_id != node_id]
        return len(self.contacts) != before

class RoutingTable:
    def __init__(self, local_id: bytes, k: int = K):
        self.local_id = local_id
        self.k = k
        self.buckets = [KBucket(i, k=k) for i in range(BUCKET_COUNT)]
    def _bucket_for(self, node_id: bytes) -> KBucket:
        return self.buckets[bucket_index(xor_distance(self.local_id, node_id))]
    def add(self, contact: Contact) -> Tuple[str, Optional[Contact]]:
        if contact.node_id == self.local_id:
            return "self", None
        return self._bucket_for(contact.node_id).add(contact)
    def replace_lrs(self, contact: Contact) -> None:
        self._bucket_for(contact.node_id).replace_lrs(contact)
    def remove(self, node_id: bytes) -> bool:
        return self._bucket_for(node_id).remove(node_id)
    def get(self, node_id: bytes) -> Optional[Contact]:
        return self._bucket_for(node_id).get(node_id)
    def closest(self, target: bytes, n: int = K, pns: bool = False) -> List[Contact]:
        all_contacts: List[Contact] = []
        for b in self.buckets:
            all_contacts.extend(b.contacts)
        all_contacts.sort(key=lambda c: xor_distance(c.node_id, target))
        if pns:
            window = all_contacts[: max(n * 2, n)]
            window.sort(key=lambda c: (xor_distance(c.node_id, target), c.rtt_ms if c.rtt_ms > 0 else 1e9))
            return window[:n]
        return all_contacts[:n]
    def all_contacts(self) -> List[Contact]:
        out: List[Contact] = []
        for b in self.buckets:
            out.extend(b.contacts)
        return out
    def nonempty_buckets(self) -> List[KBucket]:
        return [b for b in self.buckets if b.contacts]
    def size(self) -> int:
        return sum(len(b) for b in self.buckets)
    def snapshot(self) -> Dict[str, object]:
        used = {str(b.index): len(b) for b in self.buckets if b.contacts}
        return {"contacts": self.size(), "used_buckets": len(used), "buckets": used}

def contacts_from_wire(items: Iterable[dict]) -> List[Contact]:
    out: List[Contact] = []
    for raw in items:
        try:
            out.append(Contact(
                node_id=bytes.fromhex(raw["node_id"]),
                public_key=bytes.fromhex(raw["public_key"]),
                last_seen=float(raw.get("last_seen") or time.time()),
                rtt_ms=float(raw.get("rtt_ms") or 0.0),
                name=str(raw.get("name") or ""),
                capabilities=list(raw.get("capabilities") or []),
            ))
        except (KeyError, ValueError):
            continue
    return out
