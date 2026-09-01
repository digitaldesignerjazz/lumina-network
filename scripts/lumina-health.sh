#!/usr/bin/env bash
# lumina-health.sh — prüft Yggdrasil-Daemon, Peers, letzte Backups.
# Aufruf: ./scripts/lumina-health.sh   oder aus dem Workflow heraus.
set -euo pipefail

BACKUP_DIR="/opt/lumina/backups"
LOG="/opt/lumina/logs/health.log"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

main() {
  log "=== Lumina Health Check ==="
  if ! command -v yggdrasilctl >/dev/null 2>&1; then
    log "FEHLER: yggdrasilctl nicht gefunden."
    exit 1
  fi
  if [ ! -c /dev/net/tun ]; then
    log "WARNUNG: /dev/net/tun fehlt — kein TUN-Gerät."
  fi
  log "Self:"
  yggdrasilctl getSelf || log "getSelf fehlgeschlagen"
  log "Peers:"
  yggdrasilctl getPeers || log "getPeers fehlgeschlagen"
  log "Tree:"
  yggdrasilctl getTree || log "getTree fehlgeschlagen"
  if [ -d "$BACKUP_DIR" ]; then
    log "Letzte Backups:"
    ls -lt "$BACKUP_DIR" | head -6 | tee -a "$LOG"
  fi
  log "=== Ende ==="
}

main "$@"
