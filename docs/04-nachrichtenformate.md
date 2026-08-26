# Kapitel 4 – Nachrichtenformate im Detail

Alle Lumina-Nachrichten folgen einem einheitlichen, signierten Header + Body Schema.  
Sie werden als Payload über den Yggdrasil-Transport (oder andere Underlays) transportiert.

## 4.1 Gemeinsamer Header (32–96 Bytes)

```
Offset  Größe   Feld                  Beschreibung
------  ------  --------------------  --------------------------------------------
0       2       magic                 0x4C4E  ("LN")
2       1       version               Protokollversion (aktuell 0x01)
3       1       msg_type              Nachrichtentyp (siehe Tabelle)
4       2       flags                 Bitflags (z. B. encrypted, compressed, priority)
6       4       length                Gesamtlänge des Bodies in Bytes
10      8       timestamp             Unix-Nanosekunden (Sender)
18      8       msg_id                Eindeutige 64-Bit Nachrichten-ID
26      32      sender_id             256-Bit Node-ID (Public-Key-Hash)
58      64      signature             Ed25519-Signatur über Header+Body (ohne signature selbst)
```

- **Magic + Version** ermöglichen schnelles Filtern und Forward-Kompatibilität.
- **msg_id** dient der Deduplizierung und dem ACK-Matching.
- **signature** wird mit dem privaten Schlüssel des Absenders berechnet (Ed25519).
- Optionaler **encrypted**-Flag: Body ist dann mit dem Session-Key (aus Security Engine) verschlüsselt.

## 4.2 Nachrichtentypen

| Code | Name       | Richtung     | Zweck |
|------|------------|--------------|-------|
| 0x01 | HELLO      | →            | Initiale Kontaktaufnahme + Node-Info |
| 0x02 | HEARTBEAT  | ↔            | Lebendigkeit + aktuelle Metriken |
| 0x03 | GOSSIP     | →            | Status-, Topologie- und Metrik-Updates |
| 0x04 | DATA       | →            | Nutzdaten / Anwendungs-Payload |
| 0x05 | ACK        | ←            | Bestätigung einer vorherigen Nachricht |
| 0x10 | FIND_NODE  | →            | Kademlia-Lookup |
| 0x11 | FIND_NODE_REPLY | ←       | Antwort auf FIND_NODE |
| 0x20 | PATH_PROBE | ↔            | Multi-Path-Qualitätsprüfung |

## 4.3 Body-Strukturen

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

## 4.4 Signatur und Verschlüsselung

1. Header (ohne signature-Feld) + Body werden serialisiert (CBOR oder JSON, je nach Flag).
2. Ed25519-Signatur wird über den gesamten Byte-Stream berechnet und in das signature-Feld geschrieben.
3. Bei `encrypted`-Flag wird der Body vorher mit einem aus dem Shared Secret (X25519) abgeleiteten AEAD-Key (ChaCha20-Poly1305) verschlüsselt.

## 4.5 Wire-Format Empfehlung

- **CBOR** als Standard-Serialisierung (kompakt, binärfreundlich).
- Fallback JSON für Debugging und Gateway-Layer.
- Maximale Nachrichtengröße: 64 KiB (Yggdrasil-freundlich), größere Payloads über Fragmentierung oder Stream-Protokoll.

---
*Kapitel 4 – Nachrichtenformate – bereit für Implementierung.*
