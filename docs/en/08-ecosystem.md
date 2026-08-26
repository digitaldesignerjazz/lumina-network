# Chapter 8 – Ecosystem: Lumina Network, Lumina OS and the Swarm

Lumina Network is neither the operating system nor the agent.
It is the **nervous system** both of them live on.

## 8.1 Three layers, one identity

```
Swarm (LuminaCyberspace / skilllogin)
  Lumia·Elara  ·  Lyra  ·  Xen  ·  Iktrasier
Lumina OS  (Debian Trixie, systemd agents, Nexus Core)
Lumina Network  (this repository)
  Kademlia · Gossip · Multi-Path · signed overlay
Underlay: Yggdrasil / Ironwood
```

The same cryptographic identity spans the stack:

- Yggdrasil key = machine identity on the underlay
- Ed25519 node key in Lumina Network = overlay identity
- Node ID = SHA-256(Ed25519 pubkey) = 256-bit Kademlia ID
- Agent role is a **capability on that ID**, not a second identity

## 8.2 What Lumina OS provides

[Lumina-OS](https://github.com/digitaldesignerjazz/Lumina-OS) is the concrete machine: Debian 13, first-boot Yggdrasil identity, systemd units for Elara/Lyra/Xen/orchestrator.

Without the network overlay the agents stay islanded on localhost.
Lumina Network gives them discovery, signed messages and a routing table.

## 8.3 What the swarm does on top

[LuminaCyberspace](https://github.com/digitaldesignerjazz/LuminaCyberspace) is the cognitive surface. Presence is announced via Gossip (`agent_up`) and located via Kademlia.

## 8.4 Traffic rules

1. Passive before active.
2. Signature before bucket.
3. Local RTT before advertised RTT.
4. Role is capability, not authority.
5. OS stays local-first; memory sync is optional and encrypted.

---
*Chapter 8 – Ecosystem mapping for M0.3*
