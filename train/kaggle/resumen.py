"""Lee el log del notebook de Kaggle, imprime lo importante y agrega los RESULTADO a resultados.log."""
import glob, json, sys, datetime
out, registro = sys.argv[1], sys.argv[2]
logs = glob.glob(f'{out}/*.log')
if not logs: sys.exit('No se bajó ningún log de Kaggle')
lineas = [e['data'].rstrip() for e in json.load(open(logs[0]))]
claves = ('CUDA', 'GPU 0', 'semilla', 'RESULTADO', 'Error', 'Traceback', 'SUBMISSION')
for l in lineas:
    if any(k in l for k in claves): print(l)
res = [l for l in lineas if 'RESULTADO' in l]
with open(registro, 'a', encoding='utf-8') as f:
    for l in res: f.write(f'{datetime.datetime.now():%Y-%m-%d %H:%M} UTC {l}\n')
print(f'-> {len(res)} resultados agregados a resultados.log · archivos en {out}')
