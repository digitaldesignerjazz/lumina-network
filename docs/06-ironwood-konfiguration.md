# Kapitel 6 – Ironwood-Konfiguration (Detail)

Ironwood ist das Routing- und Verschlüsselungs-Herzstück von Yggdrasil und die empfohlene eingebettete Transportschicht für Lumina Network.

## 6.1 Überblick der Config-Optionen

Ironwood akzeptiert eine `Config`-Struktur (Rust) bzw. funktionale Optionen (Go). Die wichtigsten Parameter im Überblick:

| Parameter                    | Default          | Beschreibung |
|-----------------------------|------------------|--------------|
| `router_refresh`            | 4 Minuten        | Intervall, in dem der eigene Spanning-Tree-Announcement erneuert wird |
| `router_timeout`            | 5 Minuten        | Timeout, nach dem Tree-Infos eines Peers verfallen |
| `peer_keepalive_delay`      | 1 Sekunde        | Wartezeit, bevor ein Keepalive an einen idle Peer gesendet wird |
| `peer_timeout`              | 3 Sekunden       | Basis-Timeout, nach dem ein Peer als möglicherweise tot betrachtet wird |
| `peer_probe_count`          | 3                | Anzahl erlaubter stiller Intervalle, bevor der Peer endgültig entfernt wird |
| `peer_max_message_size`     | 1 MB             | Maximale Größe einer einzelnen Wire-Nachricht |
| `path_timeout`              | 1 Minute         | Timeout für gecachte Pfade |
| `path_throttle`             | 1 Sekunde        | Mindestabstand zwischen Lookups zum selben Ziel |
| `bloom_transform`           | None             | Optionale Transformation der Keys vor Bloom-Filter-Einfügung |
| `path_notify`               | None             | Callback, wenn ein neuer Pfad entdeckt wird |
| `group_password`            | None             | Optionaler Shared-Secret für Handshake (geschlossene Gruppen) |

**Gesamt-Liveness-Budget** ≈ `peer_timeout × peer_probe_count`  
(bei Defaults ca. 9 Sekunden Silence, bevor ein Peer abgebaut wird).

## 6.2 Empfohlene Einstellungen für Lumina

Für ein stabiles, aber reaktionsfreudiges Lumina-Netzwerk empfehle ich folgende Ausgangswerte:

```rust
use std::time::Duration;
use ironwood::Config;

let config = Config::default()
    .with_router_refresh(Duration::from_secs(3 * 60))      // etwas aggressiver
    .with_router_timeout(Duration::from_secs(4 * 60))
    .with_peer_keepalive_delay(Duration::from_millis(800))
    .with_peer_timeout(Duration::from_secs(4))
    .with_peer_probe_count(4)                              // tolerant gegenüber Verlust
    .with_peer_max_message_size(2 * 1024 * 1024)           // 2 MB für größere Gossip/DATA
    .with_path_timeout(Duration::from_secs(90))
    .with_path_throttle(Duration::from_millis(500));
```

### Begründung

- Etwas kürzere Tree-Refresh-Intervalle → schnellere Topologie-Anpassung
- Höheres `peer_probe_count` → bessere Toleranz gegen kurze Funk-/Mobilfunk-Aussetzer
- Größeres `peer_max_message_size` → erlaubt größere Lumina-GOSSIP- und DATA-Nachrichten ohne Fragmentierung
- Kürzeres `path_throttle` → schnellere Multi-Path-Reaktionen der Lumina Routing Engine

## 6.3 Go-Variante (Original Ironwood)

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

## 6.4 Path-Notify und Metriken-Anbindung

Der `path_notify`-Callback ist besonders wertvoll für Lumina:

```rust
let config = Config::default()
    .with_path_notify(|remote_key| {
        // Hier kann die Lumina Routing Engine sofort einen neuen Pfad registrieren
        // und Metriken (RTT, Verlust) aktualisieren.
    });
```

Damit kann die Multi-Path-Tabelle der Routing Engine in Echtzeit aktualisiert werden, sobald Ironwood einen neuen Pfad entdeckt.

## 6.5 Group Password (geschlossene Netze)

Für private Lumina-Cluster kann ein Shared Secret gesetzt werden:

```rust
let config = Config::default()
    .with_group_password(b"mein-lumina-geheimnis".to_vec());
```

Nur Knoten mit demselben Password können erfolgreiche Handshakes durchführen. Ideal für isolierte Test- oder Firmennetze.

## 6.6 Transport-Agnostizismus

Ironwood ist **transport-agnostisch**. Beliebige `AsyncRead + AsyncWrite`-Streams können übergeben werden:

- TCP / TLS / QUIC
- WebSocket
- UNIX-Sockets
- Eigene Funk- oder Mesh-Links

In Lumina werden die Links typischerweise über die höheren Yggdrasil-Link-Layer oder direkt verwaltet.

## 6.7 Empfohlene nächste Schritte

1. Identity-Sharing-Modul, das denselben Ed25519-Key an Ironwood und den Lumina Node Manager übergibt
2. Path-Notify-Hook in die Routing Engine einbinden
3. Adaptive Timeouts (falls die Rust-Version AdaptiveTimeoutConfig unterstützt) für mobile/Funk-Szenarien testen
4. Metriken aus `Debug`-Interfaces (GetPeers, GetPaths, GetSessions) in die Lumina Evaluation-Schicht exportieren

---
*Kapitel 6 – Ironwood-Konfiguration – detailliert für Lumina Network*
