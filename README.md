# 🥔 ¿Riego esta tarde? · TEAM NEXUS

**Alerta de heladas para agricultores de papa del Callejón de Huaylas (Recuay–Huaraz–Carhuaz), con pronóstico a 3 km.**
Hackathon IA PUCP 2026 · DSC PUCP × IA-PUCP.

El pronóstico global (GFS) tiene celdas de 27 km: mezcla valles de 3,000 m con nevados de más de 5,000 m y no ve el frío
de las chacras. Nuestro modelo lo baja a **3 km** y la app responde una sola pregunta, a tiempo para el turno de agua:
**¿riego esta tarde para proteger la papa de la helada de esta noche?**

- **Producto:** se ejecuta en local (ver abajo) · **Video pitch:** [pendiente]
- **Reporte:** [`REPORTE_PRODUCTO.md`](REPORTE_PRODUCTO.md) · **Cómo funciona la app:** [`docs/APP.md`](docs/APP.md)
- **Kaggle:** score público **0.49916** (ensamble de CNN con ancla en el GFS, mismos pesos que usa la app)

| | Error de la mínima de cada noche en las chacras (validación 16–30 jun 2024) |
|---|---|
| GFS solo (27 km) | 3.45 °C |
| **Nuestro modelo (3 km)** | **0.84 °C** |

## Correr la app (5 minutos)

Necesitas Python 3.10 o más reciente e internet (para el GFS de Open-Meteo). **No hace falta bajar la data de Kaggle**:
los pesos, la normalización y el relieve están en `models/`.

```bash
git clone <url-de-este-repo> && cd <carpeta>
python -m venv .venv
# Windows: .venv\Scripts\activate      ·      Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/app_heladas.py
```

Se abre en <http://localhost:8501>. En la barra lateral:

1. Elige el pueblo cercano a tu chacra (Huaraz, Carhuaz o Recuay).
2. **Pronóstico de hoy** usa el GFS actual. **Fecha pasada (demo)** corre el mismo modelo sobre una noche histórica
   (por defecto, el 3 de agosto de 2024: el modelo dice −0.2 °C y "riega"; el GFS solo dice 4.9 °C y "no hace falta").
3. Lee la decisión, compárala con el GFS solo, mira la curva de la noche y el mapa, y compártela por WhatsApp.

Si Open-Meteo no responde, la app usa la última descarga guardada (`app/gfs_cache.npz`) y lo avisa.

Versión sin interfaz (mapa PNG en `app/salidas/`): `python app/ejemplo_producto.py`.

## Reproducir el modelo (`train/`)

Necesita la data oficial en `data/` (pestaña *Data* de la competencia: `train.npz`, `test.npz`, `static.npz`,
`sample_submission.csv`) y una GPU (Kaggle T4: ~2 h).

```bash
cd train && python pipeline.py          # prueba rápida: QUICK=1 python pipeline.py
```

`pipeline.py` corre solo, sin decisiones manuales:

1. **Selección:** entrena cada configuración con 5 semillas y valida con corte temporal (val = 16–30 jun 2024).
2. **Ensamble:** elige de forma greedy qué configuraciones promediar según el score de validación.
3. **Final:** reentrena las elegidas con todo train hasta su mejor época.
4. **Salidas:** escribe `submission.csv`, `models/*.pt`, `models/stats.npz` y `models/config.json`.

El código del modelo está en `train/modelo.py`, y la app usa ese mismo archivo. Para correrlo en Docker con GPU:
`docker build -t nexus-train train/`.

| Carpeta | Contenido |
|---|---|
| `app/` | `app_heladas.py` (app Streamlit), `ejemplo_producto.py` (descarga del GFS + modelo), `gfs_forecast.py` |
| `train/` | `modelo.py` (red, ancla, predicción), `pipeline.py` (entrenamiento completo), `exp.py` (pruebas), `kaggle/` (automatización) |
| `models/` | Ensamble final: 5 configuraciones × 5 semillas (99 MB) + `stats.npz` + `config.json` |
| `docs/` | `APP.md`, `BITACORA.md` (decisiones y resultados), `PREGUNTAS.md` |

## Equipo

**TEAM NEXUS** · Keila Rocio Delgado (producto y relato) · Jhonatan Adbbell Carhuamaca Tolentino (modelo)

Data: proyecto AIRE-ANDINO (PUCP), reprocesada para la hackathon. GFS en vivo: [Open-Meteo](https://open-meteo.com/).
