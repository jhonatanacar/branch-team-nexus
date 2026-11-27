# Tanda 4 (26 nov): pruebas chicas para elegir camino. Base = config I (w128, enc1, wd1e-4), 3 semillas.
# Cada prueba cambia UNA cosa respecto de la base. Val = 16–30 jun, igual que siempre.
import glob, subprocess, sys, numpy as np
BASE = '--width 128 --enc 1 --wd 1e-4 --seeds 0 1 2'
RUNS = {
    '0_base':   '',
    '1_win6':   '--win 6',           # 6 horas de GFS en vez de 3: más memoria del día
    '2_viento': '--lossw 1,1,2,2',   # doble peso a U y V en la pérdida
    '3_dec2':   '--dec 2',           # decodificador más profundo a 3 km: más detalle del relieve
    '4_gfsup':  '--gfsup 1',         # GFS de la hora t interpolado directo al decodificador
    '5_ruido':  '--noise 0.1',       # ruido en la entrada: generalizar a otra época
    '6_ep40':   '--epochs 40',       # entrenar más largo
}
for name, args in RUNS.items():
    subprocess.run([sys.executable, 'exp.py', *BASE.split(), *args.split(), '--save', name], check=True)

tr = np.load(glob.glob('/kaggle/input/**/train.npz', recursive=True)[0])
Y, t = tr['Y'], tr['times'].astype(str); h = np.array([int(k[-2:]) for k in t]); val = t >= '2024061600'
clim = np.stack([Y[~val][h[~val] == k].mean(0) for k in range(24)])
crm = np.sqrt(((clim[h[val]] - Y[val]) ** 2).mean((0, 1, 2)))
def sc(P):
    r = np.sqrt(((P - Y[val]) ** 2).mean((0, 1, 2))); return float(1 - (r / crm).mean()), r
base, rb = sc(np.load('0_base.npy'))
print('\nRESUMEN (3 semillas c/u; diferencias < ~0.003 son ruido)')
for n in sorted(RUNS, key=lambda n: -sc(np.load(f'{n}.npy'))[0]):
    s, r = sc(np.load(f'{n}.npy'))
    print(f'RESULTADO ablacion {n:9s} val {s:.4f} ({s - base:+.4f}) · dRMSE RH {r[0]-rb[0]:+.3f} T {r[1]-rb[1]:+.3f} U {r[2]-rb[2]:+.3f} V {r[3]-rb[3]:+.3f}')
