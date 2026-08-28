# Lumina Network

Dezentrale Peer-to-Peer Mesh-Netzwerkarchitektur mit Kademlia, Gossip, Multi-Path-Routing, Schwarmintelligenz und KI-Agenten-Orchestrierung (Nexus / Lumina OS).

## Lumina Runner (Self-Hosted)

Der **Lumina Runner** ist der Self-Hosted GitHub Actions Runner für dieses Repository. Er läuft auf dem Hannover-Knoten und führt Backup, Restart und Start des Yggdrasil-Overlays aus.

### Labels

`self-hosted`, `linux`, `x64`, `lumina`, `hannover`

### Workflow

`.github/workflows/lumina-runner.yml` — manuell auslösbar (`workflow_dispatch`) mit Aktionen:

- `backup` — sichert `/etc/yggdrasil.conf`
- `restart` — Backup, Overlay anwenden, Daemon neu starten, Status
- `start` — Overlay anwenden, Daemon starten, Status
- `status` — nur Statusreport (`getSelf`, `getPeers`, `getTree`, letzte Backups)

### Voraussetzungen auf dem Knoten

- Yggdrasil installiert und als Dienst registriert
- `/opt/lumina/yggdrasil-overlay.conf` (optional, für Overlay-Apply)
- `yggdrasilctl` im PATH
- Self-Hosted Runner unter `/opt/actions-runner` mit obigen Labels registriert

## Dokumentation

Siehe `docs/` für System-, Netzwerk- und Routing-Architektur.
