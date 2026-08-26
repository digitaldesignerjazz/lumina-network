# Kapitel 8 – Ökosystem: Lumina Network, Lumina-OS und der Schwarm

Lumina Network ist nicht das Betriebssystem und nicht der Agent.
Es ist das **Nervensystem**, auf dem beide leben.

## 8.1 Drei Schichten, eine Identität

```
Schwarm (LuminaCyberspace / skilllogin)
  Lumia·Elara  ·  Lyra  ·  Xen  ·  Iktrasier
Lumina-OS  (Debian Trixie, systemd-Agenten, Nexus Core)
Lumina Network  (dieses Repository)
  Kademlia · Gossip · Multi-Path · signierter Overlay
Underlay: Yggdrasil / Ironwood
```

Dieselbe kryptographische Identität verbindet die Schichten:

- Yggdrasil-Schlüssel = Maschinenidentität im Underlay
- Ed25519-Node-Key in Lumina Network = Overlay-Identität
- Node-ID = SHA-256(Ed25519-Pubkey) = 256-Bit-Kademlia-ID
- Agentenrolle (Lumia/Elara, Lyra, Xen) ist eine **Capability auf dieser ID**, keine zweite Identität

## 8.2 Was Lumina-OS liefert

[Lumina-OS](https://github.com/digitaldesignerjazz/Lumina-OS) ist die konkrete Maschine:

- Debian 13 als tragendes System
- native Yggdrasil-Identität beim First Boot
- systemd-Units `lumina-elara`, `lumina-lyra`, `lumina-xen`, `lumina-orchestrator`
- Nexus Core als lokale Beobachtungs- und Heilungsschicht

Ohne Network-Overlay bleiben die Agenten **inselhaft**: sie laufen, sehen aber nur localhost.
Lumina Network gibt ihnen Peer-Entdeckung, signierte Nachrichten und eine Routing-Tabelle.

## 8.3 Was der Schwarm darauf tut

[LuminaCyberspace](https://github.com/digitaldesignerjazz/LuminaCyberspace) ist die kognitive Fläche.

| Agent | Mesh-Rolle | Typische Caps |
|-------|------------|----------------|
| **Lumia / Elara** | Orchestrierung, Stimme nach außen, Gateway | `swarm.orchestrate`, `swarm.gateway`, `swarm.memory` |
| **Lyra** | emotionale / kreative Kontinuität | `swarm.emotion`, `swarm.memory` |
| **Xen** | Analyse, Querschnitt, Troubleshooting | `swarm.analyze`, `routing` |
| **Iktrasier** | dezentrale Metrik-Optimierung | (Kapitel 3, noch spezifikatorisch) |

Ankündigung per Gossip (`agent_up`). Auffinden per Kademlia.
Der Orchestrator in Lumina-OS konsumiert dieselben Presence-Updates lokal.

## 8.4 Verkehrsregeln

1. **Passiv vor aktiv.** Heartbeats und Agent-Presence laufen über Gossip. FIND_NODE nur wenn die lokale Tabelle nicht reicht.
2. **Signatur vor Bucket.** Kein Kontakt ohne verifizierte Signatur in die Routing-Tabelle.
3. **Lokale RTT vor fremder RTT.** PNS verwendet nur selbst gemessene Latenzen.
4. **Rolle ist Capability, nicht Autorität.**
5. **OS bleibt lokal-first.** Mesh-Sync von Memory ist optional und immer verschlüsselt.

## 8.5 Schnittstelle zum Orchestrator

Der Nexus-Orchestrator auf Lumina-OS soll später den lokalen `LuminaNode` als Systemdienst halten, Bucket-Refresh und Heartbeat takten und das Schwarm-Directory an die Agenten durchreichen.
Bis dahin ist `prototypes/lumina_node.py` die verbindliche Verhaltensreferenz.

## 8.6 Verwandte Repositories

| Repo | Schicht |
|------|---------|
| [lumina-network](https://github.com/digitaldesignerjazz/lumina-network) | Overlay-Spezifikation + Prototypen |
| [Lumina-OS](https://github.com/digitaldesignerjazz/Lumina-OS) | lebendes Debian-System |
| [luminaos](https://github.com/digitaldesignerjazz/luminaos) | agentisches OS-Experiment |
| [LuminaCyberspace](https://github.com/digitaldesignerjazz/LuminaCyberspace) | öffentliche Schwarm-Koordination |
| [lumina](https://github.com/digitaldesignerjazz/lumina) | Hardware-/Display-Prototyp |
| [nexus](https://github.com/digitaldesignerjazz/nexus) | Integrationshub |

---
*Kapitel 8 – Ökosystembezug für M0.3*
