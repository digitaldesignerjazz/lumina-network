# Chapter 7 – Kademlia Implementation Details

This chapter specifies the concrete Kademlia implementation for **active discovery** in Lumina Network (Milestone M0.2).

## 7.1 Base Parameters (Lumina Defaults)

| Parameter              | Value    | Rationale |
|------------------------|----------|-----------|
| Identifier length      | 256 bit  | SHA-256 of the public key |
| `k` (bucket size)      | 20       | Classic Kademlia value, good robustness |
| `α` (parallelism)      | 3        | Optimal trade-off between speed and load |
| `β` (returned contacts)| 20 (`k`) | Return full set of k closest |
| Refresh interval       | 60 min   | Bucket refresh |
| Lookup timeout         | 5–8 s    | Per parallel round |

## 7.2 XOR Distance

```text
distance(a, b) = a ⊕ b   (interpreted as big-endian integer)
```

The smaller the numeric value, the “closer” the IDs are.

## 7.3 k-Buckets

Each node maintains up to 256 k-buckets (one per bit-prefix length).

- Bucket `i` holds contacts whose distance lies in the range `[2^i , 2^{i+1})`.
- Maximum `k = 20` contacts per bucket.
- Ordering: **least-recently-seen first**.

### Insertion / Replacement Rules

1. Bucket still has free slots → simply insert the contact.
2. Bucket is full:
   - Ping the least-recently-seen contact.
   - If it replies → new contact is discarded (or moved to the end).
   - If it does not reply → replace the least-recently-seen contact.
3. Optional (Lumina extension): Proximity Neighbor Selection (prefer contacts with better measured latency).

## 7.4 Iterative Lookup (FIND_NODE)

```text
function iterativeFindNode(target):
    shortlist ← α closest known contacts from the k-buckets
    queried   ← empty set

    while true:
        // α parallel requests to the still unqueried closest contacts
        results ← parallel FIND_NODE(target) to α contacts from shortlist \ queried

        queried ← queried ∪ queried contacts

        // Insert new candidates and sort by distance
        shortlist ← (shortlist ∪ results).sort_by_distance(target).take(k)

        if no closer contacts found or k successful replies:
            return the k closest live contacts
```

### Important Properties

- **Loose Parallelism**: The next round may start as soon as the first replies arrive (does not have to wait for all α).
- Nodes that do not reply are temporarily removed from the shortlist.
- Termination when no further distance improvement occurs or `k` live contacts have been reached.

## 7.5 FIND_NODE Message Format (Extension of Chapter 4)

**Request (0x10)**
```json
{
  "target": "hex256",
  "requester_id": "hex256"
}
```

**Reply (0x11)**
```json
{
  "target": "hex256",
  "contacts": [
    {
      "node_id": "hex256",
      "public_key": "hex32",
      "last_seen": 1724630000,
      "rtt_ms": 14.2
    },
    ...
  ]
}
```

At most `k` contacts are returned, already sorted by distance to the target.

## 7.6 Bucket Refresh

- Every 60 minutes a lookup is performed for a random ID in the range of each non-empty bucket.
- This keeps the buckets fresh and allows the network to discover new nodes.

## 7.7 Integration into the Lumina Prototype

In the next step the existing `LuminaNode` will be extended with:

- `KBucket` / `RoutingTable` class
- `iterative_find_node(target_id)` method
- Handling of `MSG_FIND_NODE` and `MSG_FIND_NODE_REPLY`
- Periodic bucket-refresh timer

Passive discovery (via Gossip) and active discovery (Kademlia) remain deliberately separated so that radio traffic stays controllable.

---
*Chapter 7 – Kademlia Implementation Details for M0.2*
