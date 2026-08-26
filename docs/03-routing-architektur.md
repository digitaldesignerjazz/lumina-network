# Kapitel 3 – Routing-Architektur

## 3.1 Kademlia-Ansatz

Lumina Network nutzt eine **Kademlia-basierte Distributed Hash Table (DHT)** als primäre Discovery- und Routing-Grundlage.

### Kernkonzepte

- **Node-ID**: 160-Bit (oder 256-Bit) Identifier, abgeleitet aus dem öffentlichen Schlüssel
- **XOR-Distanzmetrik**: `distance(a, b) = a ⊕ b`
- **k-Buckets**: Jeder Knoten hält bis zu `k` (typisch 20) Peers pro Distanz-Bucket
- **Iterative Lookup**: α parallele Anfragen (typisch α = 3) bis die k nächsten Knoten gefunden sind

### Lookup-Ablauf

1. Lokale k-Buckets nach den aktuell nächsten Knoten durchsuchen
2. α parallele `FIND_NODE` / `FIND_VALUE` Anfragen senden
3. Antworten in eine sortierte Kandidatenliste einfügen
4. Wiederholen, bis keine näheren Knoten mehr gefunden werden
5. Ergebnis: die k nächstgelegenen lebenden Knoten

## 3.2 Multi-Path-Routing

Über der reinen Kademlia-Distanz implementiert die **Routing Engine** echte Multi-Path-Fähigkeit:

- **Primärpfad**: niedrigste XOR-Distanz + beste aktuelle Metriken
- **Sekundärpfade**: 2–4 alternative Pfade mit disjunkten oder weitgehend disjunkten Knoten
- **Pfad-Auswahl**: dynamisch nach aktuellen Metriken (Latenz, Paketverlust, Bandbreite, Energie)
- **Path Diversity**: Vermeidung von Single Points of Failure durch geografische und topologische Diversität, soweit erkennbar

### Routing-Tabelle pro Ziel

Jeder Knoten hält für aktive Ziele eine kleine Tabelle:

| Ziel-ID | Primär-Nächste-Hops | Alternative-Nächste-Hops | Metriken | Letzte Aktualisierung |
|---------|---------------------|---------------------------|----------|-----------------------|

## 3.3 Routing-Metriken

Die Routing Engine bewertet Pfade anhand einer gewichteten Kombination aus:

| Metrik | Beschreibung | Gewicht (Beispiel) |
|--------|--------------|--------------------|
| **RTT / Latenz** | Round-Trip-Time | hoch |
| **Paketverlustrate** | Verlustquote der letzten Fenster | hoch |
| **Verfügbare Bandbreite** | geschätzt oder gemessen | mittel |
| **Energiekosten** | besonders relevant für mobile/Funk-Knoten | mittel–hoch |
| **Hop-Count** | Anzahl der Zwischenknoten | niedrig–mittel |
| **Vertrauens-/Reputation-Score** | aus Security Engine und Gossip | variabel |

Die exakte Gewichtung ist konfigurierbar und kann durch die **Iktrasier-Schwarmschicht** dezentral optimiert werden.

## 3.4 Selbstheilungs-Mechanismen

### Erkennung

- **HEARTBEAT**-Timeouts (konfigurierbar, typisch 15–30 s)
- Gossip-basierte Topologie-Updates
- Proaktive Path-Probing auf aktiven Multi-Path-Routen

### Reaktion

1. **Sofortige Umleitung** auf den besten verfügbaren Alternativpfad
2. **Re-Lookup** über Kademlia, wenn keine ausreichenden Alternativen mehr existieren
3. **Gossip-Benachrichtigung** an die Nachbarschaft über den ausgefallenen Knoten
4. **k-Bucket-Bereinigung** und Nachfüllung durch Discovery Engine
5. **Optionale Pfad-Reparatur**: gezielte Suche nach neuen disjunkten Pfaden

### Zusätzliche Robustheit

- **Redundante Speicherung** wichtiger Statusdaten über mehrere Kademlia-Knoten
- **Epidemic Gossip** für kritische Topologie-Änderungen
- **Graceful Degradation**: bei Partitionen arbeitet jede Komponente weiter mit den lokal verfügbaren Peers

## 3.5 Integration mit höheren Schichten

- Die **Security Engine** signiert und authentifiziert alle Routing-Nachrichten
- Die **Gossip Engine** transportiert Topologie- und Metrik-Updates
- **Iktrasier** kann global bessere Metrik-Gewichtungen und Path-Selection-Strategien vorschlagen und verbreiten
- KI-Agenten können Routing-Entscheidungen als Input für Orchestrierungsaufgaben nutzen

---
*Kapitel 3 – Routing-Architektur – bereit für Review und weitere Verfeinerung.*
