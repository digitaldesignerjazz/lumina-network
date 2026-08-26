# Chapter 5 – Yggdrasil Integration (Detailed)

Yggdrasil serves as the **primary transport underlay** for Lumina Network.

## 5.1 Why Yggdrasil?

- Fully decentralized, self-organizing IPv6 overlay mesh
- Cryptographic identities (Ed25519)
- End-to-end encryption at the packet level (via Ironwood)
- Automatic self-healing and spanning-tree + DHT/pathfinding
- Stable, location-independent addresses in the `200::/7` range
- Already established in the Nexus ecosystem base

## 5.2 Architectural Layering

```
┌─────────────────────────────────────────────┐
│  Lumina Application / AI Agents / Iktrasier │
├─────────────────────────────────────────────┤
│  Lumina Message Layer (HELLO, GOSSIP, DATA…)│  ← Chapter 4
├─────────────────────────────────────────────┤
│  Lumina Routing Engine (Multi-Path + Kademlia)│ ← Chapter 3
├─────────────────────────────────────────────┤
│  Optional: ygg_stream (TCP/KEY multiplexer) │
├─────────────────────────────────────────────┤
│  Ironwood PacketConn (encrypted)            │  ← End-to-End Crypto + Routing
├─────────────────────────────────────────────┤
│  Yggdrasil Link Layer (TCP / TLS / QUIC / WS)│
├─────────────────────────────────────────────┤
│  Physical / virtual network                 │
└─────────────────────────────────────────────┘
```

## 5.3 Identity Mapping & Key Sharing

| Lumina Concept     | Yggdrasil / Ironwood Equivalent            |
|--------------------|--------------------------------------------|
| Node-ID (256-bit)  | SHA-256 or SHA-512 of the public key       |
| Public Key         | Ed25519 Public Key (32 bytes)              |
| Private Key        | Ed25519 Private Key (must be identical)    |
| Address            | Derived IPv6 (`200:...`)                   |
| Session            | Ironwood encrypted session                 |

**Important rule:**  
Lumina and the Yggdrasil daemon (or the embedded Ironwood instance) **must use the same Ed25519 key**. This keeps identity consistent network-wide and makes the address self-certifying.

## 5.4 Integration Paths

### Path A – External Yggdrasil Daemon + Admin API (easiest start)

Classic approach: Yggdrasil runs as a separate process. Lumina talks via the **Admin Socket**.

- Default: `unix:///var/run/yggdrasil.sock` or `tcp://localhost:9001`
- Protocol: JSON request + newline, JSON response

Important Admin commands:

| Request          | Purpose                                    |
|------------------|--------------------------------------------|
| `getSelf`        | Own address, public key, coordinates       |
| `getPeers`       | Current peers + statistics                 |
| `getTree`        | Spanning-tree entries                      |
| `getPaths`       | Cached paths                               |
| `getSessions`    | Active encrypted sessions                  |
| `addPeer`        | Dynamically add a peer                     |
| `removePeer`     | Remove a peer                              |

Example request:
```json
{"request":"getSelf"}\n
```

Recommended libraries:
- Rust: `yggdrasilctl`
- Go: direct `net.Conn` + JSON

### Path B – Embedded Ironwood / yggdrasil-ng (recommended for production)

For maximum control and performance, embed **Ironwood** (the routing + encryption heart of Yggdrasil) directly.

- Original Go: `github.com/Arceliar/ironwood`
- Active Rust port: `Revertron/Yggdrasil-ng` → `crates/ironwood`

Advantages:
- No separate daemon required
- Direct `PacketConn` access (`ReadFrom` / `WriteTo` with public-key addresses)
- Full control over link management and metrics

Minimal example (Rust style):
```rust
let signing_key = SigningKey::generate(...);
let packet_conn = new_encrypted_packet_conn(signing_key, Config::default());
// packet_conn.write_to(payload, &remote_addr).await
// packet_conn.read_from(&mut buf).await
```

### Path C – ygg_stream (TCP-like streams over Ironwood)

For application-friendly streams (reliable, ordered, ports) **ygg_stream** is recommended:

- Provides TCP semantics (3-way handshake, flow control, congestion control)
- Addressing purely via Ed25519 public keys + port
- No additional encryption (uses Ironwood)

Ideal for the Lumina Message Layer when you do not want to implement fragmentation and reliability yourself.

## 5.5 Transporting Lumina Messages

1. Lumina serializes the signed message (Chapter 4).
2. The bytes are sent as payload via:
   - Ironwood `WriteTo(remote_pubkey, payload)` or
   - ygg_stream Connection / Datagram
3. The receiver reads via `ReadFrom` and parses the Lumina header.

Recommended fixed service port for Lumina: **4242** (via ygg_stream or as a custom protocol).

## 5.6 Discovery Synergy

- Yggdrasil multicast discovery for local peers
- Lumina Kademlia runs **on top of** the already connected Yggdrasil graph
- Additionally: Admin API `getPeers` / `getTree` as a bootstrap source for the Discovery Engine

## 5.7 Security Reinforcement (Defense-in-Depth)

- Ironwood / Yggdrasil already encrypts every packet end-to-end.
- Lumina adds a **second** Ed25519 signature + optional AEAD layer.
- Even if a session is compromised, messages remain authenticated and (with AEAD) confidential.

## 5.8 Configuration Example (Hybrid)

```yaml
# lumina-node.yaml
yggdrasil:
  mode: embedded          # or "external"
  admin_socket: "unix:///var/run/yggdrasil.sock"
  private_key_file: "/etc/lumina/node.key"   # same key for both
  listen: ["tcp://0.0.0.0:0", "tls://0.0.0.0:0"]

lumina:
  bind_port: 4242
  underlay: ironwood      # or ygg_stream / external
  node_id_from: yggdrasil
```

## 5.9 Recommended Next Implementation Steps

1. Identity-sharing module (load key file and pass it to both Ironwood and Lumina Node Manager)
2. Admin API client (for monitoring and dynamic peering)
3. PacketConn adapter that transports Lumina messages as payload
4. Optional: ygg_stream integration for reliable streams
5. Metrics export from `getPeers` / `getSessions` into the Lumina Routing Engine

---
*Chapter 5 – detailed Yggdrasil integration – as of 2026-08-26*
