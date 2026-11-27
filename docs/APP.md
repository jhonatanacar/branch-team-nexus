# ¿Riego esta tarde? · Cómo funciona la app

App de TEAM NEXUS para la Hackathon IA PUCP 2026. Ayuda a un **agricultor de papa** del Callejón de Huaylas
(Recuay–Huaraz–Carhuaz, chacras entre 3,500 y 4,000 m) a tomar una decisión concreta:
**¿riego esta tarde para proteger la papa de la helada de esta noche?**

Código: [`app/app_heladas.py`](../app/app_heladas.py) (interfaz) y [`app/ejemplo_producto.py`](../app/ejemplo_producto.py) (modelo y descarga).

---

## 1. El problema que resuelve

- La helada quema la hoja de la papa desde unos −1 °C. En una noche despejada, la hoja queda 2–3 °C más fría que el aire.
- Regar en la tarde ayuda: el suelo húmedo guarda el calor del día y lo suelta de noche. Es barato y habitual en la zona,
  pero hay que decidirlo **antes de las 5 p. m.** (turno de agua).
- El pronóstico global (GFS) tiene celdas de **27 km**. Una sola celda mezcla valles de 3,000 m con nevados de más de 5,000 m,
  así que **no ve el frío de las chacras altas**. Nuestro modelo baja ese pronóstico a **3 km**, donde sí se ve el relieve.

## 2. Qué ve el usuario

1. **Elige su pueblo** en la barra lateral: Huaraz, Carhuaz o Recuay.
2. **Recibe la respuesta en grande**, con un color según el riesgo:

   | Mínima esperada en sus chacras | Mensaje |
   |---|---|
   | ≤ 0 °C | 🚨 **Sí, riega esta tarde** (antes de las 5 p. m.). Si baja de −2 °C: prepara **humo de madrugada** (4–6 a. m.) |
   | 0 a 3 °C | ⚠️ **Riesgo moderado**: riega si al atardecer el cielo está despejado y sin viento |
   | > 3 °C | ✅ **No hace falta regar por helada** |

3. **Comparación "nuestro modelo vs. GFS solo"**: dos números lado a lado, la mínima a 3 km y la del GFS de 27 km.
   Si llevan a decisiones distintas, la app lo avisa. Esta comparación demuestra que **el modelo no es decorativo**:
   sin él, la decisión sería otra.
4. **Curva de la noche**: temperatura hora por hora (18:00 a 08:00, hora de Lima) en la chacra más fría, con las dos fuentes.
5. **Mapa de la Cordillera Blanca**: mínima de la noche a 3 km, la línea de 0 °C, las celdas de sus chacras y los pueblos.
6. **Botón "📲 Compartir por WhatsApp"**: abre WhatsApp con la alerta escrita (pueblo, noche, decisión y mínima) para reenviarla al grupo de la comunidad. Usa un enlace `wa.me`: no necesita cuenta ni API.

## 3. Qué pasa por dentro (de punta a punta)

```
Open-Meteo (GFS actual, 17×13 puntos, 27 km)
      │  descargar_gfs(48)  → si falla, usa la última descarga guardada
      ▼
Ventanas de 3 horas seguidas (t−2, t−1, t)        make_windows()
      ▼
Nuestro modelo (ensamble de CNN, mismos pesos que Kaggle)   predecir() → models/
      ▼
Mapas de 3 km (70×35) de humedad, temperatura y viento, hora por hora
      ▼
Se eligen las celdas "chacra" y las horas de "esta noche"
      ▼
Mínima → decisión (regar / riesgo moderado / no regar)
```

Detalle de cada paso:

- **Descarga del GFS** (`descargar_gfs`): pide 48 horas de pronóstico a Open-Meteo y lo guarda en `app/gfs_cache.npz`.
  Si la descarga tiene menos de 1 hora, reusa la caché. Si Open-Meteo no responde (o no hay internet), **usa la última
  descarga guardada** y muestra un aviso. Lo exige la Guía del participante: en la demo no hay segunda oportunidad.
- **Modelo** (`predecir`): carga una sola vez el ensamble de `models/` con `train/modelo.py`, **el mismo código y los mismos
  pesos** que generaron nuestra submission de Kaggle. Junto a los pesos se cargan `models/stats.npz` (normalización y
  climatología), sin los cuales el modelo daría otra cosa.
- **"Tus chacras"** (`celdas_chacra`): celdas de 3 km que están a **10 km o menos** del pueblo y **entre 3,500 y 4,000 m**
  según el relieve (DEM). En Huaraz son 16 celdas.
- **"Esta noche"** (`noche`): la primera franja de 18:00 a 08:00 (hora de Lima) a partir de ahora. **Antes del mediodía**
  se toma la noche que viene, no la que termina, porque la decisión se toma en la tarde.
- **Decisión** (`decision`): la mínima de la noche en la **chacra más fría** (criterio prudente) contra los umbrales de la tabla.
- **GFS sin modelo**: el mismo GFS interpolado a 3 km sin corregir nada. Representa lo que vería cualquier app del clima.

## 4. Modo demo con fechas pasadas

En la barra lateral, **"Fecha pasada (demo)"** permite elegir una noche desde 2022 (por defecto, el 15 de julio de 2024).
Descarga el GFS histórico de esa fecha desde Open-Meteo y corre el mismo modelo.

Sirve porque en noviembre y diciembre (época de lluvias) casi no hay heladas: con julio (época seca) se puede mostrar una
alerta real en el video y en la final.

Ejemplos medidos (Huaraz):

| Noche | Modelo 3 km | GFS solo | Decisión |
|---|---|---|---|
| 26→27 nov 2026 (en vivo) | 4.8 °C | 8.4 °C | No regar |
| 15→16 jul 2024 (demo) | 2.0 °C | 3.9 °C | Riesgo moderado |

(Modelo v4, LB 0.499.) En la validación (16–30 jun, fuera del entrenamiento), la Tmin de cada noche en la zona papera
tiene un error de **0.84 °C con el modelo** contra **3.45 °C con el GFS solo**.

En las chacras altas, el modelo sale **entre 2 y 4 °C más frío** que el GFS solo: justo lo que el GFS de 27 km no ve.

## 5. Cómo correrla

Con Python (3.10 o más reciente) y la data de Kaggle en `data/` (al menos `static.npz`):

```bash
pip install -r requirements.txt
streamlit run app/app_heladas.py
```

Se abre en <http://localhost:8501>.

Con Docker (como en la PC del equipo, imagen `nexus-train` de `train/Dockerfile`):

```bash
MSYS_NO_PATHCONV=1 docker run --rm -p 8501:8501 -v "$PWD:/w" -w /w nexus-train \
  sh -c 'pip install -q requests streamlit && streamlit run app/app_heladas.py --server.address 0.0.0.0'
```

Versión sin interfaz (genera un mapa PNG en `app/salidas/`): `python app/ejemplo_producto.py`.

## 6. Limitaciones (decirlas en el reporte y en el pitch)

- **Cambio de época**: el modelo se entrenó con feb–jun 2024. En vivo corre en otra época del año (lluvias), y el GFS de
  Open-Meteo puede no ser idéntico al de la data oficial.
- **Umbrales y pueblos**: los umbrales (0 y 3 °C), el radio de 10 km y las coordenadas de los pueblos son una propuesta
  del equipo; falta validarlos con agricultores o con un técnico agrario.
- **Temperatura a 2 m**: el modelo da la temperatura del aire, no la de la hoja (que en noches despejadas es más baja).
  Por eso el umbral de riesgo empieza en 3 °C: además, el modelo suaviza los extremos y con 3 °C detecta el 91 % de los casos de riesgo real (con 2 °C, solo el 51 %; validación 16–30 jun, modelo v4).
- **GFS sin modelo**: la comparación usa una interpolación simple, sin corregir por altura.
- **Es una guía**: no reemplaza mirar el cielo al atardecer (cielo despejado y sin viento = más helada).

## 7. Pendiente

- ~~Botón de WhatsApp~~ hecho: "📲 Compartir por WhatsApp" abre `wa.me` con la alerta lista para el grupo de la comunidad.
- Elegir una **noche de julio de 2024** en la que el GFS y el modelo den decisiones distintas, para el video.
- Validar los umbrales y los pueblos (Keila).
