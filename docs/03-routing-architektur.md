# Kapitel 3 – Routing-Architektur

## 3.1 Kademlia-Ansatz

Lumina Network nutzt eine Kademlia-DHT als primäre Discovery- und Routing-Grundlage.

- **Node-ID**: fest **256 Bit**, `SHA-256(Ed25519-Public-Key)` — keine 160-Bit-Variante
- **XOR-Distanz**: `distance(a, b) = a ⊕ b` (Big-Endian-Integer)
- **k-Buckets**: `k = 20`, Index `i = floor(log2(xor))`
- **Iterative Lookup**: `α = 3` parallele `FIND_NODE`-Anfragen
- **FIND_VALUE** gehört nicht zu M0.2

## 3.2 Multi-Path-Routing

Über der XOR-Distanz hält die Routing Engine 2–4 alternative Next-Hops pro aktivem Ziel, bewertet nach lokal gemessenen Metriken (RTT, Verlust, Bandbreite, Energie, Hop-Count, Reputation).

## 3.3 Selbstheilung

HEARTBEAT-Timeouts, Gossip-Topologie und Path-Probes lösen Failover, Kademlia-Re-Lookup und Bucket-Bereinigung aus.

## 3.4 Höhere Schichten

Signierte Routing-Nachrichten, Gossip für Topologie und `agent_up`, Iktrasier für Metrik-Gewichte. Der Schwarm (Lumia/Elara, Lyra, Xen) nutzt dieselben Node-IDs als Capability-Träger — Kapitel 8.

---
*Kapitel 3 – 256-Bit-ID fest, FIND_VALUE aus M0.2 entfernt.*
