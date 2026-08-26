# Kapitel 5 – Yggdrasil-Integration (Detail)

Yggdrasil dient als **primärer Transport-Underlay** für Lumina Network.

## 5.1 Warum Yggdrasil?

- Vollständig dezentrale, selbstorganisierende IPv6-Overlay-Mesh
- Kryptographische Identitäten (Ed25519)
- End-to-End-Verschlüsselung auf Packet-Ebene (via Ironwood)
- Automatische Selbstheilung und spanning-tree + DHT/Pathfinding
- Stabile, location-independent Adressen im `200::/7`-Bereich
- Bereits in der Nexus-Ökosystem-Basis etabliert

## 5.2 Architektur-Schichtung

```
┌─────────────────────────────────────────────┐
│  Lumina Application / KI-Agenten / Iktrasier │
├─────────────────────────────────────────────┤
│  Lumina Message Layer (HELLO, GOSSIP, DATA…) │  ← Kapitel 4
├─────────────────────────────────────────────┤
│  Lumina Routing Engine (Multi-Path + Kademlia)│  ← Kapitel 3
├─────────────────────────────────────────────┤
│  Optional: ygg_stream (TCP/KEY Multiplexer)  │
├─────────────────────────────────────────────┤
│  Ironwood PacketConn (encrypted)             │  ← End-to-End Crypto + Routing
├─────────────────────────────────────────────┤
│  Yggdrasil Link Layer (TCP / TLS / QUIC / WS)│
├─────────────────────────────────────────────┤
│  Physisches / virtuelles Netzwerk            │
└─────────────────────────────────────────────┘
```

## 5.3 Identitäts-Mapping & Schlüssel-Sharing

| Lumina-Konzept     | Yggdrasil / Ironwood Äquivalent              |
|--------------------|----------------------------------------------|
| Node-ID (256-Bit)  | SHA-256 oder SHA-512 des Public Keys         |
| Public Key         | Ed25519 Public Key (32 Byte)                 |
| Private Key        | Ed25519 Private Key (muss identisch sein)    |
| Adresse            | Abgeleitete IPv6 (`200:...`)                 |
| Session            | Ironwood encrypted session                   |

**Wichtige Regel:**  
Lumina und der Yggdrasil-Daemon (oder die eingebettete Ironwood-Instanz) **müssen denselben Ed25519-Schlüssel** verwenden. Dadurch ist die Identität netzwerkweit konsistent und die Adresse selbstzertifizierend.

## 5.4 Integrationswege

### Weg A – Externer Yggdrasil-Daemon + Admin API (einfachster Start)

Der klassische Weg: Yggdrasil läuft als separater Prozess. Lumina spricht über den **Admin Socket**.

- Standard: `unix:///var/run/yggdrasil.sock` oder `tcp://localhost:9001`
- Protokoll: JSON-Request + Newline, JSON-Response

Wichtige Admin-Befehle:

| Request          | Zweck                                      |
|------------------|--------------------------------------------|
| `getSelf`        | Eigene Adresse, Public Key, Coordinates    |
| `getPeers`       | Aktuelle Peers + Statistiken               |
| `getTree`        | Spanning-Tree-Einträge                     |
| `getPaths`       | Gecachte Pfade                             |
| `getSessions`    | Aktive verschlüsselte Sessions             |
| `addPeer`        | Dynamisch einen Peer hinzufügen            |
| `removePeer`     | Peer entfernen                             |

Beispiel-Request:
```json
{"request":"getSelf"}\n
```

Empfohlene Bibliotheken:
- Rust: `yggdrasilctl`
- Go: direkter Zugriff über `net.Conn` + JSON

### Weg B – Eingebettetes Ironwood / yggdrasil-ng (empfohlen für Produktion)

Für maximale Kontrolle und Performance wird **Ironwood** (das Routing + Encryption-Herz von Yggdrasil) direkt eingebettet.

- Go-Original: `github.com/Arceliar/ironwood`
- Rust-Port (aktiv): `Revertron/Yggdrasil-ng` → `crates/ironwood`

Vorteile:
- Kein separater Daemon nötig
- Direkter `PacketConn`-Zugriff (`ReadFrom` / `WriteTo` mit Public-Key-Adressen)
- Volle Kontrolle über Link-Management und Metriken

Minimalbeispiel (Rust-Stil):
```rust
let signing_key = SigningKey::generate(...);
let packet_conn = new_encrypted_packet_conn(signing_key, Config::default());
// packet_conn.write_to(payload, &remote_addr).await
// packet_conn.read_from(&mut buf).await
```

### Weg C – ygg_stream (TCP-ähnliche Streams über Ironwood)

Für anwendungsfreundliche Streams (zuverlässig, ordered, ports) empfiehlt sich **ygg_stream**:

- Bietet TCP-Semantik (3-Way-Handshake, Flow-Control, Congestion Control)
- Adressierung rein über Ed25519 Public Keys + Port
- Keine zusätzliche Verschlüsselung (nutzt Ironwood)

Ideal für die Lumina Message Layer, wenn man nicht selbst Fragmentierung und Reliability bauen will.

## 5.5 Transport von Lumina-Nachrichten

1. Lumina serialisiert die signierte Nachricht (Kapitel 4).
2. Die Bytes werden als Payload über:
   - Ironwood `WriteTo(remote_pubkey, payload)` oder
   - ygg_stream Connection / Datagram
   gesendet.
3. Empfänger liest über `ReadFrom` und parst den Lumina-Header.

Empfohlener fester Service-Port für Lumina: **4242** (über ygg_stream oder als eigenes Protokoll).

## 5.6 Discovery-Synergie

- Yggdrasil Multicast Discovery für lokale Peers
- Lumina Kademlia läuft **über** den bereits verbundenen Yggdrasil-Graphen
- Zusätzlich: Admin-API `getPeers` / `getTree` als Bootstrapping-Quelle für die Discovery Engine

## 5.7 Sicherheits-Verstärkung (Defense-in-Depth)

- Ironwood / Yggdrasil verschlüsselt bereits jedes Paket end-to-end.
- Lumina fügt eine **zweite** Ed25519-Signatur + optionale AEAD-Schicht hinzu.
- Selbst bei Kompromittierung einer Session bleiben Nachrichten authentifiziert und (bei AEAD) vertraulich.

## 5.8 Konfigurationsbeispiel (Hybrid)

```yaml
# lumina-node.yaml
yggdrasil:
  mode: embedded          # oder "external"
  admin_socket: "unix:///var/run/yggdrasil.sock"
  private_key_file: "/etc/lumina/node.key"   # derselbe Key für beide
  listen: ["tcp://0.0.0.0:0", "tls://0.0.0.0:0"]

lumina:
  bind_port: 4242
  underlay: ironwood      # oder ygg_stream / external
  node_id_from: yggdrasil
```

## 5.9 Empfohlene nächste Implementierungsschritte

1. Identity-Sharing-Modul (Key-Datei laden und sowohl an Ironwood als auch an Lumina Node Manager übergeben)
2. Admin-API-Client (für Monitoring und dynamisches Peering)
3. PacketConn-Adapter, der Lumina-Nachrichten als Payload transportiert
4. Optional: ygg_stream-Integration für zuverlässige Streams
5. Metriken-Export aus `getPeers` / `getSessions` in die Lumina Routing Engine

---
*Kapitel 5 – detaillierte Yggdrasil-Integration – Stand 2026-08-26*
