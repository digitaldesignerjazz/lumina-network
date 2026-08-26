# Chapter 4 – Message Formats in Detail

All Lumina messages follow a uniform signed Header + Body scheme.  
They are transported as payload over the Yggdrasil transport (or other underlays).

## 4.1 Common Header (32–96 Bytes)

```
Offset  Size    Field                 Description
------  ------  --------------------  --------------------------------------------
0       2       magic                 0x4C4E  ("LN")
2       1       version               Protocol version (currently 0x01)
3       1       msg_type              Message type (see table)
4       2       flags                 Bit flags (e.g. encrypted, compressed, priority)
6       4       length                Total length of the body in bytes
10      8       timestamp             Unix nanoseconds (sender)
18      8       msg_id                Unique 64-bit message ID
26      32      sender_id             256-bit Node-ID (public key hash)
58      64      signature             Ed25519 signature over Header+Body (excluding the signature itself)
```

- **Magic + Version** enable fast filtering and forward compatibility.
- **msg_id** is used for deduplication and ACK matching.
- **signature** is computed with the sender’s private key (Ed25519).
- Optional **encrypted** flag: Body is then encrypted with the session key (from Security Engine).

## 4.2 Message Types

| Code | Name            | Direction | Purpose |
|------|-----------------|-----------|---------|
| 0x01 | HELLO           | →         | Initial contact + node info |
| 0x02 | HEARTBEAT       | ↔         | Liveness + basic metrics |
| 0x03 | GOSSIP          | →         | Status, topology and metric updates |
| 0x04 | DATA            | →         | Application payload |
| 0x05 | ACK             | ←         | Acknowledgement of a previous message |
| 0x10 | FIND_NODE       | →         | Kademlia lookup |
| 0x11 | FIND_NODE_REPLY | ←         | Reply to FIND_NODE |
| 0x20 | PATH_PROBE      | ↔         | Multi-path quality probe |

## 4.3 Body Structures

### HELLO (0x01)
```json
{
  "node_id": "hex256",
  "public_key": "hex32",
  "ygg_address": "200:...",
  "capabilities": ["routing", "gossip", "agent", "gateway"],
  "software_version": "0.1.0",
  "listen_ports": {"lumina": 4242},
  "timestamp": 1724630000000000000
}
```

### HEARTBEAT (0x02)
```json
{
  "uptime_s": 3600,
  "load": 0.23,
  "peer_count": 12,
  "metrics": {
    "avg_rtt_ms": 18.4,
    "packet_loss": 0.002
  },
  "seq": 4821
}
```

### GOSSIP (0x03)
```json
{
  "origin_id": "hex256",
  "seq": 193,
  "ttl": 8,
  "updates": [
    {
      "type": "peer_up" | "peer_down" | "metric" | "topology",
      "node_id": "hex256",
      "data": { ... }
    }
  ]
}
```

### DATA (0x04)
```json
{
  "content_type": "application/octet-stream" | "text/plain" | "agent/task" | ...,
  "payload": "base64...",
  "priority": 0-7,
  "ttl_hops": 16
}
```

### ACK (0x05)
```json
{
  "acked_msg_id": 1234567890123456789,
  "status": "ok" | "error" | "duplicate",
  "error_code": null | 1-255
}
```

## 4.4 Signature and Encryption

1. Header (without signature field) + Body are serialized (CBOR or JSON, depending on flag).
2. Ed25519 signature is computed over the entire byte stream and written into the signature field.
3. When the `encrypted` flag is set, the body is first encrypted with an AEAD key (ChaCha20-Poly1305) derived from the shared secret (X25519).

## 4.5 Wire Format Recommendation

- **CBOR** as standard serialization (compact, binary-friendly).
- Fallback JSON for debugging and gateway layer.
- Maximum message size: 64 KiB (Yggdrasil-friendly); larger payloads via fragmentation or a stream protocol.

---
*Chapter 4 – Message Formats – ready for implementation.*
