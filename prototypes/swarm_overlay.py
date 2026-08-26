#!/usr/bin/env python3
"""Lumina Network – Schwarm-Overlay (M0.3 Prototyp)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

ROLE_LUMIA = "lumia"
ROLE_ELARA = "elara"
ROLE_LYRA = "lyra"
ROLE_XEN = "xen"
ROLE_ALIASES = {ROLE_LUMIA: ROLE_ELARA, ROLE_ELARA: ROLE_ELARA}
CAP_ORCHESTRATE = "swarm.orchestrate"
CAP_EMOTION = "swarm.emotion"
CAP_ANALYZE = "swarm.analyze"
CAP_GATEWAY = "swarm.gateway"
CAP_MEMORY = "swarm.memory"
ROLE_CAPS = {
    ROLE_ELARA: [CAP_ORCHESTRATE, CAP_GATEWAY, CAP_MEMORY, "routing", "gossip", "agent"],
    ROLE_LYRA: [CAP_EMOTION, CAP_MEMORY, "gossip", "agent"],
    ROLE_XEN: [CAP_ANALYZE, "routing", "gossip", "agent"],
}

def normalize_role(role: str) -> str:
    r = (role or "").strip().lower()
    return ROLE_ALIASES.get(r, r)

@dataclass
class AgentPresence:
    role: str
    node_id: bytes
    public_key: bytes
    name: str
    capabilities: List[str] = field(default_factory=list)
    last_seen: float = 0.0
    def as_update(self) -> dict:
        return {
            "type": "agent_up",
            "node_id": self.node_id.hex(),
            "data": {
                "role": self.role,
                "name": self.name,
                "public_key": self.public_key.hex(),
                "capabilities": list(self.capabilities),
            },
        }

class SwarmDirectory:
    def __init__(self):
        self.by_role: Dict[str, List[AgentPresence]] = {}
        self.by_node: Dict[bytes, AgentPresence] = {}
    def upsert(self, presence: AgentPresence) -> None:
        role = normalize_role(presence.role)
        presence.role = role
        self.by_node[presence.node_id] = presence
        bucket = [p for p in self.by_role.get(role, []) if p.node_id != presence.node_id]
        bucket.append(presence)
        self.by_role[role] = bucket
    def ingest_gossip(self, updates: List[dict]) -> List[AgentPresence]:
        found: List[AgentPresence] = []
        for u in updates or []:
            if u.get("type") != "agent_up":
                continue
            data = u.get("data") or {}
            try:
                p = AgentPresence(
                    role=normalize_role(str(data.get("role") or "")),
                    node_id=bytes.fromhex(u["node_id"]),
                    public_key=bytes.fromhex(data.get("public_key") or ""),
                    name=str(data.get("name") or ""),
                    capabilities=list(data.get("capabilities") or []),
                )
            except (KeyError, ValueError):
                continue
            if not p.role or not p.public_key:
                continue
            self.upsert(p)
            found.append(p)
        return found
    def nearest_role(self, role: str) -> Optional[AgentPresence]:
        role = normalize_role(role)
        peers = self.by_role.get(role) or []
        return peers[0] if peers else None
    def summary(self) -> Dict[str, int]:
        return {role: len(peers) for role, peers in sorted(self.by_role.items())}

def capabilities_for(role: str) -> List[str]:
    return list(ROLE_CAPS.get(normalize_role(role), ["agent", "gossip"]))
