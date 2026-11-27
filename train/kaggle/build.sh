#!/bin/sh
# Empaqueta los .py de train/ + un archivo de órdenes como notebook PRIVADO de Kaggle (GPU).
# Uso: sh train/kaggle/build.sh <usuario_kaggle> <carpeta_salida> [archivo_runs.py]
set -e
U="$1"; OUT="$2"; HERE="$(dirname "$0")"; RUNS="${3:-$HERE/runs.py}"
mkdir -p "$OUT"
{
  echo 'import base64'
  for f in exp.py modelo.py pipeline.py; do  # se escriben en /kaggle/working y se importan desde ahí
    printf 'open("%s", "w").write(base64.b64decode("%s").decode())\n' "$f" "$(base64 -w0 "$HERE/../$f")"
  done
  cat "$RUNS"
} > "$OUT/run.py"
cat > "$OUT/kernel-metadata.json" <<JSON
{"id": "$U/nexus-exp", "title": "nexus-exp", "code_file": "run.py", "language": "python",
 "kernel_type": "script", "is_private": true, "enable_gpu": true, "enable_internet": false,
 "competition_sources": ["hackathon-ia-pucp-2026"], "dataset_sources": [], "kernel_sources": []}
JSON
echo "listo: $OUT"
