"""Modelo de downscaling GFS (17x13) -> WRF (70x35) de TEAM NEXUS.
Lo usan el entrenamiento (pipeline.py) y el producto (app/), así ambos dan exactamente lo mismo."""
import numpy as np, pandas as pd
import torch, torch.nn as nn, torch.nn.functional as F

VARS = ['RH', 'T', 'U', 'V']


def hour(t):
    return np.array([int(str(k)[-2:]) for k in t])


def windows(X, t):
    """(N,17,13,4) -> (N,3,17,13,4) con las horas t-2, t-1, t. Si falta una hora previa, repite la actual."""
    ts = pd.to_datetime(np.asarray(t).astype(str), format='%Y%m%d%H'); pos = {k: i for i, k in enumerate(ts)}
    out = np.empty((len(X), 3) + X.shape[1:], np.float32)
    for i, k in enumerate(ts):
        for j, lag in enumerate([2, 1, 0]):
            idx = pos.get(k - pd.Timedelta(hours=lag)); out[i, j] = X[idx] if idx is not None else X[i]
    return out


def climatology(Y, t):
    h = hour(t); return np.stack([Y[h == k].mean(0) for k in range(24)])  # (24,70,35,4)


def make_stats(X, Y, t, static):
    """Todo lo que el modelo necesita además de los pesos. Se guarda en models/stats.npz."""
    clim = climatology(Y, t)
    s = dict(mu_x=X.mean((0, 1, 2)), sd_x=X.std((0, 1, 2)), clim=clim,
             anom_sd=(Y - clim[hour(t)]).std((0, 1, 2)), gclim=climatology(X, t),
             dem=static['dem'], gfs_lats=static['gfs_lats'], gfs_lons=static['gfs_lons'],
             wrf_lats=static['wrf_lats'], wrf_lons=static['wrf_lons'])
    s['anom_sd_gfs'] = (Y - base(s, X, t, 'gfs')).std((0, 1, 2))
    return s


def wrf_grid(stats):
    """Coordenadas de la grilla WRF en el sistema [-1,1] de grid_sample sobre la grilla GFS. (1,70,35,2)"""
    LAT, LON = np.meshgrid(stats['wrf_lats'], stats['wrf_lons'], indexing='ij')
    glat, glon = stats['gfs_lats'], stats['gfs_lons']  # GFS fila 0 = norte; WRF fila 0 = sur
    gy = (LAT - glat[0]) / (glat[-1] - glat[0]) * 2 - 1; gx = (LON - glon[0]) / (glon[-1] - glon[0]) * 2 - 1
    return torch.tensor(np.stack([gx, gy], -1)[None], dtype=torch.float32)


def base(stats, X, t, anchor='clim', bs=512):
    """Punto de partida que la red corrige. 'clim': climatología por hora (feb-jun).
    'gfs': climatología + anomalía del GFS interpolada a 3 km, así el cambio de época del GFS pasa directo.
    X: (N,17,13,4) físico (la hora t)."""
    h = hour(t); B = stats['clim'][h].astype(np.float32)
    if anchor == 'gfs':
        g = wrf_grid(stats)
        for s in range(0, len(X), bs):
            a = torch.tensor((X[s:s + bs] - stats['gclim'][h[s:s + bs]]).astype(np.float32)).permute(0, 3, 1, 2)
            B[s:s + bs] += F.grid_sample(a, g.expand(len(a), -1, -1, -1), align_corners=True).permute(0, 2, 3, 1).numpy()
    return B


def anom_sd(stats, anchor='clim'):
    return stats['anom_sd_gfs'] if anchor == 'gfs' else stats['anom_sd']


def block(i, o):
    return nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.GELU(), nn.Conv2d(o, o, 3, padding=1), nn.GELU())


class Net(nn.Module):
    """CNN sobre el GFS -> interpolación a 3 km -> + relieve + mapa aprendido -> anomalía normalizada."""
    def __init__(self, stats, w=64, enc=1, anchor='clim'):
        super().__init__()
        self.anchor = anchor
        dem = stats['dem']
        self.register_buffer('grid', wrf_grid(stats), persistent=False)
        self.register_buffer('dem', torch.tensor((dem - dem.mean()) / dem.std(), dtype=torch.float32)[None, None], persistent=False)
        self.enc = nn.Sequential(block(14, w), *[block(w, w) for _ in range(enc - 1)])
        self.learned = nn.Parameter(torch.zeros(1, 8, 70, 35))
        self.dec = nn.Sequential(nn.Conv2d(w + 9, w, 3, padding=1), nn.GELU(),
                                 nn.Conv2d(w, w, 3, padding=1), nn.GELU(), nn.Conv2d(w, 4, 1))

    def forward(self, x, h):  # x: (B,3,17,13,4) normalizado, h: (B,) hora UTC
        B = x.shape[0]
        x = x.permute(0, 1, 4, 2, 3).reshape(B, 12, 17, 13)
        ang = 2 * np.pi * h / 24
        hh = torch.stack([torch.sin(ang), torch.cos(ang)], 1)[..., None, None].expand(B, 2, 17, 13)
        f = F.grid_sample(self.enc(torch.cat([x, hh], 1)), self.grid.expand(B, -1, -1, -1), align_corners=True)
        f = torch.cat([f, self.dem.expand(B, -1, -1, -1), self.learned.expand(B, -1, -1, -1)], 1)
        return self.dec(f).permute(0, 2, 3, 1)


@torch.no_grad()
def predict(models, stats, W, t, bs=256):
    """Promedio del ensamble en unidades físicas. models: lista de listas (una por configuración)."""
    dev = next(models[0][0].parameters()).device
    tt = lambda v: torch.tensor(v, dtype=torch.float32, device=dev)
    h_all = hour(t); P = 0
    for grupo in models:  # cada configuración puede tener otra base (ancla); se promedia en unidades físicas
        anc = grupo[0].anchor; B, ASD = base(stats, W[:, -1], t, anc), tt(anom_sd(stats, anc)); out = []
        for s in range(0, len(W), bs):
            x = tt((W[s:s + bs] - stats['mu_x']) / stats['sd_x']); h = torch.tensor(h_all[s:s + bs], device=dev)
            out.append((torch.stack([m.eval()(x, h.float()) for m in grupo]).mean(0) * ASD).cpu().numpy())
        P = P + (B + np.concatenate(out)) / len(models)
    P = np.array(P, dtype=np.float32)
    P[..., 0] = P[..., 0].clip(0, 100)  # la RH física (y la del WRF) está entre 0 y 100 %
    return P


def load_ensemble(folder, device='cpu'):
    """Carga models/stats.npz + models/config.json + pesos. Devuelve (models, stats)."""
    import json, os
    stats = dict(np.load(os.path.join(folder, 'stats.npz')))
    cfg = json.load(open(os.path.join(folder, 'config.json')))
    models = []
    for name, c in cfg['configs'].items():
        grupo = []
        for seed in cfg['seeds']:
            m = Net(stats, c['w'], c['enc'], c.get('anchor', 'clim')).to(device)
            m.load_state_dict(torch.load(os.path.join(folder, f'{name}_s{seed}.pt'), map_location=device))
            grupo.append(m.eval())
        models.append(grupo)
    return models, stats
