# Kapitel 1 – Systemarchitektur

Die Systemarchitektur von Lumina (Blumina) ist modular aufgebaut und besteht aus mehreren Schichten:

```
Anwendungen
    ↓
APIs und Dienste
    ↓
Routing (Kademlia + Gossip)
    ↓
Transport (Funk- / Netzwerkmedien)
```

## Kernmodule

Im Kern arbeiten mehrere Module zusammen:

| Modul | Aufgabe |
|-------|---------|
| **Node Manager** | Identität und Schlüsselverwaltung |
| **Discovery Engine** | Peer-Suche (Kademlia) |
| **Gossip Engine** | Verteilung von Status und Topologie-Updates |
| **Routing Engine** | Mehrfachpfade (Multi-Path) |
| **Security Engine** | Authentifizierung und Verschlüsselung |

## Höhere Schichten

- **KI-Agenten mit Orchestrierung** – koordinieren Aufgaben dezentral
- **Memory-, Evaluation- und Status-Streaming** – halten Wissen, Qualität und Netzwerkzustand kontinuierlich verfügbar
- **Gateway-Layer** – ermöglicht die Anbindung externer Systeme
- **Iktrasier** – Schwarmintelligenz-Schicht für dezentrale Optimierungen

---
*Grundlage der gesamten Lumina Network Architektur.*
