#!/usr/bin/env bash
set -euo pipefail

# args
if (( $# < 2 )); then
  echo "usage: $0 <local-ip> <vm2-ip> [vm3-ip ...] [--yaml <file>]"
  exit 1
fi

LOCAL_IP="$1"; shift
REMOTES=()
YAML="4vm-testnet.yaml"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --yaml)
      shift
      [[ $# -gt 0 ]] || { echo "Error: --yaml requires a filename."; exit 1; }
      YAML="$1"; shift
      ;;
    *)
      REMOTES+=("$1"); shift
      ;;
  esac
done

# Do I need this for ~?
YAML="${YAML/#\~/$HOME}"

# Require at least one remote
(( ${#REMOTES[@]} >= 1 )) || { echo "need at least one remote IP"; exit 1; }

POOL_COUNT=$(( ${#REMOTES[@]} + 1 ))

# config
OUT="/tmp/testnet_files"
LOCAL_BASE="/tmp/testnet"
LOCAL_POOL_DEST="$LOCAL_BASE/pool"
REMOTE_BASE="/tmp/testnet"
REMOTE_POOL_DEST="$REMOTE_BASE/pool"
UTXO_SUB="utxos/keys"
UTXO_SRC="$OUT/$UTXO_SUB"
SSH_USER="ubuntu"
TOOL_DIR="/home/ubuntu/src/testnet-generation-tool"

echo "check outputs..."
if [[ ! -d "$OUT" || ! -f "$OUT/pools/1/configs/config.json" ]]; then
  echo "outputs missing; trying to generate..."
  if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found. install uv: https://github.com/astral-sh/uv"
    exit 1
  fi
  if [[ ! -d "$TOOL_DIR" ]]; then
    echo "tool repo missing. clone https://github.com/cardano-foundation/testnet-generation-tool.git to $TOOL_DIR"
    exit 1
  fi
  cd "$TOOL_DIR"
  echo "generate files..."
  uv run python3 genesis-cli.py "$YAML" -o "$OUT" -c generate
fi

echo "stop nodes..."
pkill -x cardano-node || true

echo "rewrite log paths..."
sed -i "s#${OUT}/#${LOCAL_BASE}/#g" "$OUT"/pools/*/configs/config.json

echo "local pool..."
mkdir -p "$LOCAL_POOL_DEST"
rm -rf "$LOCAL_POOL_DEST"/*
cp -a "$OUT/pools/1/." "$LOCAL_POOL_DEST/"

idx=2
for ip in "${REMOTES[@]}"; do
  host="${SSH_USER}@${ip}"
  echo "sync pool $idx -> $host..."
  ssh "$host" "mkdir -p '$REMOTE_POOL_DEST' && rm -rf '$REMOTE_POOL_DEST'/*"
  rsync -a --delete "$OUT/pools/$idx/" "$host:$REMOTE_POOL_DEST/"
  idx=$((idx+1))
done

echo "copy delegated.*.addr.info to all..."
install -d "$LOCAL_BASE/$UTXO_SUB"
DELEGATED=( "$UTXO_SRC"/delegated.*.addr.info )
if (( ${#DELEGATED[@]} )); then
  cp -f "${DELEGATED[@]}" "$LOCAL_BASE/$UTXO_SUB/"
  for ip in "${REMOTES[@]}"; do
    host="${SSH_USER}@${ip}"
    ssh "$host" "mkdir -p '$REMOTE_BASE/$UTXO_SUB'"
    rsync -a "${DELEGATED[@]}" "$host:$REMOTE_BASE/$UTXO_SUB/"
  done
fi

echo "copy all *\.1\.* (payment.1.*, stake.1.*, genesis.1.*, etc.) to LOCAL..."
ONE_FILES=( "$UTXO_SRC"/*\.1\.* )
if (( ${#ONE_FILES[@]} )); then
  cp -f "${ONE_FILES[@]}" "$LOCAL_BASE/$UTXO_SUB/"
fi

echo "copy per-node *.addr.info to respective VMs..."
for i in $(seq 1 "$POOL_COUNT"); do
  if [[ $i -eq 1 ]]; then
    install -d "$LOCAL_BASE/$UTXO_SUB"
    for f in "$UTXO_SRC/genesis.$i.addr.info" "$UTXO_SRC/stake.$i.addr.info"; do
      [[ -e "$f" ]] && cp -f "$f" "$LOCAL_BASE/$UTXO_SUB/"
    done
  else
    ip="${REMOTES[$((i-2))]}"
    host="${SSH_USER}@${ip}"
    for f in "$UTXO_SRC/genesis.$i.addr.info" "$UTXO_SRC/stake.$i.addr.info"; do
      [[ -e "$f" ]] && rsync -a "$f" "$host:$REMOTE_BASE/$UTXO_SUB/"
    done
  fi
done

echo "done."
