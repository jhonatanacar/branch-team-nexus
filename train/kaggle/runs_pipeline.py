# Corre el pipeline todo en uno (selección -> ensamble -> final con todo train -> submission.csv)
import subprocess, sys
subprocess.run([sys.executable, 'pipeline.py'], check=True)
