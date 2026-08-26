# Chapter 2 – Network Architecture

## Core Principles

- Decentralized peer-to-peer nodes
- Automatic peer discovery via Kademlia
- Self-healing in case of node failures
- Standardized message formats with header and digital signature

## Message Types

| Type | Purpose |
|------|---------|
| `HELLO` | Initial contact |
| `HEARTBEAT` | Liveness check |
| `GOSSIP` | Status and topology updates |
| `DATA` | Application payload |
| `ACK` | Acknowledgement |

## Layers above the Network

- **Agent layer** with swarm intelligence
- **Shared memory**
- **Evaluation and status streaming**
- **Gateway layer** for external systems

## Quality Goals

- High availability
- Low latency
- Energy efficiency
- Scalability
- Strong cryptography

---
*Foundation of the network architecture described.*
