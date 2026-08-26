# Prototypen

Lauffähige Spezifikations-Kerne für M0.2 (Kademlia) und M0.3 (Schwarm-Overlay).

| Datei | Rolle |
|-------|--------|
| `kademlia.py` | XOR-256, k-Buckets, RoutingTable, PNS-Option, Wire-Kontakte |
| `lumina_node.py` | Signierter Node v0.3.0, FIND_NODE iterativ, Gossip, simuliertes Ironwood |
| `swarm_overlay.py` | Agentenrollen Lumia/Elara · Lyra · Xen über das Mesh |

## Start

```bash
pip install pynacl
cd prototypes
python lumina_node.py
```

Der Demo startet vier Knoten (Lumia, Lyra, Xen, Hannover), bootstrapped per HELLO, verkündet den Schwarm per Gossip und führt einen iterativen FIND_NODE aus.

Passive Discovery bleibt Gossip. Aktive Discovery ist Kademlia. Der Schwarm hängt als Capability-Schicht darüber.
