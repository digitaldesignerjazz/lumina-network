# Kapitel 7 – Kademlia-Implementierungsdetails

Aktive Discovery für Lumina Network (M0.2).

## 7.1 Defaults

256-Bit-IDs (SHA-256 des Public Keys), `k = 20`, `α = 3`, `β = k`, Refresh 60 min, Lookup-Timeout 5–8 s.

## 7.2 XOR und Bucket-Index

```text
distance(a, b) = a ⊕ b   (Big-Endian Integer)
bucket_index(0) = 0
bucket_index(d) = min(floor(log2(d)), 255)
```

## 7.3 k-Buckets

Bucket `i` hält Kontakte mit Distanz in `[2^i, 2^{i+1})`. Least-recently-seen first. Voller Bucket: LRS pingen, behalten wenn lebend, sonst ersetzen. PNS nur mit **lokal gemessener** RTT. Kein unsignierter Kontakt in die Tabelle.

## 7.4 Iterativer FIND_NODE

Loose Parallelism, stumme Nodes aus der Shortlist, Abbruch bei Distanz-Stagnation oder `k` Live-Kontakten.

## 7.5 Wire-Format

Request `0x10`: `{target, requester_id}`  
Reply `0x11`: `{target, contacts[]}` mit `node_id`, `public_key`, `last_seen`, `rtt_ms`, optional `name` / `capabilities`.

## 7.6 Refresh

Stündlicher Lookup in jedem nicht-leeren Bucket. Seltener Zufalls-Lookup in leere ferne Buckets, wenn das Netz wächst.

## 7.7 Stand im Prototyp

Umgesetzt in `prototypes/kademlia.py` und `prototypes/lumina_node.py` v0.3.0: RoutingTable, iterativer FIND_NODE, Handler für 0x10/0x11, LRS-Ping über HEARTBEAT.
Offen auf Lumina-OS: systemd-Refresh, echter async Loose-Parallelism, S/Kademlia-disjunkte Pfade.

---
*Kapitel 7 – M0.2 / Prototyp v0.3*
