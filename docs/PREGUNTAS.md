# Preguntas abiertas · TEAM NEXUS

Lista viva de las preguntas que tenemos que responder **antes de empezar a probar**.

**Cómo leer esta lista (25 nov):**
- `[x]` = decidido por el equipo o verificado con la data.
- `[ ]` + **Propuesta:** = recomendación del coach, **pendiente de que el equipo la apruebe o la cambie**.
  Cuando la aprueben, marquen `[x]` y copien la decisión a [`BITACORA.md`](BITACORA.md).

Producto: **alerta de heladas para agricultores de papa de la Cordillera Blanca** (25 nov 2026).

---

## 1. Para el equipo (lo decidimos nosotros)

### Producto
- [x] **1.** ¿Qué **cultivo** protegemos? → **Papa** (decidido por el equipo). Por qué: (a) es el cultivo principal de las
  partes altas del Callejón de Huaylas (≈3,000–4,000 m), justo la franja donde 3 km separa valle de ladera; (b) el follaje se
  daña desde ≈ −1 a −2 °C y, en noches despejadas, la hoja queda 2–3 °C más fría que el aire, así que 0–2 °C en el aire ya es
  riesgo; (c) la campaña grande se siembra en set–nov, así que en diciembre la planta está recién emergida y es más sensible;
  (d) la helada por radiación depende de **T + RH baja + viento en calma**, así que el producto usa las 4 salidas del modelo.
  Cifras de producción y pérdidas: **por verificar** (MIDAGRI/SIEA, SENAMHI).
- [x] **2.** ¿Qué **zona y altitud**? → **Aprobado (25 nov):** **Recuay–Huaraz–Carhuaz, franja de 3,500–4,000 m** (verificado en el
  DEM). La grilla WRF cubre las tres ciudades. En la caja lat −9.95 a −9.15, lon −77.80 a −77.35 hay 480 celdas, **112 en
  3,500–4,000 m** (~1,000 km²). Una sola celda GFS sobre Huaraz contiene 90 celdas WRF de 2,980 a 5,244 m (≈ 15 °C de
  diferencia por altura): eso es lo que el GFS no ve. Ojo: la celda de 3 km suaviza el fondo del valle (Carhuaz sale 2,871 m
  en el DEM frente a ~2,650 m reales); el valor es de la celda, no de la chacra.
- [x] **3.** ¿Qué **decisión concreta** toma el agricultor? → **Aprobado (25 nov):** **"¿Riego esta tarde o no?"** Principal: regar
  entre las 4 y 6 p. m. si el suelo está seco (el suelo húmedo guarda calor y lo suelta de noche, y sube la humedad; ~1–2 °C).
  Secundaria si el riesgo es alto: humo o fogatas de madrugada (4–6 a. m.). Descartadas: tapar (caro para hectáreas) y
  cosechar antes (en dic la planta recién emergió).
- [x] **4.** ¿Con **cuántas horas de anticipación**? → **Aprobado (25 nov):** **~24 h.** Aviso al **mediodía del día anterior** (da
  tiempo a pedir el turno de agua) y **confirmación a las 6 a. m.** del mismo día (antes de regar en la tarde). La data
  confirma la hora crítica: en train, el frío < 2 °C se concentra entre las 09 y 11 UTC = **4–6 a. m. hora de Lima**.
- [x] **5.** ¿Qué umbral es helada? → **Aprobado (25 nov):** usar la **T mínima de la noche a 2 m** en la celda: **< 0 °C = helada**,
  **0–2 °C = riesgo** (la hoja queda 2–3 °C más fría que el aire y la papa se daña desde ≈ −1 °C). Umbral agronómico, no el
  meteorológico de 0 °C solo.
- [x] **6.** ¿Cómo combinamos T, RH y viento en un **nivel de riesgo**? → **Aprobado (25 nov), regla simple:**
  - Base por Tmin: **alto** < 0 °C · **medio** 0–2 °C · **bajo** > 2 °C.
  - **Sube un nivel** si a la hora de la Tmin hay **viento < 2 m/s** (calma: no mezcla el aire) **y RH < 60 %** (aire seco:
    enfría más).
  - **Baja un nivel** si el viento es > 5 m/s (el aire mezclado evita la helada por radiación).
  - Umbrales iniciales; ajustarlos con la data de train (junio) antes de congelar. En train, la RH media en las horas frías
    fue 68.8 % frente a 72.8 % en el resto: el aire seco sí acompaña al frío.
- [x] **7.** ¿Por qué **canal**? → **Aprobado (25 nov):** **app web (Streamlit)** con el mapa de riesgo por comunidad, más un botón
  **"Enviar por WhatsApp"** (enlace `wa.me` con el mensaje ya escrito) para que el técnico agrario o el presidente de la
  comunidad lo reenvíe al grupo. Costo cero, sin aprobación de API. El usuario directo es el **técnico/líder comunal** (tiene
  smartphone); el agricultor recibe el mensaje en su grupo. Bot de Telegram o SMS: solo si sobra tiempo.
- [ ] **8.** ¿Qué **idioma**? → **Propuesta:** **español simple + quechua (variante de Áncash)** con **plantillas fijas**
  (3 mensajes, uno por nivel) traducidas y revisadas por un hablante. Nada de traducción con LLM en vivo (riesgo de errores).
  Ejemplo: *"Helada probable esta madrugada en Olleros (−1 °C, 5 a. m.). Riega tu papa hoy entre 4 y 6 p. m."*
- [ ] **9.** ¿Cómo mostramos valor en la demo de diciembre? → **Propuesta:** tres partes:
  1. **En vivo:** pronóstico real de los próximos días. Con el umbral de 2 °C es probable ver riesgo "medio": en train,
     **febrero (lluvias) tuvo 8 días con alguna celda < 2 °C y 2 días < 0 °C**.
  2. **Modo historia:** reproducir una helada real de **junio 2024** (18 días con alguna celda < 0 °C en la zona) con el GFS
     de esa fecha, mostrando qué habría avisado el producto y cómo se compara con lo que daba el GFS solo.
  3. Mensaje del pitch: "en lluvias hay menos heladas, pero la planta recién emergida es la más frágil".
- [ ] **10.** ¿Qué nos hace **diferentes**? → **Propuesta:** SENAMHI emite avisos por región o provincia y por rangos de
  altitud generales; una app de clima da un número para la ciudad (el fondo del valle). Nosotros damos **riesgo por comunidad
  a 3 km** (la ladera de 3,800 m no es Huaraz a 3,050 m), **con una acción y una hora concretas** (riega hoy de 4 a 6 p. m.),
  y que llega por el grupo de WhatsApp que ya usan.
- [ ] **11.** ¿Cómo **cuantificamos** el valor? → **Propuesta:** dos números.
  - **Del modelo:** error en la Tmin de madrugada del modelo frente al GFS interpolado (validación temporal, junio 2024), y
    cuántas heladas detecta cada uno (aciertos y falsas alarmas).
  - **Del negocio:** hectáreas de papa en la zona × rendimiento × precio × % de pérdida por helada (fuentes: MIDAGRI/SIEA).
    Presentarlo como "pérdida evitable estimada", con la fuente citada. **No inventar cifras.**

### Modelo
- [x] **12.** ¿Dónde entrenamos? → **Docker local con GPU** (verificado: **NVIDIA RTX 5060 Ti, 8 GB**). Ojo: es arquitectura
  Blackwell, necesita **PyTorch con CUDA 12.8+** (imagen o rueda `cu128`). El notebook final también debe correr en Kaggle T4
  para la reproducibilidad.
- [x] **13.** ¿Qué meta y hasta cuándo? → **Aprobado (25 nov):** meta **≥ 0.50 en el LB público** (el 1.º está en 0.507; da ≈ 34/35
  pts). Mejorar el modelo hasta el **jue 3 dic**; **congelar el 4 dic** y desde ahí solo producto, video y entrega.
- [x] **14.** ¿Más peso a **T** en la pérdida? → **Aprobado (25 nov):** **no** en la submission: el score promedia las 4 variables y
  el viento es donde hay más margen. En cambio, **medir aparte el error en la Tmin de madrugada** (pregunta 40) y reportarlo.
  Solo probar un peso extra para T si el score general no baja.
- [x] **15.** ¿Cuáles serán las **2 submissions finales**? → **Aprobado (25 nov):** (1) la **mejor en validación temporal** (últimas
  2 semanas de junio) y (2) una **más conservadora** (ensamble/promedio de semillas), por si la primera sobreajusta. Nunca
  elegir solo por el LB público.

### Equipo y entrega
- [x] **16.** ¿Quiénes somos? → **2 integrantes:** **Keila Rocio Delgado** y **Jhonatan Adbbell Carhuamaca Tolentino** (25 nov).
  - [x] Ambos inscritos en Luma; equipo `TEAM NEXUS` creado en Kaggle (25 nov).
  - [x] **Líder: Keila.** Llenó el formulario oficial y es la líder del equipo en Kaggle (cambiado el 25 nov).
  - [ ] Confirmar que en el formulario el nombre quedó escrito **exactamente** `TEAM NEXUS` (mayúsculas y espacio; regla 7g).
  - [x] Tras la 1.ª submission: verificar que en el leaderboard salga `TEAM NEXUS`. → **Verificado (26 nov), LB 0.47363.**
- [x] **17.** ¿Quién hace qué? → **Rol A (técnico) = Jhonatan · Rol B (producto y relato) = Keila** (25 nov):
  - **Rol A · Técnico:** modelo y submissions, `models/` + `stats.npz`, app Streamlit (carga de pesos, caché del GFS,
    despliegue), notebook reproducible.
  - **Rol B · Producto y relato:** regla de riesgo y mensajes (español/quechua), entrevista al técnico o agricultor, cifras
    con fuente, `REPORTE_PRODUCTO.md`, `README`, guion y edición del video.
  - **Juntos:** revisar las propuestas de esta lista, la prueba de "clonar en limpio" (6 dic) y grabar la demo.
- [ ] **18.** ¿Desplegado o local? → **Propuesta:** **las dos.** Desplegar en **Hugging Face Spaces (Streamlit, CPU gratis)**
  para tener link, y `README` para correrlo en local como respaldo. La caché del GFS va en ambos.
- [ ] **19.** ¿Video: quién y cuándo? → **Propuesta:** guion el **4 dic**, grabación el **5 dic**, edición y subida el
  **6 dic**. Estructura de 5 min: problema (30 s) → agricultor y decisión (45 s) → **demo en vivo (2.5 min)** → modelo y
  score (45 s) → cierre (30 s).
- [ ] **20.** ¿Fecha interna? → **Propuesta: dom 6 dic** todo listo, con prueba de "clonar el repo en limpio y correrlo solo
  con el README". Hitos: **30 nov** 1.ª submission + esqueleto de la app · **3 dic** mejor modelo · **4 dic** modelo
  congelado y pesos en la app · **6 dic** video y entrega lista · **8 dic** enviar el formulario (no esperar a las 23:59).

## 2. Para los organizadores (grupo de participantes)

- [x] **21.** ¿Dónde está la **Guía del participante**? → Guía v1.0 (22 nov). Rúbrica: modelo 35, valor 20, uso del modelo
  15, originalidad 10, reproducibilidad 10, video 10. (25 nov)
- [ ] **22.** ¿Cómo se divide el LB **público/privado**? → **Propuesta:** preguntarlo en el grupo. Mientras tanto, asumir
  que es un corte aleatorio o temporal del test y **no fiarse del LB público** (por eso la pregunta 15).
- [ ] **23.** ¿El producto puede **post-procesar** la salida? → **Propuesta:** preguntarlo. Asumir que **sí**, porque la
  regla 7d permite agregar cualquier API o dato alrededor siempre que el núcleo sea nuestro modelo. Nuestra regla de riesgo
  (pregunta 6) es post-proceso simple y no reemplaza al modelo.
- [x] **24.** ¿El producto puede usar **otras horas o pronósticos**? → Sí: se aplica el modelo a cada hora que da
  `gfs_forecast.py` (hasta 16 días) y también a fechas pasadas. Caché obligatoria. (Guía, 25 nov)
- [ ] **25.** ¿Hace falta desplegarlo para la final? → **Propuesta:** preguntarlo; igual tenemos las dos opciones (pregunta 18).
- [ ] **26.** ¿Qué formato de video? → **Propuesta:** preguntarlo; por defecto **YouTube no listado** (no pide permisos,
  a diferencia de Drive).

## 3. Para los mentores (ir con el nombre del equipo y una duda concreta, reservar ≥ 6 h antes)

**Propuesta de prioridad** (no hace falta ir a todos): **Juan Carrasco (30)** y **Laura Rodríguez (29)** esta semana para
validar producto y demo; **Ney Flores (27)** antes de elegir las submissions (~3 dic); **Brenda Hidalgo (33)** con el guion
del video (~4 dic).

| # · Mentor | Pregunta concreta |
|---|---|
| **27.** Ney Flores (Kaggle) | ¿Cómo elegimos las 2 submissions finales sin sobreajustar al LB público? ¿Cómo presentamos las métricas? |
| **28.** José Luis Corcuera (ML) | ¿Vale la pena una U-Net frente al starter, o conviene mejorar solo el viento? ¿Cómo explicamos el modelo al jurado? |
| **29.** Laura Rodríguez (prototipo) | ¿La propuesta de valor para el agricultor es clara? ¿Qué mínimo debe tener el prototipo? |
| **30.** Juan Carrasco (del modelo al MVP) | ¿Cómo hacemos una demo en vivo convincente si en diciembre casi no hay heladas? |
| **31.** Héctor Vásquez (despliegue) | ¿Dónde desplegamos gratis una app con PyTorch (Streamlit Cloud, HF Spaces, Render)? |
| **32.** Martín Grandez (producto con IA) | ¿Tiene sentido un LLM para redactar la alerta en lenguaje simple o en quechua? |
| **33.** Brenda Hidalgo (pitch) | ¿Cómo contamos la historia del agricultor en 5 min? ¿Hace falta un modelo de negocio? |

## 4. Para usuarios reales (validan los 20 pts de "valor para el usuario")

**Propuesta:** hablar con **1 técnico de la Agencia Agraria de Huaraz** (o de una ONG) y **1 agricultor de papa** (familiar o
conocido de la zona), por llamada de 10 min, antes del **1 dic**. Grabar o anotar frases textuales para el pitch.
Hipótesis que queremos confirmar o tumbar:
- [ ] **34.** ¿Cuántas heladas tuvo el último año y cuánto perdió? → *Hipótesis:* varias al año, sobre todo may–ago; pérdidas parciales del follaje.
- [ ] **35.** ¿Cómo se entera hoy? → *Hipótesis:* experiencia y cielo despejado al atardecer; radio; casi nadie usa SENAMHI.
- [ ] **36.** ¿Qué hace cuando viene una? ¿Con cuánta anticipación? → *Hipótesis:* riega o hace humo; necesita saberlo el día antes (turno de agua).
- [ ] **37.** ¿Tiene celular, WhatsApp, señal? → *Hipótesis:* el técnico o el líder comunal sí; el agricultor mayor, a veces solo llamadas.
- [ ] **38.** ¿Confiaría? ¿Qué la haría confiable? → *Hipótesis:* que acierte las primeras veces y que venga de alguien conocido (técnico, comunidad).

## 5. Técnicas (las verificamos nosotros con la data)

- [x] **39.** ¿El GFS de Open-Meteo se parece al `X` oficial? → **Propuesta:** correr
  `get_gfs_forecast(start_date="2024-06-20")` y comparar media y RMSE por variable contra `train.npz` en esas fechas. Hacerlo
  **antes de construir la app**: si difieren mucho, hay que recalibrar la entrada.
  **Respuesta (26 nov):** son **idénticos**. Se compararon 120 horas (20–22 jun de train y 14–16 jul de test) con el archivo histórico de Open-Meteo (`get_gfs_forecast(start_date=...)`): diferencia 0 en el 100 % de los píxeles y las 4 variables, mismas horas UTC (con ±1 h la diferencia ya sería RH 4–5 %, T 0.7–1.1 K). La data oficial *es* el GFS de Open-Meteo, así que no hay que recalibrar nada. Lo único distinto en vivo: el pronóstico a 24–48 h trae su propio error de pronóstico (el archivo histórico usa las primeras horas de cada corrida). Script: `data/compara_gfs.py`.
- [x] **40.** ¿Qué tan bien predice la **Tmin de madrugada**? → **Propuesta:** en la validación temporal, medir el error de T a
  las 09–11 UTC en las 112 celdas de la zona, modelo frente a GFS interpolado. Es el número clave para el pitch.
  **Respuesta (26 nov, val 16–30 jun, 112 celdas, fuera del entrenamiento; script `data/p40.py`):** T a las 4–6 a. m.: **modelo RMSE 1.0 °C** vs GFS solo 3.5 °C y GFS con corrección por altura 3.0 °C. Tmin de cada noche y celda: **modelo 0.9 °C** (error > 2 °C en el 2 % de los casos) vs GFS solo 3.5 °C (62 %). Riesgo Tmin ≤ 2 °C por celda: con umbral 2 °C el modelo detecta 42 % (19 % falsas alarmas); el GFS solo, 29 % con 87 % de falsas alarmas. **Con umbral de alerta 3 °C el modelo detecta 85 %** (48 % falsas alarmas). Por noche en toda la zona: modelo 16/16 aciertos, GFS solo 14/16. Heladas reales (≤ 0 °C) fueron solo el 1 % de celda-noches: muestra chica. **Propuesta:** subir el umbral de "riesgo moderado" de la app de 2 a 3 °C (regar de más cuesta poco; perder una helada cuesta la cosecha).
  **Actualización con el modelo v4 (26 nov, sin fuga):** Tmin por noche y celda **0.84 °C** (GFS solo 3.45 °C); 4–6 a. m. 1.01 °C. Riesgo ≤ 2 °C: umbral 2 °C detecta 51 % (27 % falsas alarmas), **umbral 3 °C detecta 91 %** (51 %). Heladas ≤ 0 °C: modelo 70 %, GFS solo 0 %. Por noche 16/16 vs 14/16. El umbral de 3 °C se mantiene.
- [x] **41.** ¿Hay heladas para mostrar? → El **test no trae `Y`** (solo GFS), así que no se pueden contar heladas WRF ahí.
  En **train**, zona papera (112 celdas de 3,500–4,000 m): Tmin por mes feb −0.2 · mar 0.2 · abr 1.1 · may −0.2 · **jun −1.5 °C**.
  Días con alguna celda < 0 °C: feb 2 · may 2 · **jun 18**. → Los casos de demo salen de **junio 2024** (verificado 25 nov).
- [x] **42.** ¿Cuánto tarda la inferencia de 24 h en CPU? → **Medido (26 nov):** cargar el ensamble de 10 modelos + predecir 1 hora = **1.6 s en CPU**; 24 h, unos segundos. Antes: un CNN chico
  sobre 17×13 debería tardar segundos. Importa para HF Spaces (solo CPU).
- [x] **43.** ¿Cómo maneja `make_windows()` los huecos? → **No los revisa:** asume horas seguidas y repite la primera hora en
  las 2 primeras ventanas. En vivo no es problema porque Open-Meteo da horas continuas; sí lo es si se pega caché vieja con
  descarga nueva. **Regla:** descartar las 2 primeras horas de cada descarga y no mezclar descargas. (Verificado en
  `app/gfs_forecast.py:126`, 25 nov)
