# Kapitel 7 – Kademlia-Implementierungsdetails

Dieses Kapitel spezifiziert die konkrete Kademlia-Implementierung für die **aktive Discovery** in Lumina Network (Meilenstein M0.2).

## 7.1 Grundparameter (Lumina-Defaults)

| Parameter              | Wert     | Begründung |
|------------------------|----------|------------|
| Identifier-Länge       | 256 Bit  | SHA-256 des Public Keys |
| `k` (Bucket-Größe)     | 20       | Klassischer Kademlia-Wert, gute Robustheit |
| `α` (Parallelität)     | 3        | Optimaler Trade-off zwischen Geschwindigkeit und Last |
| `β` (Antwort-Kontakte) | 20 (`k`) | Volle k-nächsten zurückgeben |
| Refresh-Intervall      | 60 min   | Bucket-Refresh |
| Lookup-Timeout         | 5–8 s    | Pro paralleler Runde |

## 7.2 XOR-Distanz

```text
distance(a, b) = a ⊕ b   (als Big-Endian Integer interpretiert)
```

Je kleiner der numerische Wert, desto „näher“ liegen die IDs.

## 7.3 k-Buckets

Jeder Knoten hält bis zu 256 k-Buckets (einen pro Bit-Präfix-Länge).

- Bucket `i` enthält Kontakte, deren Distanz im Bereich `[2^i , 2^{i+1})` liegt.
- Maximal `k = 20` Kontakte pro Bucket.
- Sortierung: **least-recently-seen first** (älteste zuerst).

### Einfüge- / Ersetzungsregeln

1. Bucket hat noch Platz → Kontakt einfach einfügen.
2. Bucket ist voll:
   - Den least-recently-seen Kontakt anpingen.
   - Antwortet er → neuer Kontakt wird verworfen (oder an das Ende gestellt).
   - Antwortet er nicht → least-recently-seen wird ersetzt.
3. Optional (Lumina-Erweiterung): Proximity-Neighbor-Selection (bevorzuge Kontakte mit besserer gemessener Latenz).

## 7.4 Iterativer Lookup (FIND_NODE)

```text
function iterativeFindNode(target):
    shortlist ← α nächste bekannte Kontakte aus den k-Buckets
    queried   ← leere Menge

    while true:
        // α parallele Anfragen an die noch nicht abgefragten nächsten Kontakte
        results ← parallel FIND_NODE(target) an α Kontakte aus shortlist \ queried

        queried ← queried ∪ angefragte Kontakte

        // Neue Kandidaten einfügen und nach Distanz sortieren
        shortlist ← (shortlist ∪ results).sort_by_distance(target).take(k)

        if keine näheren Kontakte mehr gefunden oder k erfolgreiche Antworten:
            return die k nächsten live-Kontakte
```

### Wichtige Eigenschaften

- **Loose Parallelism**: Die nächste Runde kann starten, sobald die ersten Antworten eintreffen (muss nicht auf alle α warten).
- Nodes, die nicht antworten, werden vorübergehend aus der Shortlist entfernt.
- Abbruch, wenn keine Verbesserung der Distanz mehr eintritt oder `k` live-Kontakte erreicht sind.

## 7.5 FIND_NODE Nachrichtenformat (Erweiterung Kapitel 4)

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

Maximal `k` Kontakte werden zurückgegeben, bereits nach Distanz zum Target sortiert.

## 7.6 Bucket-Refresh

- Alle 60 Minuten wird für jeden non-empty Bucket ein Lookup auf eine zufällige ID aus dem Bucket-Bereich durchgeführt.
- Dadurch bleiben die Buckets frisch und das Netzwerk entdeckt neue Knoten.

## 7.7 Integration in den Lumina-Prototyp

Im nächsten Schritt wird der bestehende `LuminaNode` um folgende Komponenten erweitert:

- `KBucket` / `RoutingTable`-Klasse
- `iterative_find_node(target_id)`-Methode
- Behandlung von `MSG_FIND_NODE` und `MSG_FIND_NODE_REPLY`
- Periodischer Bucket-Refresh-Timer

Passive Discovery (über Gossip) und aktive Discovery (Kademlia) bleiben bewusst getrennt, damit der Funkverkehr kontrollierbar bleibt.

---
*Kapitel 7 – Kademlia-Implementierungsdetails für M0.2*
