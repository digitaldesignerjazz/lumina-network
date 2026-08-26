# Chapter 1 – System Architecture

The system architecture of Lumina (Blumina) is modular and consists of several layers:

```
Applications
    ↓
APIs and Services
    ↓
Routing (Kademlia + Gossip)
    ↓
Transport (radio / network media)
```

## Core Modules

Several modules work together at the core:

| Module | Responsibility |
|--------|----------------|
| **Node Manager** | Identity and key management |
| **Discovery Engine** | Peer search (Kademlia) |
| **Gossip Engine** | Distribution of status and topology updates |
| **Routing Engine** | Multi-path routing |
| **Security Engine** | Authentication and encryption |

## Higher Layers

- **AI Agents with Orchestration** – coordinate tasks in a decentralized manner
- **Memory, Evaluation and Status Streaming** – keep knowledge, quality and network state continuously available
- **Gateway Layer** – enables connection of external systems
- **Iktrasier** – swarm intelligence layer for decentralized optimizations

---
*Foundation of the entire Lumina Network architecture.*
