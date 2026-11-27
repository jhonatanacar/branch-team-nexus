# Reporte del producto · TEAM NEXUS

**Integrantes:** Keila Rocio Delgado, Jhonatan Adbbell Carhuamaca Tolentino
**Producto:** se ejecuta en local, ver [README](README.md) (`streamlit run app/app_heladas.py`)
**Video pitch:** [pendiente]

---

## 1. ¿Qué modelo o arquitectura usaron?

Un **ensamble de 25 CNN**: 5 configuraciones × 5 semillas.

**Entradas de cada red:**
- 3 horas seguidas del GFS (t−2, t−1, t) con RH, T, U y V, sobre la grilla de 17×13: 12 canales.
- El seno y el coseno de la hora del día.

**Cómo funciona:**
1. Un codificador convolucional procesa esa grilla de 27 km.
2. `grid_sample` lleva el resultado a la grilla de 3 km (70×35).
3. Se le suman el relieve (DEM) y un mapa estático aprendido.
4. Un decodificador corrige un **punto de partida físico**.

**El punto de partida es la idea clave (el "ancla GFS"):**
- Partimos de la climatología del WRF para esa hora más la *anomalía del GFS* interpolada a 3 km.
- La red solo aprende lo que falta: el efecto del relieve sobre esa anomalía.
- Como el GFS trae el cambio de estación, el modelo generaliza mejor de feb–jun (entrenamiento) a jul–ago (test).
- Solo esta idea subió el score público de 0.477 a 0.499.

**Entrenamiento y validación:**
- Pérdida MSE sobre la diferencia normalizada por variable.
- AdamW con OneCycle durante 25 épocas, quedándonos con la mejor época.
- **Validación con corte temporal:** val = 16–30 jun 2024, nunca un split aleatorio.
- El ensamble se elige de forma greedy en val y luego se reentrena con todo train.
- Medimos que el ruido entre semillas es de unos ±0.003. Por eso solo aceptamos cambios que mejoren ≥ 0.005 en val y no
  perseguimos el leaderboard público.

| | |
|---|---|
| Arquitectura | Ensamble de 25 CNN (codificador 27 km → `grid_sample` → decodificador 3 km con DEM), con ancla GFS |
| Parámetros / tamaño de los pesos | 25.6 M en total (≈1 M por red) · 99 MB (`models/`) |
| Score en el leaderboard público | **0.49916** |
| Score en tu validación local | **0.393** (16–30 jun 2024; 0 = climatología, 1 = perfecto) |
| Tiempo de inferencia (24 horas de pronóstico) y hardware | ≈ 4 s en CPU (4 hilos), sin GPU |

## 2. ¿Para quién es y qué problema le resuelve?

**Usuario:** el pequeño agricultor de papa del Callejón de Huaylas, entre Recuay, Huaraz y Carhuaz, con chacras entre 3,500 y 4,000 m.

**Qué le pasa en la época seca (junio–agosto):** las noches despejadas traen heladas, y la hoja de la papa se quema desde unos −1 °C.

**La decisión:** la defensa más barata es **regar en la tarde**, porque el suelo húmedo guarda el calor y lo suelta de
noche. Pero hay que decidirlo antes del turno de agua (≈ 5 p. m.).

**Qué tiene hoy:** decide mirando el cielo, o con una app del clima que usa el GFS de 27 km. Ese GFS se equivoca en las
dos direcciones:
- En Huaraz sale 3–4 °C más cálido: no avisa la helada.
- En Carhuaz y Recuay sale 3–7 °C más frío, porque su celda incluye los nevados: alarma casi todas las noches, y el
  agricultor deja de creerle.

**Con el producto:** recibe una respuesta concreta para *sus* chacras, a 3 km:
- "Sí, riega esta tarde" (y prepara humo de madrugada si baja de −2 °C).
- "Riesgo moderado".
- "No hace falta".

## 3. ¿Cuál es la propuesta de valor del producto?

**Saber antes de las 5 p. m. si esta noche hiela en tus chacras, con un error de ~0.8 °C en vez de ~3.5 °C.**

En la validación (16–30 jun 2024, 112 celdas de la zona papera):

| | Nuestro modelo | GFS solo |
|---|---|---|
| Error de la mínima de cada noche | 0.84 °C | 3.45 °C |
| Casos con error mayor a 2 °C | 3 % | 62 % |
| Celdas en riesgo real (≤ 2 °C) detectadas | 91 % (umbral de alerta 3 °C) | 29 % (con 87 % de falsas alarmas) |
| Noches acertadas en la zona | 16/16 | 14/16 |

Regar de más cuesta poco; una helada no avisada puede quemar la campaña.

## 4. ¿Por qué tu producto es diferente a algo usual?

- **No es un mapa del clima, es una decisión.** La app responde "¿riego esta tarde?" con el lenguaje del agricultor y a la
  hora en que lo necesita: elige sola la noche que viene y mira solo sus chacras (celdas de 3,500–4,000 m a ≤ 10 km de su pueblo).
- **Muestra por qué confiar.** Pone lado a lado nuestra mínima y la del GFS solo, y avisa cuando llevan a decisiones distintas.
  Ejemplo: el 3 de agosto de 2024, en Huaraz, el modelo dice −0.2 °C ("riega") y el GFS solo 4.9 °C ("no hace falta").
- **Llega a la comunidad.** Un botón arma el mensaje para reenviarlo por WhatsApp al grupo del pueblo, sin cuentas ni API.
- **Aguanta fallas.** Si Open-Meteo no responde, usa la última descarga guardada y lo avisa.

## 5. ¿Cómo usa el producto la salida de tu modelo?

```
Open-Meteo (GFS actual, 17×13, 27 km) → caché de 1 h (respaldo si falla)
  → ventanas de 3 horas (t−2, t−1, t)
  → nuestro ensamble (models/, los mismos pesos y el mismo código que la submission de Kaggle)
  → mapas de 3 km (70×35) de RH, T, U y V, hora por hora
  → celdas "tus chacras" (3,500–4,000 m a ≤ 10 km del pueblo) × horas de "esta noche" (18:00–08:00 Lima)
  → mínima en la chacra más fría → decisión, curva de la noche, mapa y mensaje de WhatsApp
```

**El valor depende del downscaling:** sin el modelo, la misma app con el GFS interpolado daría otra decisión en la mayoría
de las noches de julio de 2024. Verificamos que el GFS de Open-Meteo es **idéntico** al `X` oficial con el que entrenamos
(diferencia 0 en 120 horas), así que en vivo el modelo recibe la misma entrada que vio al entrenar. El modo demo corre el
mismo modelo sobre fechas pasadas, para mostrar heladas fuera de temporada.

## 6. Limitaciones y próximos pasos

**Limitaciones:**
- **Temperatura del aire, no de la hoja.** El modelo da T a 2 m. En noches despejadas, la hoja queda 2–3 °C más fría.
  Además, el modelo suaviza los extremos. Por eso el riesgo empieza en 3 °C y no en 0 °C.
- **Época del año.** Entrenamos con feb–jun 2024. En vivo, en época de lluvias (nov–mar), hay pocas heladas y el modelo
  trabaja fuera de lo que vio. Las heladas reales del val fueron pocas (1 % de los casos), así que la detección de ≤ 0 °C
  (70 %) tiene muestra chica.
- **Pronóstico.** En vivo se suma el error propio del GFS a 24–48 h.
- **Viento.** Es la variable con más error (60 % de lo que le falta al modelo), aunque no afecta esta decisión.
- **Por validar en campo.** Los umbrales (0 y 3 °C), el radio de 10 km y la ubicación de los pueblos son una propuesta
  del equipo; falta validarlos con agricultores o con técnicos de la agencia agraria.

**Próximos pasos:**
- Alertas automáticas por WhatsApp o SMS a las 2 p. m.
- Más pueblos y cultivos: maíz y habas, con sus propios umbrales.
- Usar la humedad y el viento para estimar si la noche será despejada y calma (más helada).
- Validar con observaciones de estaciones de SENAMHI.
