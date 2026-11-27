# Tanda 7 (26 nov): las 5 configs de v4 con semillas 5-9. Se promedian luego con las 0-4 (v4 x10 semillas).
# ALL_FINAL=1 asegura los pesos finales de las 5 aunque el greedy deje alguna fuera.
import os, subprocess, sys
env = dict(os.environ, SOLO='Gg,Igr,Hg,I,Ggr', SEEDS='5,6,7,8,9', ALL_FINAL='1')
subprocess.run([sys.executable, 'pipeline.py'], check=True, env=env)
