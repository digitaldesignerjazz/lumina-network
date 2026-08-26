# Chapter 5 – Yggdrasil Integration

Yggdrasil serves as the **primary transport underlay** for Lumina Network.

## 5.1 Why Yggdrasil?

- Fully decentralized, self-organizing IPv6 overlay mesh
- Cryptographic identities (Ed25519 / Curve25519)
- End-to-end encryption at the packet level
- Automatic self-healing and spanning-tree + DHT routing
- Stable, location-independent addresses in the `200::/7` range
- Already established in the Nexus ecosystem base (xMesh / NovaNet predecessor)

## 5.2 Architectural Layering

```
┌─────────────────────────────────────────────┐
│  Lumina Application / AI Agents / Iktrasier │
├─────────────────────────────────────────────┤
│  Lumina Message Layer (HELLO, GOSSIP, DATA…)│  ← Chapter 4
├─────────────────────────────────────────────┤
│  Lumina Routing Engine (Multi-Path + Kademlia)│ ← Chapter 3
├─────────────────────────────────────────────┤
│  Yggdrasil PacketConn / Session Layer       │  ← End-to-End Crypto + Routing
├─────────────────────────────────────────────┤
│  Yggdrasil Link Layer (TCP / TLS / QUIC / WS)│
├─────────────────────────────────────────────┤
│  Physical / virtual network                 │
└─────────────────────────────────────────────┘
```

## 5.3 Identity Mapping

| Lumina Concept          | Yggdrasil Equivalent                     |
|-------------------------|------------------------------------------|
| Node-ID (256-bit)       | SHA-512(PublicKey) or direct Ed25519 key |
| Public Key              | Yggdrasil Public Key                     |
| Address                 | Derived IPv6 address (`200:...`)         |
| Session Key             | Yggdrasil Session (ephemeral) + optional additional Lumina key |

Lumina nodes generate or import the same key used by the local Yggdrasil daemon. This keeps identity consistent.

## 5.4 Transport Usage

- Lumina messages are sent as **payload** over Yggdrasil sessions or the PacketConn.
- Recommended ports / services:
  - `lumina` service on a fixed UDP/TCP port over Yggdrasil (e.g. 4242)
  - Alternatively: custom stream protocol analogous to ygg_stream (TCP/KEY style)
- Discovery: Yggdrasil multicast + Lumina’s own Kademlia over already connected peers

## 5.5 Routing Synergy

- Yggdrasil already provides a robust, self-healing underlay path.
- The Lumina Routing Engine sits **on top** and can:
  - Use multiple Yggdrasil paths in parallel (multi-path)
  - Additionally consider its own metrics (energy, agent load, reputation)
  - Gracefully degrade during Yggdrasil partitions

## 5.6 Security Reinforcement

- Yggdrasil already encrypts every packet end-to-end.
- Lumina adds a second signature and optional AEAD layer (see Chapter 4).
- This creates defense-in-depth: even if a Yggdrasil session key were compromised, the Lumina contents remain protected and authenticated.

## 5.7 Configuration (Example)

```yaml
# lumina-node.yaml
yggdrasil:
  config: /etc/yggdrasil.conf
  listen: ["tcp://0.0.0.0:0", "tls://0.0.0.0:0"]
  peers: []                          # will be extended dynamically

lumina:
  bind_port: 4242
  node_id_from: yggdrasil            # derive identity from Yggdrasil key
  underlay: yggdrasil
```

## 5.8 Next Steps

- Binding to the official `yggdrasil-go` admin API or to `ironwood` / `yggdrasil-ng`
- Optional custom stream multiplexer (similar to ygg_stream)
- Integration of Lumina gossip updates into Yggdrasil NodeInfo

---
*Chapter 5 – Yggdrasil as the foundation of the Lumina Network transport layer.*
