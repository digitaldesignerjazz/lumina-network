# Lumina Network

**Decentralized Peer-to-Peer Mesh Network Architecture**  
Part of the Nexus / Lumina OS ecosystem

**Dezentrale Peer-to-Peer Mesh-Netzwerkarchitektur**  
Teil des Nexus / Lumina OS Ökosystems

Lumina Network is the signed overlay between Yggdrasil/Ironwood and the living agents on Lumina OS.  
It does not replace the OS and it does not replace the swarm — it lets both find each other.

## Overview / Überblick

Lumina Network is a modular, self-healing P2P network featuring:

- Kademlia-based discovery (256-bit IDs, k=20, α=3)
- Gossip protocol for status, topology and agent presence
- Multi-path routing
- Strong cryptography (Ed25519-signed messages)
- Swarm intelligence layer (Iktrasier)
- AI agent orchestration (Lumia/Elara · Lyra · Xen)
- Gateway layer for external systems
- **Yggdrasil / Ironwood as primary transport underlay**

## Place in the stack / Platz im Stapel

```
Schwarm     LuminaCyberspace   Elara/Lumia · Lyra · Xen
Runtime     Lumina-OS         Debian + systemd + Nexus Core
Overlay     lumina-network    Kademlia + Gossip + Caps
Underlay    Yggdrasil         permanente Maschinenidentität
```

Details: [Kapitel 8 – Ökosystem](docs/08-oekosystem.md) · [Chapter 8 – Ecosystem](docs/en/08-ecosystem.md)

## Documentation / Dokumentation

| Chapter | German | English | Status |
|---------|--------|---------|--------|
| 1 | [Systemarchitektur](docs/01-systemarchitektur.md) | [System Architecture](docs/en/01-system-architecture.md) | ✅ |
| 2 | [Netzwerkarchitektur](docs/02-netzwerkarchitektur.md) | [Network Architecture](docs/en/02-network-architecture.md) | ✅ |
| 3 | [Routing-Architektur](docs/03-routing-architektur.md) | [Routing Architecture](docs/en/03-routing-architecture.md) | ✅ |
| 4 | [Nachrichtenformate im Detail](docs/04-nachrichtenformate.md) | [Message Formats in Detail](docs/en/04-message-formats.md) | ✅ |
| 5 | [Yggdrasil-Integration](docs/05-yggdrasil-integration.md) | [Yggdrasil Integration](docs/en/05-yggdrasil-integration.md) | ✅ |
| 6 | [Ironwood-Konfiguration](docs/06-ironwood-konfiguration.md) | [Ironwood Configuration](docs/en/06-ironwood-configuration.md) | ✅ |
| 7 | [Kademlia-Implementierungsdetails](docs/07-kademlia-implementierungsdetails.md) | [Kademlia Implementation Details](docs/en/07-kademlia-implementation-details.md) | ✅ |
| 8 | [Ökosystem](docs/08-oekosystem.md) | [Ecosystem](docs/en/08-ecosystem.md) | ✅ |

## Code Prototypes / Code-Prototypen

| Path | Version | Description |
|------|---------|-------------|
| `prototypes/kademlia.py` | M0.2 | RoutingTable, k-Buckets, XOR-256 |
| `prototypes/lumina_node.py` | v0.3.0 | Signierter Node + iterativer FIND_NODE |
| `prototypes/swarm_overlay.py` | M0.3 | Agent-Presence für Lumia/Elara · Lyra · Xen |

```bash
pip install pynacl
python prototypes/lumina_node.py
```

## Related / Verwandt

- [Lumina-OS](https://github.com/digitaldesignerjazz/Lumina-OS)
- [LuminaCyberspace](https://github.com/digitaldesignerjazz/LuminaCyberspace)
- [luminaos](https://github.com/digitaldesignerjazz/luminaos)
- [nexus](https://github.com/digitaldesignerjazz/nexus)

## Quality Goals / Qualitätsziele

- High availability
- Low latency
- Energy efficiency
- Scalability
- Strong cryptography

---
*Public core of the Lumina Network specification · Esslinger Consulting · Hannover*
