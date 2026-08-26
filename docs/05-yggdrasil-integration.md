# Kapitel 5 – Yggdrasil-Integration

Yggdrasil dient als **primärer Transport-Underlay** für Lumina Network.

## 5.1 Warum Yggdrasil?

- Vollständig dezentrale, selbstorganisierende IPv6-Overlay-Mesh
- Kryptographische Identitäten (Ed25519 / Curve25519)
- End-to-End-Verschlüsselung auf Packet-Ebene
- Automatische Selbstheilung und spanning-tree + DHT Routing
- Stabile, location-independent Adressen im `200::/7`-Bereich
- Bereits in der Nexus-Ökosystem-Basis etabliert (xMesh / NovaNet-Vorläufer)

## 5.2 Architektur-Schichtung

```
┌─────────────────────────────────────────────┐
│  Lumina Application / KI-Agenten / Iktrasier │
├─────────────────────────────────────────────┤
│  Lumina Message Layer (HELLO, GOSSIP, DATA…) │  ← Kapitel 4
├─────────────────────────────────────────────┤
│  Lumina Routing Engine (Multi-Path + Kademlia)│  ← Kapitel 3
├─────────────────────────────────────────────┤
│  Yggdrasil PacketConn / Session Layer         │  ← End-to-End Crypto + Routing
├─────────────────────────────────────────────┤
│  Yggdrasil Link Layer (TCP / TLS / QUIC / WS) │
├─────────────────────────────────────────────┤
│  Physisches / virtuelles Netzwerk             │
└─────────────────────────────────────────────┘
```

## 5.3 Identitäts-Mapping

| Lumina-Konzept          | Yggdrasil-Äquivalent                     |
|-------------------------|------------------------------------------|
| Node-ID (256-Bit)       | SHA-512(PublicKey) oder direkter Ed25519-Key |
| Public Key              | Yggdrasil Public Key                     |
| Adresse                 | Abgeleitete IPv6-Adresse (`200:...`)     |
| Session-Key             | Yggdrasil Session (ephemeral) + optional zusätzlicher Lumina-Key |

Lumina-Nodes generieren oder importieren denselben Schlüssel, den auch der lokale Yggdrasil-Daemon verwendet. Dadurch ist die Identität konsistent.

## 5.4 Transport-Nutzung

- Lumina-Nachrichten werden als **Payload** über Yggdrasil-Sessions oder den PacketConn gesendet.
- Empfohlene Ports / Services:
  - `lumina` Service auf einem festen UDP/TCP-Port über Yggdrasil (z. B. 4242)
  - Alternativ: eigenes Stream-Protokoll analog zu ygg_stream (TCP/KEY-Stil)
- Discovery: Yggdrasil-Multicast + Lumina-eigene Kademlia über die bereits verbundenen Peers

## 5.5 Routing-Synergie

- Yggdrasil liefert bereits einen robusten, selbstheilenden Underlay-Pfad.
- Lumina-Routing Engine sitzt **darüber** und kann:
  - Mehrere Yggdrasil-Pfade parallel nutzen (Multi-Path)
  - Eigene Metriken (Energie, Agenten-Last, Reputation) zusätzlich berücksichtigen
  - Bei Yggdrasil-Partitionen graceful degrade

## 5.6 Sicherheits-Verstärkung

- Yggdrasil verschlüsselt bereits jedes Paket end-to-end.
- Lumina fügt eine zweite Signatur- und optionale AEAD-Schicht hinzu (siehe Kapitel 4).
- Dadurch entsteht Defense-in-Depth: selbst wenn ein Yggdrasil-Session-Key kompromittiert würde, bleiben die Lumina-Inhalte geschützt und authentifiziert.

## 5.7 Konfiguration (Beispiel)

```yaml
# lumina-node.yaml
yggdrasil:
  config: /etc/yggdrasil.conf
  listen: ["tcp://0.0.0.0:0", "tls://0.0.0.0:0"]
  peers: []                          # wird dynamisch ergänzt

lumina:
  bind_port: 4242
  node_id_from: yggdrasil            # Identität vom Yggdrasil-Key ableiten
  underlay: yggdrasil
```

## 5.8 Nächste Schritte

- Bindung an die offizielle `yggdrasil-go` Admin-API bzw. an `ironwood` / `yggdrasil-ng`
- Optionaler eigener Stream-Multiplexer (ähnlich ygg_stream)
- Integration der Lumina-Gossip-Updates in Yggdrasil-NodeInfo

---
*Kapitel 5 – Yggdrasil als Fundament der Lumina Network Transportschicht.*
