#!/usr/bin/env bash
# lumina-health.sh — Health-Check für den Hannover-Knoten.
# Läuft lokal per Cron oder im Workflow. Keine Secrets, keine Keys.
set -euo pipefail

LOG="/opt/lumina/logs/health.log"
TS=$(date -u +%Y-%m-%dT%H:%M:%SZ)

{
  echo "=== $TS ==="
  echo "-- Daemon --"
  systemctl is-active yggdrasil 2>/dev/null || echo "inactive"
  echo "-- Self --"
  yggdrasilctl getSelf 2>/dev/null || echo "yggdrasilctl fehlt"
  echo "-- Peers --"
  yggdrasilctl getPeers 2>/dev/null || true
  echo "-- Tree --"
  yggdrasilctl getTree 2>/dev/null || true
  echo "-- Backups --"
  ls -lt /opt/lumina/backups 2>/dev/null | head -5 || echo "kein Backup-Ordner"
  echo "-- Disk --"
  df -h /opt/lumina 2>/dev/null || true
} | tee -a "$LOG"
