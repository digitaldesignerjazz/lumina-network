# Chapter 6 – Ironwood Configuration (Detailed)

Ironwood is the routing and encryption core of Yggdrasil and the recommended embedded transport layer for Lumina Network.

## 6.1 Overview of Config Options

Ironwood accepts a `Config` structure (Rust) or functional options (Go). Key parameters:

| Parameter                    | Default          | Description |
|-----------------------------|------------------|-------------|
| `router_refresh`            | 4 minutes        | How often the node refreshes its own spanning-tree announcement |
| `router_timeout`            | 5 minutes        | Timeout after which a peer’s tree info expires |
| `peer_keepalive_delay`      | 1 second         | Delay before sending a keepalive to an idle peer |
| `peer_timeout`              | 3 seconds        | Base timeout after which a peer is considered possibly dead |
| `peer_probe_count`          | 3                | Number of silent intervals allowed before the peer is finally removed |
| `peer_max_message_size`     | 1 MB             | Maximum size of a single wire message |
| `path_timeout`              | 1 minute         | Timeout for cached paths |
| `path_throttle`             | 1 second         | Minimum interval between lookups to the same destination |
| `bloom_transform`           | None             | Optional transform applied to keys before bloom-filter insertion |
| `path_notify`               | None             | Callback invoked when a new path is discovered |
| `group_password`            | None             | Optional shared secret for the handshake (closed groups) |

**Total liveness budget** ≈ `peer_timeout × peer_probe_count`  
(with defaults ≈ 9 seconds of silence before a peer is torn down).

## 6.2 Recommended Settings for Lumina

For a stable yet responsive Lumina network the following starting values are recommended:

```rust
use std::time::Duration;
use ironwood::Config;

let config = Config::default()
    .with_router_refresh(Duration::from_secs(3 * 60))      // slightly more aggressive
    .with_router_timeout(Duration::from_secs(4 * 60))
    .with_peer_keepalive_delay(Duration::from_millis(800))
    .with_peer_timeout(Duration::from_secs(4))
    .with_peer_probe_count(4)                              // tolerant of loss
    .with_peer_max_message_size(2 * 1024 * 1024)           // 2 MB for larger Gossip/DATA
    .with_path_timeout(Duration::from_secs(90))
    .with_path_throttle(Duration::from_millis(500));
```

### Rationale

- Slightly shorter tree-refresh intervals → faster topology adaptation
- Higher `peer_probe_count` → better tolerance of short radio / mobile dropouts
- Larger `peer_max_message_size` → allows larger Lumina GOSSIP and DATA messages without fragmentation
- Shorter `path_throttle` → faster multi-path reactions by the Lumina Routing Engine

## 6.3 Go Variant (Original Ironwood)

```go
import (
    "time"
    "github.com/Arceliar/ironwood/network"
    "github.com/Arceliar/ironwood/encrypted"
)

pc, err := encrypted.NewPacketConn(
    privateKey,
    network.WithRouterRefresh(3*time.Minute),
    network.WithRouterTimeout(4*time.Minute),
    network.WithPeerKeepAliveDelay(800*time.Millisecond),
    network.WithPeerTimeout(4*time.Second),
    network.WithPeerMaxMessageSize(2*1024*1024),
    network.WithPathTimeout(90*time.Second),
    network.WithPathThrottle(500*time.Millisecond),
    // network.WithBloomTransform(...),
    // network.WithPathNotify(func(key ed25519.PublicKey) { ... }),
)
```

## 6.4 Path-Notify and Metrics Integration

The `path_notify` callback is especially valuable for Lumina:

```rust
let config = Config::default()
    .with_path_notify(|remote_key| {
        // Here the Lumina Routing Engine can immediately register a new path
        // and update metrics (RTT, loss).
    });
```

This allows the multi-path table of the Routing Engine to be updated in real time as soon as Ironwood discovers a new path.

## 6.5 Group Password (Closed Networks)

For private Lumina clusters a shared secret can be set:

```rust
let config = Config::default()
    .with_group_password(b"my-lumina-secret".to_vec());
```

Only nodes with the same password can complete successful handshakes. Ideal for isolated test or corporate networks.

## 6.6 Transport Agnosticism

Ironwood is **transport-agnostic**. Any `AsyncRead + AsyncWrite` stream can be passed:

- TCP / TLS / QUIC
- WebSocket
- UNIX sockets
- Custom radio or mesh links

In Lumina the links are typically managed by the higher Yggdrasil link layer or directly.

## 6.7 Recommended Next Steps

1. Identity-sharing module that passes the same Ed25519 key to both Ironwood and the Lumina Node Manager
2. Wire the path-notify hook into the Routing Engine
3. Test adaptive timeouts (if the Rust version supports AdaptiveTimeoutConfig) for mobile/radio scenarios
4. Export metrics from the Debug interfaces (GetPeers, GetPaths, GetSessions) into the Lumina Evaluation layer

---
*Chapter 6 – Ironwood Configuration – detailed for Lumina Network*
