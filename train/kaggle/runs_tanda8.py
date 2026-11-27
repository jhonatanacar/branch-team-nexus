# Tanda 8 (26 nov, ~8 h): librería. Cada config deja val_<c>.npy + pesos + submission_<c>.csv apenas termina.
# Mañana: data/libreria.py arma el mejor ensamble en local con todo eso, sin volver a entrenar.
import os, subprocess, sys
env = dict(os.environ, ALL_FINAL='1', LIMITE_H='10.5')
subprocess.run([sys.executable, 'pipeline.py'], check=True, env=env)
