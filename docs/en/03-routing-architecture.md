# Chapter 3 – Routing Architecture

## 3.1 Kademlia Approach

Lumina Network uses a **Kademlia-based Distributed Hash Table (DHT)** as the primary foundation for discovery and routing.

### Core Concepts

- **Node-ID**: 160-bit (or 256-bit) identifier derived from the public key
- **XOR Distance Metric**: `distance(a, b) = a ⊕ b`
- **k-Buckets**: Each node maintains up to `k` (typically 20) peers per distance bucket
- **Iterative Lookup**: α parallel queries (typically α = 3) until the k closest nodes are found

### Lookup Process

1. Search local k-buckets for the currently closest nodes
2. Send α parallel `FIND_NODE` / `FIND_VALUE` requests
3. Insert responses into a sorted candidate list
4. Repeat until no closer nodes are found
5. Result: the k closest living nodes

## 3.2 Multi-Path Routing

Above pure Kademlia distance, the **Routing Engine** implements true multi-path capability:

- **Primary path**: lowest XOR distance + best current metrics
- **Secondary paths**: 2–4 alternative paths with disjoint or largely disjoint nodes
- **Path selection**: dynamic according to current metrics (latency, packet loss, bandwidth, energy)
- **Path Diversity**: avoidance of single points of failure through geographic and topological diversity where detectable

### Routing Table per Destination

Each node maintains a small table for active destinations:

| Destination ID | Primary Next Hops | Alternative Next Hops | Metrics | Last Update |
|----------------|-------------------|-----------------------|---------|-------------|

## 3.3 Routing Metrics

The Routing Engine evaluates paths using a weighted combination of:

| Metric | Description | Weight (example) |
|--------|-------------|------------------|
| **RTT / Latency** | Round-trip time | high |
| **Packet loss rate** | Loss ratio of recent windows | high |
| **Available bandwidth** | estimated or measured | medium |
| **Energy cost** | especially relevant for mobile/radio nodes | medium–high |
| **Hop count** | number of intermediate nodes | low–medium |
| **Trust / Reputation score** | from Security Engine and Gossip | variable |

The exact weighting is configurable and can be optimized in a decentralized manner by the **Iktrasier swarm layer**.

## 3.4 Self-Healing Mechanisms

### Detection

- **HEARTBEAT** timeouts (configurable, typically 15–30 s)
- Gossip-based topology updates
- Proactive path probing on active multi-path routes

### Reaction

1. **Immediate failover** to the best available alternative path
2. **Re-lookup** via Kademlia when insufficient alternatives remain
3. **Gossip notification** to the neighborhood about the failed node
4. **k-Bucket cleanup** and refill by the Discovery Engine
5. **Optional path repair**: targeted search for new disjoint paths

### Additional Robustness

- **Redundant storage** of important status data across multiple Kademlia nodes
- **Epidemic Gossip** for critical topology changes
- **Graceful degradation**: in case of partitions each component continues with locally available peers

## 3.5 Integration with Higher Layers

- The **Security Engine** signs and authenticates all routing messages
- The **Gossip Engine** transports topology and metric updates
- **Iktrasier** can propose and disseminate globally better metric weightings and path-selection strategies
- AI agents can use routing decisions as input for orchestration tasks

---
*Chapter 3 – Routing Architecture – ready for review and further refinement.*
