#!/usr/bin/env bash
# Lance le proto Godot depuis WSL, avec le binaire WINDOWS.
#
# Pourquoi le binaire Windows et pas celui de Linux : sous WSL, le rendu passe
# par une couche de traduction, et c'est exactement ce qui a fait dérailler la
# session de juillet — l'eau apparaissait sur mes captures et pas sur ton écran.
# En appelant le Godot de Windows, le rendu passe par TON pilote NVIDIA : ce
# que je vois est ce que tu vois.
#
#   ./lancer.sh           ouvre la fenêtre, à toi de jouer
#   ./lancer.sh --auto    prend les captures de comparaison et quitte
#   ./lancer.sh --editeur ouvre l'éditeur Godot sur le projet

set -euo pipefail
GODOT="/mnt/c/Godot/Godot_v4.7.2-stable_win64_console.exe"
PROJET="$(wslpath -w "$(cd "$(dirname "$0")" && pwd)")"

[ -x "$GODOT" ] || { echo "Godot introuvable : $GODOT"; exit 1; }

case "${1:-}" in
  --editeur) exec "$GODOT" --path "$PROJET" --editor ;;
  --auto)    exec "$GODOT" --path "$PROJET" --resolution 1600x900 -- --auto ;;
  *)         exec "$GODOT" --path "$PROJET" --resolution 1600x900 ;;
esac
