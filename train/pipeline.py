"""Pipeline todo en uno de TEAM NEXUS: corre solo, sin decisiones manuales.
 1. Selección: entrena cada configuración (varias semillas) con corte temporal (val = 16–30 jun).
 2. Ensamble: elige de forma greedy qué configuraciones promediar según el score de validación.
 3. Final: reentrena las elegidas con TODO train (hasta su mejor época) y predice el test.
 4. Salidas en OUT (por defecto la carpeta actual): submission.csv, models/*.pt, models/stats.npz, models/config.json.
Con ALL_FINAL=1 (modo librería) cada config, apenas termina, guarda val_<config>.npy, sus pesos finales y
submission_<config>.csv: así se puede armar cualquier ensamble después sin volver a entrenar (data/libreria.py).
Uso: python pipeline.py     ·     prueba rápida: QUICK=1 python pipeline.py"""
import glob, json, os, time
import numpy as np, pandas as pd, torch, torch.nn.functional as F
from modelo import VARS, hour, windows, make_stats, Net, predict, base, anom_sd

QUICK = os.environ.get('QUICK') == '1'
T0 = time.time(); LIMITE_H = float(os.environ.get('LIMITE_H', '10.5'))  # Kaggle corta a las 12 h: no empezar configs después
CONFIGS = {  # w = ancho, enc = bloques del codificador GFS, wd = weight decay; opcionales: anchor, rep, lr, ep, bs, dec
    # Tanda 1 (26 nov, val): A starter w64 0.355 · B w96/enc2 0.357 · C w64/wd1e-2 0.355 · D w64/enc2 0.350
    # -> descartadas. Quedan las dos mejores y se prueban más anchas (más ancho ayudó).
    # Tanda 2 (26 nov, 5 semillas): E 0.359 · F 0.364 · G 0.362 · H w192 0.360 (descartada) · I 0.365
    # -> ensamble I+F+G+E = 0.372. Tanda 3: las mismas con 10 semillas.
    # Tanda 3 (10 semillas): ensamble 0.3725 = ruido. Tanda 4 (exp.py): ningún cambio de arquitectura ayuda.
    # Tanda 5a (falló en Ir por un bug ya corregido): I 0.3648 · Ig 0.3781 · Fg 0.3791 -> el ancla GFS da +0.013.
    # Tanda 5b (val): I 0.3648 · Ig 0.3781 · Fg 0.3792 · Gg 0.3846 · Eg 0.3741 · Igr 0.3791
    # -> ensamble Gg+Igr+I+Fg = 0.3900. Con ancla, más ancho SÍ ayuda (Gg > Fg).
    # Tanda 6 (val): Gg 0.3865 · Hg 0.3841 · Jg 0.3823 · Ggr 0.3804 · Igr 0.3791 · Fg 0.3792 · I 0.3648
    # -> v4 = Gg+Igr+Hg+I+Ggr: val 0.3930, LB 0.49916. Local: ancla 'mix' (GFS solo en RH/T) Gm 0.3819 < Gg -> descartada.
    # Tanda 7: v4 con semillas 5-9 -> ensamble 0.3901: el ruido entre semillas es ~0.003.
    # Tanda 8 (librería, ~8 h): hiperparámetros nunca probados con ancla GFS + las 5 de v4 (al final).
    'Gg_lr1': dict(w=160, enc=2, wd=1e-3, anchor='gfs', lr=1e-3),
    'Gg_lr4': dict(w=160, enc=2, wd=1e-3, anchor='gfs', lr=4e-3),
    'Gg_wd2': dict(w=160, enc=2, wd=1e-2, anchor='gfs'),
    'Gg_ep40': dict(w=160, enc=2, wd=1e-3, anchor='gfs', ep=40),
    'Gg_bs16': dict(w=160, enc=2, wd=1e-3, anchor='gfs', bs=16),
    'Gg_e3': dict(w=160, enc=3, wd=1e-3, anchor='gfs'),
    'Gg_d2': dict(w=160, enc=2, wd=1e-3, anchor='gfs', dec=2),
    'Hg_e3': dict(w=192, enc=3, wd=1e-3, anchor='gfs'),
    'Hgr': dict(w=192, enc=2, wd=1e-3, anchor='gfs', rep=3),
    'Kg': dict(w=256, enc=1, wd=1e-3, anchor='gfs'),             # ancho y poco profundo
    'Gc': dict(w=160, enc=2, wd=1e-3),                            # Gg sin ancla: diversidad para el ensamble
    'Ig': dict(w=128, enc=1, wd=1e-4, anchor='gfs'),
    'Hg_lr1': dict(w=192, enc=2, wd=1e-3, anchor='gfs', lr=1e-3),
    'Hg_d2': dict(w=192, enc=2, wd=1e-3, anchor='gfs', dec=2),
    # las 5 de v4 (mismas semillas): su val por config permite el greedy con todas las nuevas
    'Gg':  dict(w=160, enc=2, wd=1e-3, anchor='gfs'),
    'Hg':  dict(w=192, enc=2, wd=1e-3, anchor='gfs'),
    'Igr': dict(w=128, enc=1, wd=1e-4, anchor='gfs', rep=3),    # + junio repetido x3 (lo más parecido a julio)
    'Ggr': dict(w=160, enc=2, wd=1e-3, anchor='gfs', rep=3),
    'I':   dict(w=128, enc=1, wd=1e-4),                         # sin ancla: aporta diversidad al ensamble
}
ALL_FINAL = os.environ.get('ALL_FINAL', '0') == '1'
SEEDS = [int(s) for s in os.environ.get('SEEDS', '0,1,2,3,4').split(',')]; EPOCHS = 25; LR = 2e-3; BS = 32
if os.environ.get('SOLO'): CONFIGS = {k: CONFIGS[k] for k in os.environ['SOLO'].split(',')}  # p. ej. SOLO=Gg,Hg
if QUICK: CONFIGS = {k: CONFIGS[k] for k in ('Gg_d2', 'Gg_ep40')}; SEEDS = [0]; EPOCHS = 2
OUT = os.environ.get('OUT', '.'); os.makedirs(f'{OUT}/models', exist_ok=True)
dev = 'cuda' if torch.cuda.is_available() else 'cpu'
print('CUDA disponible:', torch.cuda.is_available(), flush=True)


def find(name):
    hits = glob.glob(f'/kaggle/input/**/{name}', recursive=True) + glob.glob(f'../data/{name}') + glob.glob(f'data/{name}')
    assert hits, f'No encuentro {name}'
    return hits[0]


tr, te, st = np.load(find('train.npz')), np.load(find('test.npz')), dict(np.load(find('static.npz')))
Xtr, Ytr, ttr = tr['X'], tr['Y'], tr['times'].astype(str)
Xte, tte = te['X'], te['times'].astype(str)
Wtr, Wte = windows(Xtr, ttr), windows(Xte, tte)
val = ttr >= '2024061600'; trn = ~val


BASES = {}


def train_one(cfg, seed, idx, stats, val_idx=None, stop_at=None):
    """Entrena con calendario OneCycle. Con val_idx guarda la mejor época; con stop_at corta ahí."""
    torch.manual_seed(seed); np.random.seed(seed)
    epochs = EPOCHS if QUICK else cfg.get('ep', EPOCHS); lr, bs = cfg.get('lr', LR), cfg.get('bs', BS)
    anc = cfg.get('anchor', 'clim'); m = Net(stats, cfg['w'], cfg['enc'], anc, cfg.get('dec', 1)).to(dev)
    idx = np.concatenate([idx] + [idx[ttr[idx] >= '2024060100']] * (cfg.get('rep', 1) - 1)); best = (-9e9, None, 0)
    opt = torch.optim.AdamW(m.parameters(), lr=lr, weight_decay=cfg['wd'])
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=lr, total_steps=epochs * int(np.ceil(len(idx) / bs)))
    tt = lambda v: torch.tensor(v, dtype=torch.float32, device=dev)
    key = (id(stats), anc)
    if key not in BASES: BASES[key] = base(stats, Xtr, ttr, anc)  # base física de cada hora de train
    Btr, ASD = BASES[key], tt(anom_sd(stats, anc))
    for ep in range(epochs):
        m.train(); np.random.shuffle(idx)
        for s in range(0, len(idx), bs):
            b = idx[s:s + bs]
            x = tt((Wtr[b] - stats['mu_x']) / stats['sd_x']); h = torch.tensor(hour(ttr[b]), device=dev)
            loss = F.mse_loss(m(x, h.float()), tt(Ytr[b] - Btr[b]) / ASD)
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        if val_idx is not None:
            pv = predict([[m]], stats, Wtr[val_idx], ttr[val_idx]); sc = score(pv)
            if sc > best[0]: best = (sc, pv, ep + 1)
        if stop_at == ep + 1: break
    return m, best


# ---------- preparación: métrica, formato del submission y stats con todo train ----------
st_trn = make_stats(Xtr[trn], Ytr[trn], ttr[trn], st)
clim_rmse = np.sqrt(((st_trn['clim'][hour(ttr[val])] - Ytr[val]) ** 2).mean((0, 1, 2)))
rmse = lambda P: np.sqrt(((P - Ytr[val]) ** 2).mean((0, 1, 2)))
score = lambda P: float(1 - (rmse(P) / clim_rmse).mean())
vidx, tidx = np.where(val)[0], np.where(trn)[0]

sample = pd.read_csv(find('sample_submission.csv'))
parts = sample['id'].str.split('_', expand=True)
ti = parts[0].map({k: i for i, k in enumerate(tte)}).values
r, c = parts[1].astype(int).values, parts[2].astype(int).values
assert not np.isnan(ti.astype(float)).any(), 'hay horas del sample que no están en el test'


def write_sub(P, path):
    sub = pd.DataFrame({'id': sample['id']})
    for k, v in enumerate(VARS): sub[v] = P[ti, r, c, k].round(3)
    assert len(sub) == len(sample) and not sub[VARS].isna().any().any()
    assert 200 < sub['T'].min() and sub['T'].max() < 320, 'T fuera de rango físico (debe estar en K)'
    sub.to_csv(path, index=False); return sub


st_all = make_stats(Xtr, Ytr, ttr, st)
np.savez(f'{OUT}/models/stats.npz', **st_all)
grupos = {}


def final(name):
    """Reentrena una config con todo train hasta su mejor época y guarda sus pesos."""
    grupos[name] = []
    for seed in SEEDS:
        m, _ = train_one(CONFIGS[name], seed, np.arange(len(Xtr)), st_all, stop_at=best_ep[name])
        torch.save(m.state_dict(), f'{OUT}/models/{name}_s{seed}.pt'); grupos[name].append(m)


# ---------- 1. Selección con corte temporal (en modo librería, cada config queda completa al terminar) ----------
val_pred, best_ep = {}, {}
for name, cfg in CONFIGS.items():
    if (time.time() - T0) / 3600 > LIMITE_H:
        print(f'TIEMPO: {LIMITE_H} h alcanzadas, no se empieza {name} ni las siguientes', flush=True); break
    t0 = time.time(); preds, eps = [], []
    for seed in SEEDS:
        _, (sc, pv, ep) = train_one(cfg, seed, tidx, st_trn, val_idx=vidx)
        preds.append(pv); eps.append(ep)
    val_pred[name] = np.mean(preds, 0); best_ep[name] = int(round(np.median(eps)))
    print(f'RESULTADO config {name} {cfg} -> val {score(val_pred[name]):.4f} {rmse(val_pred[name]).round(3)} '
          f'· épocas {eps} · {time.time() - t0:.0f}s', flush=True)
    if ALL_FINAL:
        np.save(f'{OUT}/val_{name}.npy', val_pred[name].astype(np.float32)); final(name)
        write_sub(predict([grupos[name]], st_all, Wte, tte), f'{OUT}/submission_{name}.csv')
        json.dump(dict(configs=CONFIGS, epochs=best_ep, seeds=SEEDS,
                       val={k: round(score(v), 4) for k, v in val_pred.items()}),
                  open(f'{OUT}/libreria.json', 'w'), indent=1)
        print(f'SUBMISSION config {name}: submission_{name}.csv · val {score(val_pred[name]):.4f} '
              f'· {(time.time() - T0) / 3600:.1f} h', flush=True)

# ---------- 2. Ensamble greedy ----------
sel = [max(val_pred, key=lambda k: score(val_pred[k]))]
while True:
    cur = score(np.mean([val_pred[k] for k in sel], 0))
    cand = {k: score(np.mean([val_pred[j] for j in sel + [k]], 0)) for k in val_pred if k not in sel}
    if not cand or max(cand.values()) <= cur + 1e-4: break
    sel.append(max(cand, key=cand.get))
P_sel = np.mean([val_pred[k] for k in sel], 0)
print(f'RESULTADO ensamble elegido {sel} -> val {score(P_sel):.4f} {rmse(P_sel).round(3)}', flush=True)
if os.environ.get('SOLO_VAL') == '1':  # solo validación: guarda la predicción del val (sin fuga) y termina
    P_all = np.mean(list(val_pred.values()), 0); np.save(f'{OUT}/val_pred.npy', P_all)
    print(f'RESULTADO promedio de todas {list(val_pred)} -> val {score(P_all):.4f}', flush=True); raise SystemExit

# ---------- 3. Final con todo train ----------
for name in sel:
    if name not in grupos: final(name)
json.dump(dict(configs={k: CONFIGS[k] for k in sel}, seeds=SEEDS, epochs={k: best_ep[k] for k in sel},
               val_score=round(score(P_sel), 4), quick=QUICK), open(f'{OUT}/models/config.json', 'w'), indent=1)

# ---------- 4. Submission del ensamble elegido ----------
sub = write_sub(predict([grupos[k] for k in sel], st_all, Wte, tte), f'{OUT}/submission.csv')
print(f'SUBMISSION lista: {sub.shape} · ensamble {sel} · épocas {[best_ep[k] for k in sel]} · val {score(P_sel):.4f}', flush=True)
