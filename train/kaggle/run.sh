#!/bin/sh
# Ciclo completo sin intervención: empaqueta -> envía a Kaggle (GPU T4) -> espera -> baja salidas -> resume.
# Uso: sh train/kaggle/run.sh [archivo_runs.py]      (por defecto train/kaggle/runs.py)
# Salidas: train/kaggle/_build/out/ (log y archivos que genere el notebook) y una línea por RESULTADO en resultados.log
set -e
USUARIO=jhonatanacar; KERNEL=nexus-exp
HERE="$(cd "$(dirname "$0")" && pwd)"; B="$HERE/_build"
rm -rf "$B"; sh "$HERE/build.sh" "$USUARIO" "$B/k" "${1:-$HERE/runs.py}" >/dev/null
MSYS_NO_PATHCONV=1 docker run --rm -e K="$USUARIO/$KERNEL" -v "$HOME/.kaggle:/root/.kaggle:ro" -v "$B:/b" -v "$HERE:/h" \
  python:3.12-slim sh -c '
export KAGGLE_API_TOKEN="$(cat /root/.kaggle/access_token)"; pip install -q kaggle==2.2.5 six 2>/dev/null
kaggle kernels push -p /b/k --accelerator NvidiaTeslaT4
visto=0; t0=$(date +%s)
while :; do
  s=$(kaggle kernels status "$K" 2>&1)
  case "$s" in *QUEUED*|*RUNNING*) visto=1;; esac
  # no confundir el estado final de la versión anterior con el de la nueva
  if [ $visto = 1 ] || [ $(( $(date +%s) - t0 )) -gt 300 ]; then
    case "$s" in *COMPLETE*|*ERROR*|*CANCEL*) break;; esac
  fi
  sleep 30
done
echo "$s ($(( ($(date +%s) - t0) / 60 )) min)"
mkdir -p /b/out; kaggle kernels output "$K" -p /b/out >/dev/null 2>&1 || true
python /h/resumen.py /b/out /h/resultados.log'
