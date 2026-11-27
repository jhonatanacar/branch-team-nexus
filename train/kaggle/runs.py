# Experimentos que corre el notebook de Kaggle (editar esta lista para cada tanda)
import glob, subprocess, sys, numpy as np, torch
print("CUDA disponible:", torch.cuda.is_available(), torch.__version__, flush=True)
subprocess.run("nvidia-smi -L", shell=True)
RUNS = {
    'A_base':     '--seeds 0 1 2 3 4',
    'B_enc2_w96': '--enc 2 --width 96 --seeds 0 1 2 3 4',
}
for name, args in RUNS.items():
    subprocess.run([sys.executable, 'exp.py', *args.split(), '--save', name], check=True)
# Ensamble entre configuraciones (mismo split y misma métrica que exp.py)
tr = np.load(glob.glob('/kaggle/input/**/train.npz', recursive=True)[0])
Y, t = tr['Y'], tr['times'].astype(str); h = np.array([int(k[-2:]) for k in t]); val = t >= '2024061600'
clim = np.stack([Y[~val][h[~val] == k].mean(0) for k in range(24)])
crm = np.sqrt(((clim[h[val]] - Y[val]) ** 2).mean((0, 1, 2)))
P = np.mean([np.load(f'{n}.npy') for n in RUNS], 0)
rmse = np.sqrt(((P - Y[val]) ** 2).mean((0, 1, 2)))
print('RESULTADO ensamble de todas las configs ->', round(float(1 - (rmse / crm).mean()), 4), rmse.round(3))
