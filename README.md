# Lumina Network

**Decentralized Peer-to-Peer Mesh Network Architecture**  
Part of the Nexus / Lumina OS ecosystem

**Dezentrale Peer-to-Peer Mesh-Netzwerkarchitektur**  
Teil des Nexus / Lumina OS Ökosystems

## Overview / Überblick

Lumina Network is a modular, self-healing P2P network featuring:
- Kademlia-based discovery
- Gossip protocol for status & topology
- Multi-path routing
- Strong cryptography
- Swarm intelligence layer (Iktrasier)
- AI agent orchestration
- Gateway layer for external systems
- **Yggdrasil / Ironwood as primary transport underlay**

## Documentation / Dokumentation

| Chapter | German | English | Status |
|---------|--------|---------|--------|
| 1 | [Systemarchitektur](docs/01-systemarchitektur.md) | [System Architecture](docs/en/01-system-architecture.md) | ✅ |
| 2 | [Netzwerkarchitektur](docs/02-netzwerkarchitektur.md) | [Network Architecture](docs/en/02-network-architecture.md) | ✅ |
| 3 | [Routing-Architektur](docs/03-routing-architektur.md) | [Routing Architecture](docs/en/03-routing-architecture.md) | ✅ |
| 4 | [Nachrichtenformate im Detail](docs/04-nachrichtenformate.md) | [Message Formats in Detail](docs/en/04-message-formats.md) | ✅ |
| 5 | [Yggdrasil-Integration](docs/05-yggdrasil-integration.md) | [Yggdrasil Integration](docs/en/05-yggdrasil-integration.md) | ✅ |
| 6 | [Ironwood-Konfiguration](docs/06-ironwood-konfiguration.md) | [Ironwood Configuration](docs/en/06-ironwood-configuration.md) | ✅ |

## Code Prototypes / Code-Prototypen

| Path | Description |
|------|-------------|
| `prototypes/lumina_node.py` | First minimal node skeleton (message formats + simulated Yggdrasil layer) |

## Quality Goals / Qualitätsziele

- High availability
- Low latency
- Energy efficiency
- Scalability
- Strong cryptography

---
*This repository serves as the public core of the Lumina Network specification.*
