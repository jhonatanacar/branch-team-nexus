# Entorno de entrenamiento: PyTorch con CUDA 12.8 (necesario para GPUs Blackwell, p. ej. RTX 50xx)
FROM pytorch/pytorch:2.7.0-cuda12.8-cudnn9-runtime
RUN pip install --no-cache-dir numpy==2.2.6 pandas==2.2.3 matplotlib==3.10.3 nbconvert==7.16.6 ipykernel==6.29.5
WORKDIR /w/train
