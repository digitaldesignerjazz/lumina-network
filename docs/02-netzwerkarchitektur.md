# Kapitel 2 – Netzwerkarchitektur

## Grundprinzipien

- Dezentrale Peer-to-Peer-Knoten
- Automatische Peer Discovery über Kademlia
- Selbstheilung bei Ausfall von Knoten
- Standardisierte Nachrichtenformate mit Header und digitaler Signatur

## Nachrichtentypen

| Typ | Zweck |
|-----|-------|
| `HELLO` | Initiale Kontaktaufnahme |
| `HEARTBEAT` | Lebendigkeitsprüfung |
| `GOSSIP` | Status- und Topologie-Updates |
| `DATA` | Nutzdaten |
| `ACK` | Bestätigung |

## Schichten über dem Netzwerk

- **Agentenschicht** mit Schwarmintelligenz
- **Gemeinschaftliches Gedächtnis** (shared memory)
- **Evaluations- und Status-Streaming**
- **Gateway-Layer** für externe Systeme

## Qualitätsziele

- Hohe Verfügbarkeit
- Geringe Latenz
- Energieeffizienz
- Skalierbarkeit
- Starke Kryptografie

---
*Grundlage der Netzwerkarchitektur beschrieben.*
