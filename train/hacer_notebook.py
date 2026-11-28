"""Genera train/submission_notebook.ipynb a partir de modelo.py y models/config.json.
Si cambia el modelo (nuevo ensamble o nuevo modelo.py), volver a correr esto y luego ejecutar el notebook.
Uso (desde la raíz): docker run --rm -v "$PWD:/w" -w /w nexus-train python train/hacer_notebook.py"""
import json, nbformat as nbf

cfg = json.load(open('models/config.json'))
modelo = open('train/modelo.py', encoding='utf-8').read()
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

cells = [
    md("""# TEAM NEXUS · Submission (Hackathon IA PUCP 2026)
Downscaling GFS (~27 km, 17×13) → WRF (3 km, 70×35) de RH, T, U, V en la Cordillera Blanca.

**Qué hace este notebook (de punta a punta, solo con la data oficial):**
1. Escribe `modelo.py` (la misma red que usa el producto en `app/`).
2. Entrena el ensamble final con **todo** `train.npz` (cada configuración, 5 semillas, hasta su mejor época
   elegida con validación temporal 16–30 jun).
3. Predice el test y escribe `submission.csv`; guarda los pesos y `stats.npz` en `models/` (los que carga la app).

**Cómo correrlo:** en Kaggle (GPU T4, agregar la competencia `hackathon-ia-pucp-2026` como input) o en local
con la data en `data/` (rutas relativas). Con `VALIDAR = True` además reentrena con corte temporal y muestra el
score en validación (duplica el tiempo).

**Idea del modelo:** CNN sobre 3 horas del GFS (t−2, t−1, t) + hora del día → interpolación a la grilla de 3 km →
se suman relieve (DEM) y un mapa aprendido → la red predice la corrección sobre una **base física**:
climatología WRF por hora + anomalía del GFS interpolada (*ancla GFS*), para que el cambio de época pase directo."""),
    md('## 1. Configuración'),
    code(f"""SEEDS = {cfg['seeds']}
CONFIGS = {json.dumps(cfg['configs'])}  # w = ancho, enc = bloques del codificador, wd = weight decay, anchor, rep = junio ×rep
EPOCHS = {json.dumps(cfg['epochs'])}  # mejor época de cada config en validación temporal (pipeline.py)
LR, BS, EPOCHS_PLAN = 2e-3, 32, 25  # OneCycle planificado a 25 épocas y cortado en EPOCHS[c] (igual que pipeline.py)
VALIDAR = False  # True: entrena también con corte temporal y reporta el score en val (val de referencia: {cfg['val_score']})
OUT = '.'"""),
    md('## 2. Modelo (mismo archivo que usa el producto)'),
    code('%%writefile modelo.py\n' + modelo),
    md('## 3. Data'),
    code("""import glob, json, os, time
import numpy as np, pandas as pd, torch, torch.nn.functional as F
from modelo import VARS, hour, windows, make_stats, Net, predict, base, anom_sd

dev = 'cuda' if torch.cuda.is_available() else 'cpu'
print('dispositivo:', dev, '· torch', torch.__version__)

def find(name):
    hits = glob.glob(f'/kaggle/input/**/{name}', recursive=True) + glob.glob(f'../data/{name}') + glob.glob(f'data/{name}')
    assert hits, f'No encuentro {name}: poner la data oficial en data/ o como input de Kaggle'
    return hits[0]

tr, te, st = np.load(find('train.npz')), np.load(find('test.npz')), dict(np.load(find('static.npz')))
Xtr, Ytr, ttr = tr['X'], tr['Y'], tr['times'].astype(str)
Xte, tte = te['X'], te['times'].astype(str)
Wtr, Wte = windows(Xtr, ttr), windows(Xte, tte)  # (N,3,17,13,4): horas t-2, t-1, t
print('train', Xtr.shape, Ytr.shape, ttr[0], '→', ttr[-1], '· test', Xte.shape, tte[0], '→', tte[-1])"""),
    md('## 4. Entrenamiento'),
    code("""def train_one(cfg, seed, idx, stats, epochs):
    torch.manual_seed(seed); np.random.seed(seed)
    anc = cfg.get('anchor', 'clim'); m = Net(stats, cfg['w'], cfg['enc'], anc, cfg.get('dec', 1)).to(dev)
    idx = np.concatenate([idx] + [idx[ttr[idx] >= '2024060100']] * (cfg.get('rep', 1) - 1))  # junio repetido
    opt = torch.optim.AdamW(m.parameters(), lr=LR, weight_decay=cfg['wd'])
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=LR, total_steps=EPOCHS_PLAN * int(np.ceil(len(idx) / BS)))
    tt = lambda v: torch.tensor(v, dtype=torch.float32, device=dev)
    Btr, ASD = base(stats, Xtr, ttr, anc), tt(anom_sd(stats, anc))
    for ep in range(epochs):
        m.train(); np.random.shuffle(idx)
        for s in range(0, len(idx), BS):
            b = idx[s:s + BS]
            x = tt((Wtr[b] - stats['mu_x']) / stats['sd_x']); h = torch.tensor(hour(ttr[b]), device=dev).float()
            loss = F.mse_loss(m(x, h), tt(Ytr[b] - Btr[b]) / ASD)
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
    return m.eval()"""),
    md('## 5. (Opcional) Validación temporal: entrena hasta el 15 jun y evalúa 16–30 jun'),
    code("""if VALIDAR:
    val = ttr >= '2024061600'; trn = np.where(~val)[0]
    st_trn = make_stats(Xtr[~val], Ytr[~val], ttr[~val], st)
    grupos_v = [[train_one(CONFIGS[c], s, trn, st_trn, EPOCHS[c]) for s in SEEDS] for c in CONFIGS]
    P = predict(grupos_v, st_trn, Wtr[val], ttr[val])
    clim_rmse = np.sqrt(((st_trn['clim'][hour(ttr[val])] - Ytr[val]) ** 2).mean((0, 1, 2)))
    rmse = np.sqrt(((P - Ytr[val]) ** 2).mean((0, 1, 2)))
    print('RMSE', dict(zip(VARS, rmse.round(3))), '· score val', round(float(1 - (rmse / clim_rmse).mean()), 4))"""),
    md('## 6. Entrenamiento final con todo train + pesos para el producto'),
    code("""os.makedirs(f'{OUT}/models', exist_ok=True)
st_all = make_stats(Xtr, Ytr, ttr, st)
np.savez(f'{OUT}/models/stats.npz', **st_all)  # mu_x, sd_x, climatologías, DEM y coordenadas: la app los necesita
grupos, t0 = [], time.time()
for c in CONFIGS:
    g = []
    for s in SEEDS:
        m = train_one(CONFIGS[c], s, np.arange(len(Xtr)), st_all, EPOCHS[c])
        torch.save(m.state_dict(), f'{OUT}/models/{c}_s{s}.pt'); g.append(m)
    grupos.append(g); print(f'{c}: {len(g)} semillas · {time.time() - t0:.0f} s', flush=True)
json.dump(dict(configs=CONFIGS, seeds=SEEDS, epochs=EPOCHS), open(f'{OUT}/models/config.json', 'w'), indent=1)"""),
    md('## 7. Submission'),
    code("""P = predict(grupos, st_all, Wte, tte)  # (N_test,70,35,4) en unidades físicas, fila 0 = sur
sample = pd.read_csv(find('sample_submission.csv'))
parts = sample['id'].str.split('_', expand=True)  # id = YYYYMMDDHH_fila_columna
ti = parts[0].map({k: i for i, k in enumerate(tte)}).values
assert not pd.isna(ti).any(), 'hay horas del sample que no están en el test'
r, c = parts[1].astype(int).values, parts[2].astype(int).values
sub = pd.DataFrame({'id': sample['id']})
for k, v in enumerate(VARS): sub[v] = P[ti.astype(int), r, c, k].round(3)
assert len(sub) == len(sample) and not sub[VARS].isna().any().any()
assert 200 < sub['T'].min() and sub['T'].max() < 320, 'T debe estar en K'
assert sub['RH'].between(0, 100).all()
sub.to_csv(f'{OUT}/submission.csv', index=False)
print(sub.shape); sub.describe().round(2)"""),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={'kernelspec': {'name': 'python3', 'display_name': 'Python 3', 'language': 'python'}})
nbf.write(nb, 'train/submission_notebook.ipynb')
print('listo: train/submission_notebook.ipynb', list(cfg['configs']))
