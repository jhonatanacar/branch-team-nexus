"""Experimentos rápidos sobre el starter. Uso (dentro de nexus-train, cwd = train/):
    python exp.py --arch unet --epochs 40 --seeds 0 1 2
Imprime el score de validación (16–30 jun) por semilla y del ensamble de semillas."""
import argparse, glob, time
import numpy as np, pandas as pd
import torch, torch.nn as nn, torch.nn.functional as F

p = argparse.ArgumentParser()
p.add_argument('--arch', default='base', choices=['base', 'unet'])
p.add_argument('--epochs', type=int, default=25)
p.add_argument('--width', type=int, default=64)
p.add_argument('--lr', type=float, default=2e-3)
p.add_argument('--terrain', type=int, default=0, help='1 = agrega pendientes del DEM y lat/lon como entradas')
p.add_argument('--enc', type=int, default=1, help='bloques convolucionales en el codificador GFS')
p.add_argument('--wd', type=float, default=1e-4)
p.add_argument('--seeds', type=int, nargs='+', default=[0])
p.add_argument('--win', type=int, default=3, help='horas del GFS de entrada (t-win+1 ... t)')
p.add_argument('--lossw', default='1,1,1,1', help='peso de RH,T,U,V en la pérdida')
p.add_argument('--dec', type=int, default=0, help='bloques extra del decodificador a 3 km')
p.add_argument('--gfsup', type=int, default=0, help='1 = pasa el GFS de la hora t interpolado directo al decodificador')
p.add_argument('--noise', type=float, default=0.0, help='ruido gaussiano en la entrada al entrenar')
p.add_argument('--clim_desde', default='', help='YYYYMMDDHH: climatología solo con datos recientes (más parecidos a val/test)')
p.add_argument('--rep', type=int, default=1, help='repite REP veces las horas desde --rep_desde (más peso a lo reciente)')
p.add_argument('--rep_desde', default='2024060100')
p.add_argument('--save', default='', help='guarda la predicción de val del ensamble en <save>.npy')
a = p.parse_args()

def find(name):  # Kaggle (/kaggle/input) o la carpeta data/ del repo
    hits = glob.glob(f'/kaggle/input/**/{name}', recursive=True) + glob.glob(f'../data/{name}') + glob.glob(f'data/{name}')
    assert hits, f'No encuentro {name}'
    return hits[0]

tr, st = np.load(find('train.npz')), np.load(find('static.npz'))
Xtr, Ytr, ttr = tr['X'], tr['Y'], tr['times'].astype(str)
dem = st['dem']; VARS = ['RH', 'T', 'U', 'V']
hour = lambda t: np.array([int(k[-2:]) for k in t])
val = ttr >= '2024061600'; trn = ~val

def climatology(Y, t):
    h = hour(t); return np.stack([Y[h == k].mean(0) for k in range(24)])

cm = trn & (ttr >= a.clim_desde) if a.clim_desde else trn
clim_all = climatology(Ytr[cm], ttr[cm])
clim_rmse_val = np.sqrt(((climatology(Ytr[trn], ttr[trn])[hour(ttr[val])] - Ytr[val]) ** 2).mean(axis=(0, 1, 2)))
def local_score(pred, true):
    rmse = np.sqrt(((pred - true) ** 2).mean(axis=(0, 1, 2)))
    return 1 - (rmse / clim_rmse_val).mean(), dict(zip(VARS, rmse.round(3).tolist()))

def windows(X, t):  # igual que el starter: si falta una hora previa, repite la actual
    ts = pd.to_datetime(t, format='%Y%m%d%H'); pos = {k: i for i, k in enumerate(ts)}
    out = np.empty((len(X), a.win) + X.shape[1:], np.float32)
    for i, k in enumerate(ts):
        for j, lag in enumerate(range(a.win - 1, -1, -1)):
            idx = pos.get(k - pd.Timedelta(hours=lag)); out[i, j] = X[idx] if idx is not None else X[i]
    return out
Wtr = windows(Xtr, ttr)

dev = 'cuda'
mu_x = Xtr[trn].mean((0, 1, 2)); sd_x = Xtr[trn].std((0, 1, 2))
anom_sd = (Ytr[trn] - clim_all[hour(ttr[trn])]).std((0, 1, 2))
glat, glon, wlat, wlon = st['gfs_lats'], st['gfs_lons'], st['wrf_lats'], st['wrf_lons']
LAT, LON = np.meshgrid(wlat, wlon, indexing='ij')
gy = (LAT - glat[0]) / (glat[-1] - glat[0]) * 2 - 1; gx = (LON - glon[0]) / (glon[-1] - glon[0]) * 2 - 1
GRID = torch.tensor(np.stack([gx, gy], -1)[None], dtype=torch.float32, device=dev)

z = lambda m: (m - m.mean()) / m.std()
static = [z(dem)]
if a.terrain:
    dy, dx = np.gradient(dem)  # pendiente norte-sur y este-oeste: el viento sigue el relieve
    static += [z(dy), z(dx), z(LAT), z(LON), z(dem - (np.roll(dem, 1, 0) + np.roll(dem, -1, 0) + np.roll(dem, 1, 1) + np.roll(dem, -1, 1)) / 4)]
STATIC = torch.tensor(np.stack(static), dtype=torch.float32, device=dev)[None]
NS = STATIC.shape[1]

def block(i, o): return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.GELU(), nn.Conv2d(o, o, 3, padding=1), nn.GELU())

class Net(nn.Module):
    def __init__(s, w):
        super().__init__()
        s.enc = nn.Sequential(block(4 * a.win + 2, w), *[block(w, w) for _ in range(a.enc - 1)])
        s.learned = nn.Parameter(torch.zeros(1, 8, 70, 35))
        c = w + NS + 8 + 4 * a.gfsup
        if a.arch == 'base':
            s.dec = nn.Sequential(nn.Conv2d(c, w, 3, padding=1), nn.GELU(), nn.Conv2d(w, w, 3, padding=1), nn.GELU(), *[block(w, w) for _ in range(a.dec)], nn.Conv2d(w, 4, 1))
        else:  # U-Net chica a 3 km: más campo de visión sobre el relieve fino
            s.d0, s.d1, s.d2 = block(c, w), block(w, 2 * w), block(2 * w, 4 * w)
            s.u1, s.u0 = block(6 * w, 2 * w), block(3 * w, w)
            s.out = nn.Conv2d(w, 4, 1)
    def forward(s, x, h):
        B = x.shape[0]
        x = x.permute(0, 1, 4, 2, 3).reshape(B, 4 * a.win, 17, 13)
        ang = 2 * np.pi * h / 24
        hh = torch.stack([torch.sin(ang), torch.cos(ang)], 1)[..., None, None].expand(B, 2, 17, 13)
        f = F.grid_sample(s.enc(torch.cat([x, hh], 1)), GRID.expand(B, -1, -1, -1), align_corners=True)
        f = torch.cat([f, STATIC.expand(B, -1, -1, -1), s.learned.expand(B, -1, -1, -1)], 1)
        if a.gfsup: f = torch.cat([f, F.grid_sample(x[:, -4:], GRID.expand(B, -1, -1, -1), align_corners=True)], 1)
        if a.arch == 'base': return s.dec(f).permute(0, 2, 3, 1)
        e0 = s.d0(f); e1 = s.d1(F.avg_pool2d(e0, 2, ceil_mode=True)); e2 = s.d2(F.avg_pool2d(e1, 2, ceil_mode=True))
        up = lambda t, ref: F.interpolate(t, size=ref.shape[-2:], mode='bilinear', align_corners=False)
        d1 = s.u1(torch.cat([up(e2, e1), e1], 1)); d0 = s.u0(torch.cat([up(d1, e0), e0], 1))
        return s.out(d0).permute(0, 2, 3, 1)

to_t = lambda v: torch.tensor(v, dtype=torch.float32, device=dev)
CLIM, ASD = to_t(clim_all), to_t(anom_sd)
LW = to_t([float(v) for v in a.lossw.split(',')]); LW = LW / LW.mean()
prep = lambda W, t: (to_t((W - mu_x) / sd_x), torch.tensor(hour(t), dtype=torch.long, device=dev))
def predict(m, W, t, bs=256):
    m.eval(); out = []
    with torch.no_grad():
        for s in range(0, len(W), bs):
            x, h = prep(W[s:s + bs], t[s:s + bs]); out.append((CLIM[h] + m(x, h.float()) * ASD).cpu().numpy())
    return np.concatenate(out)

preds = []
for seed in a.seeds:
    torch.manual_seed(seed); np.random.seed(seed)
    m = Net(a.width).to(dev)
    opt = torch.optim.AdamW(m.parameters(), lr=a.lr, weight_decay=a.wd)
    itr = np.where(trn)[0]; itr = np.concatenate([itr] + [itr[ttr[itr] >= a.rep_desde]] * (a.rep - 1)); spe = int(np.ceil(len(itr) / 32))
    sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=a.lr, total_steps=a.epochs * spe)
    best, best_p, t0 = -9e9, None, time.time()
    for ep in range(a.epochs):
        m.train(); np.random.shuffle(itr)
        for s in range(0, len(itr), 32):
            b = itr[s:s + 32]; x, h = prep(Wtr[b], ttr[b])
            if a.noise: x = x + a.noise * torch.randn_like(x)
            loss = (((m(x, h.float()) - (to_t(Ytr[b]) - CLIM[h]) / ASD) ** 2) * LW).mean()
            opt.zero_grad(); loss.backward(); opt.step(); sched.step()
        pv = predict(m, Wtr[val], ttr[val]); sc, _ = local_score(pv, Ytr[val])
        if sc > best: best, best_p, best_ep = sc, pv, ep + 1
    preds.append(best_p)
    print(f'semilla {seed}: mejor val {best:.4f} (época {best_ep}) · {local_score(best_p, Ytr[val])[1]} · {time.time() - t0:.0f}s', flush=True)
sc, pv = local_score(np.mean(preds, 0), Ytr[val])
print(f'RESULTADO {vars(a)} -> ensamble {sc:.4f} {pv}')
if a.save: np.save(f'{a.save}.npy', np.mean(preds, 0))
