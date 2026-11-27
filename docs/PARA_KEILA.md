# Para Keila · Estado del proyecto (26 nov 2026)

Este documento resume lo avanzado por Jhonatan, explica **cada término técnico** que aparece en el proyecto, da los
números clave para el reporte y el video, y lista **qué necesitamos de ti**.

Faltan **12 días** para la entrega (**mar 8 dic, 23:59**).

> **Cómo leerlo:** las secciones 1 a 4 cuentan el proyecto de principio a fin y explican cada término la primera vez que
> aparece. La sección 8 es un **glosario** alfabético para consultar cuando haga falta. Si solo tienes 5 minutos,
> lee la sección 1, la sección 5 (números) y la sección 6 (tus tareas).

---

## 1. En una frase

Tenemos un modelo competitivo en Kaggle (**0.499**; el 1.º tiene ~0.519) y una app que funciona de punta a punta:
**"¿Riego esta tarde?"**, una alerta de heladas para agricultores de papa de Recuay–Huaraz–Carhuaz.
Lo que falta es sobre todo **tu parte**: validar el producto con la realidad, el relato y el video.

---

## 2. El reto, explicado desde cero

### 2.1 Qué pide la hackathon

El reto tiene **dos mitades** que pesan en la nota:

1. **Un modelo de IA** (se compite en Kaggle) que mejore la resolución del pronóstico del clima en la Cordillera Blanca.
2. **Un producto** que use ese modelo para ayudar a una persona real a tomar una decisión.

### 2.2 El problema de fondo: el pronóstico global es "borroso"

- **GFS** (*Global Forecast System*): es el pronóstico del clima gratuito de Estados Unidos (NOAA) para todo el planeta.
  Es lo que usan por detrás muchas apps del clima.
- **Resolución de 27 km:** el GFS divide el mundo en una cuadrícula. Cada cuadrado (**celda**) mide unos 27 × 27 km, y para
  cada celda da **un solo valor** de temperatura, humedad y viento.
- **Por qué es un problema en los Andes:** una sola celda de 27 km del Callejón de Huaylas mezcla valles a 3,000 m,
  chacras a 3,800 m y nevados a más de 5,000 m. El GFS da un promedio de todo eso, que no representa a ninguno.
  Por eso **no ve el frío real de las chacras**.

### 2.3 La solución: "downscaling" (bajar de escala)

- **Downscaling:** pasar de un pronóstico grueso (27 km) a uno fino (**3 km**), donde sí se ven los valles, las laderas y
  las alturas. Es como pasar de una foto pixelada a una nítida.
- **WRF** (*Weather Research and Forecasting*): un modelo físico del clima que sí calcula a 3 km, pero es muy caro de
  correr (horas de supercomputadora). La organización nos dio datos del WRF del proyecto **AIRE-ANDINO** (PUCP) como
  "respuesta correcta" para entrenar.
- **La idea de la IA:** aprender, a partir de ejemplos, cómo convertir el GFS de 27 km en lo que habría dicho el WRF a 3 km,
  pero en segundos y en una computadora normal.

### 2.4 Los datos

| Dato | Qué es |
|---|---|
| **Entrada (X)** | El GFS: una cuadrícula de **17 × 13 celdas** de 27 km, que cubre una zona grande alrededor de la cordillera |
| **Salida (Y)** | El WRF: una cuadrícula de **70 × 35 celdas** de 3 km, solo la Cordillera Blanca |
| **Variables** | **RH** = humedad relativa (%) · **T** = temperatura (en Kelvin; °C = K − 273.15) · **U** y **V** = viento hacia el este y hacia el norte (m/s) |
| **DEM** | *Digital Elevation Model*: el mapa de alturas del terreno (de 115 a 5,782 m) |
| **Entrenamiento (train)** | 18 feb – 30 jun 2024, **con** la respuesta (Y) |
| **Prueba (test)** | 2 jul – 4 ago 2024, **sin** la respuesta: es lo que se predice y Kaggle califica |

El modelo recibe **3 horas seguidas** del GFS (la hora actual y las 2 anteriores) y produce el mapa de 3 km de esa hora.

### 2.5 Cómo se califica el modelo

- **RMSE** (*error cuadrático medio*, en las mismas unidades de la variable): mide cuánto se equivoca en promedio el modelo.
  Penaliza más los errores grandes. Ejemplo: un RMSE de 1 °C significa que el error típico es de alrededor de 1 °C.
- **Climatología:** el pronóstico más simple posible, "hoy será igual al promedio histórico de esta hora". Sirve de vara
  mínima: cualquier modelo útil debe superarla.
- **Score de la competencia:** compara el error del modelo con el de la climatología, en cada variable, y los promedia.
  **0 = igual que la climatología; 1 = perfecto.** Nuestro 0.499 significa que eliminamos cerca de la mitad del error
  que tendría la climatología.
- **Leaderboard público y privado:** Kaggle divide el test en dos partes. El **público** (30 % del test) se ve en la tabla
  durante la competencia. El **privado** (70 %) se revela al final y **es el que cuenta para la nota**.
- **Submission:** cada archivo de predicciones que subimos a Kaggle. Al cierre se eligen **2 submissions finales**.

### 2.6 Cuánto pesa cada parte en la nota (rúbrica de preselección, 100 pts)

| Pts | Criterio | Quién lidera |
|---|---|---|
| 35 | Modelo: proporcional a nuestro score privado frente al mejor | Jhonatan |
| 20 | Valor para el usuario: usuario concreto y decisión real | **Keila** |
| 15 | Uso del modelo y funcionamiento de punta a punta | Ambos |
| 10 | Originalidad | **Keila** |
| 10 | Reproducibilidad (que otro pueda correrlo) | Jhonatan |
| 10 | Video pitch (máx. 5 min, "menos diapositivas, más demo") | **Keila** |

**Lectura clave:** con nuestro score, el modelo ya da ≈ **33.6 de 35**. Aunque llegáramos al 1.º, ganaríamos ~1.4 puntos.
En cambio, **55 puntos dependen del producto, el relato y el video**.

---

## 3. Cómo va el modelo

### 3.1 Conceptos para entender esta sección

- **CNN** (*red neuronal convolucional*): el tipo de red de IA que mejor trabaja con imágenes y mapas. Mira el mapa por
  ventanitas y aprende patrones, como "viento del este contra una ladera alta → más frío arriba".
- **Entrenar:** mostrarle a la red miles de ejemplos (GFS → WRF) para que ajuste sus números internos hasta equivocarse poco.
- **Pesos:** esos números internos aprendidos. Son el "cerebro" del modelo, se guardan en archivos (`models/`) y la app
  los usa. **Regla de la hackathon: la app debe usar exactamente los mismos pesos que la submission final.**
- **Época:** una pasada completa por todos los datos de entrenamiento. Entrenamos 25 épocas y guardamos la mejor.
- **Semilla:** el número que fija el azar inicial del entrenamiento. Dos entrenamientos iguales con distinta semilla dan
  modelos un poco distintos.
- **Ensamble:** promediar las predicciones de varios modelos. Los errores de uno se compensan con los de otro y el
  resultado es más estable. El nuestro promedia **25 redes** (5 configuraciones × 5 semillas).
- **Configuración:** una "receta" de red. Las nuestras tienen nombres cortos (`Gg`, `Hg`, `I`…) que indican su tamaño
  (ancho = cuántos patrones aprende a la vez; profundidad = cuántas capas) y si usan el ancla GFS.
- **Tanda:** una ronda de experimentos enviada a la GPU de Kaggle (cada una tarda de 1 a 8 horas).

### 3.2 Cómo validamos sin hacer trampa

- **Validación (val):** apartamos las **últimas dos semanas de junio (16–30 jun 2024)**. El modelo entrena sin verlas y
  luego medimos qué tan bien las predice. Es nuestro "examen de práctica".
- **Corte temporal:** separar por fechas y no al azar. Si mezcláramos días al azar, el modelo vería el día anterior y el
  siguiente de cada día de examen, y la nota saldría inflada. Con el corte temporal, el examen se parece a la situación real:
  predecir días que todavía no vio.
- **Sobreajuste al leaderboard público:** subir muchas versiones y quedarse con la que mejor sale en el público. Como el
  público es solo el 30 % del test, eso puede "aprenderse" esa parte por suerte y salir peor en el privado.
  **Nuestra regla:** decidimos con nuestra validación y solo cambiamos de modelo si mejora al menos **+0.005**.
- **Ruido entre semillas:** medimos que el mismo modelo con otras semillas puede variar **±0.003** en validación. Cualquier
  mejora menor que eso puede ser pura suerte, y no la contamos como avance.

### 3.3 Qué es el "ancla GFS" (la idea que más mejoró el modelo)

Para predecir el mapa de 3 km, la red no parte de cero: parte de un **punto de partida** y solo aprende a corregirlo.

- **Antes (ancla en la climatología):** el punto de partida era el promedio histórico de cada lugar a esa hora, calculado
  con febrero–junio. La red tenía que aprender todo lo demás.
  - El problema: el test es julio–agosto (**época seca**, más fría y seca). El promedio de febrero–junio ya no
    representaba bien esa época, y la red tenía que corregir mucho más de lo que aprendió.
- **Ahora (ancla GFS):** el punto de partida es **el promedio histórico + la "anomalía" del GFS** de ese momento,
  llevada a 3 km.
  - **Anomalía:** cuánto se aleja hoy el GFS de su propio promedio. Ejemplo: si en esa zona y a esa hora el GFS suele
    marcar 8 °C y hoy marca 5 °C, la anomalía es **−3 °C** ("hoy está 3 °C más frío de lo normal").
  - Esa anomalía se suma al promedio fino de 3 km. Así, el cambio de estación (y cualquier día raro) **entra directo** por el
    GFS, y la red solo tiene que aprender lo que el GFS no ve: **el efecto del relieve**.
- **Analogía:** antes la red tenía que adivinar el clima del día y además el efecto de la montaña. Ahora el GFS le dice
  "hoy está 3 °C más frío de lo normal" y la red solo decide cómo se reparte ese frío entre valles, laderas y cumbres.
- **Resultado:** fue el único salto grande y confirmado del proyecto: de 0.477 a **0.499** en el leaderboard.

### 3.4 Historial de versiones

| Versión | Score público | Qué cambió |
|---|---|---|
| Starter (plantilla de la organización) | 0.428 | Una CNN chica de ejemplo |
| v1 | 0.474 | Ensamble de CNN más anchas |
| v2 | 0.477 | Más configuraciones en el ensamble |
| **v4 (actual)** | **0.499** | **Ancla GFS** + configuraciones más anchas |

(v3 fue una prueba intermedia que no se subió: v4 la superó.)

### 3.5 Decisiones y lo que sigue

- **El modelo está congelado en v4.** Probamos muchas otras ideas (más semillas, otras arquitecturas, otros pesos para el
  viento) y ninguna superó el ruido. El modelo llegó a una meseta.
- **Esta noche quedó corriendo una última prueba larga** (~8 h, la "tanda 8", con 12 variantes nuevas). Mañana Jhonatan la
  revisa. Solo cambiamos de modelo si mejora claramente (+0.005).
- **Las 2 submissions finales:** (1) la mejor en validación y (2) un modelo distinto y bueno, como **seguro** por si la
  primera sale peor en el privado.

---

## 4. El producto: "¿Riego esta tarde?"

### 4.1 Usuario y decisión

- **Usuario:** pequeño agricultor de papa con chacras entre **3,500 y 4,000 m**, cerca de **Huaraz, Carhuaz o Recuay**.
- **Helada:** cuando la temperatura baja de 0 °C y el agua de las plantas se congela. En los Andes son sobre todo
  **heladas radiativas**: en noches despejadas y sin viento, el suelo y las plantas pierden calor hacia el cielo y se
  enfrían más que el aire. Son típicas de la **época seca (junio–agosto)**. En la **época de lluvias (noviembre–marzo)**
  las nubes actúan como una manta y casi no hay heladas.
- **Daño:** la hoja de la papa se quema desde unos **−1 °C**.
- **La decisión:** ¿riego esta tarde para proteger la papa de la helada de esta noche? Regar ayuda porque **el suelo húmedo
  guarda el calor del día y lo suelta de noche**. Pero hay que decidirlo **antes del turno de agua (~5 p. m.)**.
- **Humo de madrugada:** quemar material húmedo a las 4–6 a. m. crea una capa que reduce la pérdida de calor. La app lo
  sugiere si se esperan menos de −2 °C.

### 4.2 Qué ve el usuario

1. **Elige su pueblo** en la barra lateral.
2. **Recibe la respuesta en grande**, con un color según el riesgo:

   | Mínima esperada en sus chacras | Mensaje de la app |
   |---|---|
   | 0 °C o menos | 🚨 **Sí, riega esta tarde** (y humo de madrugada si baja de −2 °C) |
   | Entre 0 y 3 °C | ⚠️ **Riesgo moderado**: riega si al atardecer está despejado y sin viento |
   | Más de 3 °C | ✅ **No hace falta regar** |

   - **Umbral:** el valor de corte que cambia la decisión (aquí, 0 °C y 3 °C).
   - **Por qué el riesgo empieza en 3 °C y no en 0 °C:** el modelo da la temperatura del **aire a 2 m de altura**
     (estándar meteorológico), pero en noches despejadas la hoja queda **2–3 °C más fría** que el aire. Además, el modelo
     tiende a suavizar los extremos. Con 3 °C detecta el 91 % de los casos de riesgo real.
3. **Compara "nuestro modelo vs. GFS solo":** dos números lado a lado. El "GFS solo" es lo que mostraría cualquier app
   del clima. Si llevan a decisiones distintas, la app lo avisa. Esto demuestra que **el modelo no es decorativo**, un
   requisito explícito de la hackathon: si la app funcionara igual sin el modelo, no cumpliría.
4. **Ve la curva de la noche** (temperatura hora por hora, de 6 p. m. a 8 a. m.) y el **mapa de la Cordillera Blanca** con
   la línea de 0 °C y sus chacras marcadas.
5. **Comparte la alerta por WhatsApp** con un botón que abre WhatsApp con el mensaje ya escrito, listo para reenviar al
   grupo de la comunidad. Usa un enlace `wa.me` (función estándar de WhatsApp): no necesita cuenta ni pago.

### 4.3 Qué pasa por dentro

```
Open-Meteo (GFS de hoy, 27 km)
   → nuestro modelo (los mismos pesos de Kaggle)
   → mapas de 3 km hora por hora
   → se eligen "tus chacras" y "esta noche"
   → la mínima en la chacra más fría
   → decisión + curva + mapa + mensaje de WhatsApp
```

- **Open-Meteo:** un servicio gratuito que entrega el GFS actualizado por internet. Verificamos que da **exactamente los
  mismos datos** que la organización usó para el entrenamiento (diferencia 0 en 120 horas comparadas).
- **"Tus chacras":** las celdas de 3 km que están a **10 km o menos** del pueblo y **entre 3,500 y 4,000 m** de altura
  (Huaraz: 16 celdas; Carhuaz: 8; Recuay: 20).
- **"Esta noche":** de 6 p. m. a 8 a. m., hora de Lima. Antes del mediodía, la app mira la noche que viene.
- **Chacra más fría:** la app usa la celda más fría del grupo. Es un **criterio prudente**: preferimos avisar de más.
- **Caché (respaldo):** la app guarda la última descarga del GFS. Si Open-Meteo falla durante la demo, usa esa copia y lo
  avisa. La hackathon lo pide porque en la final no hay segunda oportunidad.
- **Modo demo (fecha pasada):** permite elegir una noche desde 2022. Sirve para mostrar heladas reales aunque ahora
  (época de lluvias) casi no haya.
- **Streamlit:** la herramienta con la que está hecha la interfaz web de la app (corre en Python, en tu navegador).

### 4.4 Cómo correrla en tu PC

Necesitas **Python 3.10 o más reciente** e internet. **No necesitas bajar la data de Kaggle**: los pesos y el relieve
ya vienen en la carpeta `models/`.

```bash
git clone <url-del-repo> && cd <carpeta>
git checkout jact                      # la rama con todo lo nuevo
pip install -r requirements.txt        # instala las librerías
streamlit run app/app_heladas.py       # abre la app
```

Se abre en <http://localhost:8501>. Explicación técnica completa en [`docs/APP.md`](APP.md).

---

## 5. Números clave para el reporte y el pitch

### 5.1 Precisión en la zona papera

Medidos con datos que el modelo **no vio** al entrenar (validación 16–30 jun 2024, 112 celdas de la zona papera):

| | **Nuestro modelo (3 km)** | GFS solo (27 km) |
|---|---|---|
| Error de la temperatura mínima de cada noche (RMSE) | **0.84 °C** | 3.45 °C |
| Casos con error mayor a 2 °C | **3 %** | 62 % |
| Celdas en riesgo real detectadas (mínima ≤ 2 °C) | **91 %** | 29 % |
| Falsas alarmas | 51 % | 87 % |
| Noches acertadas en la zona | **16 de 16** | 14 de 16 |

Qué significa cada fila:

- **Detección:** de todas las veces que realmente hubo riesgo, qué porcentaje avisó la herramienta.
- **Falsa alarma:** de todas las veces que la herramienta avisó, qué porcentaje no correspondía a un riesgo real.
- **Por qué aceptamos 51 % de falsas alarmas:** regar de más cuesta poco; una helada no avisada puede quemar la campaña.
  Aun así, el GFS solo tiene muchas más falsas alarmas (87 %) y detecta mucho menos (29 %).

**La frase para el video:** *"La app del clima se equivoca por 3.5 °C en las chacras; nosotros, por menos de 1 °C."*

### 5.2 El hallazgo más fuerte: el GFS solo se equivoca en las dos direcciones

Lo vimos al comparar el modelo con el GFS solo en todas las noches del 2 de julio al 4 de agosto de 2024:

- **En Huaraz** el GFS sale 3–4 °C **más cálido** que el modelo: **no avisaría la helada** y el agricultor podría perder
  la cosecha.
- **En Carhuaz y Recuay** el GFS sale 3–7 °C **más frío**, porque su celda de 27 km incluye los nevados: diría "riega"
  casi todas las noches de julio. Con tantas falsas alarmas, el agricultor **deja de creerle a la alerta**.

**Matiz honesto:** para julio y agosto no tenemos la respuesta del WRF (el test no la trae), así que esas noches muestran
que **el modelo y el GFS no coinciden**, no quién acertó. La prueba de que el modelo acierta más es la validación de junio
(0.84 contra 3.45 °C).

### 5.3 La noche para la demo del video: 3 de agosto de 2024 en Huaraz

- **Nuestro modelo:** −0.2 °C → "🚨 **SÍ, riega esta tarde**".
- **GFS solo:** 4.9 °C → "✅ No hace falta regar".

La app abre esa noche por defecto en el modo demo, así que en el video basta con elegir "Fecha pasada (demo)".

### 5.4 Ficha técnica (por si la piden)

| | |
|---|---|
| Modelo | Ensamble de 25 CNN con ancla GFS |
| Tamaño | 25.6 millones de parámetros · 99 MB de pesos |
| Velocidad | ~4 segundos para 24 horas de pronóstico, en una laptop sin tarjeta gráfica |
| Score Kaggle (público) | 0.49916 |

---

## 6. Lo que necesitamos de ti

### 6.1 Validación del producto (lo más importante)

- [ ] **Umbrales:** ¿0 °C para "riega" y 3 °C para "riesgo moderado" tienen sentido? Si puedes, confírmalo con un
      agricultor, un técnico de la agencia agraria o información de **SENAMHI** (servicio meteorológico del Perú) o
      **INIA** (instituto de innovación agraria).
- [ ] **Pueblos y zona:** revisa si las coordenadas de Huaraz, Carhuaz y Recuay (en `app/app_heladas.py`) están bien, y
      si "chacras entre 3,500 y 4,000 m a ≤ 10 km del pueblo" representa dónde se siembra papa de verdad.
- [ ] **Recomendaciones:** ¿el riego en la tarde y el humo de madrugada son prácticas reales en la zona? ¿Falta alguna
      (cubrir con paja o mantas, aporque)?
- [ ] **Un testimonio:** aunque sea una conversación corta con un agricultor o técnico (llamada, audio, mensaje). Suma
      mucho al criterio "Valor para el usuario" (20 pts) y al video.

### 6.2 Documentos

- [ ] **Leer y corregir [`REPORTE_PRODUCTO.md`](../REPORTE_PRODUCTO.md)**: ya está completo, con las 6 preguntas
      oficiales y números reales. Revisa sobre todo las preguntas **2, 3 y 4** (usuario, propuesta de valor y qué lo hace
      diferente), que son tu parte.
- [ ] **Revisar el [`README.md`](../README.md)** como si fueras alguien externo. El README es la portada del repositorio
      y explica qué es el proyecto y cómo correrlo. El jurado intentará correr la app siguiendo solo ese archivo.

### 6.3 Video pitch (máximo 5 min, 10 pts)

- [ ] **Guion.** Sugerencia de estructura:
  1. El problema: la helada y un GFS de 27 km que no ve las chacras.
  2. El usuario: el agricultor de papa y su decisión de las 5 p. m.
  3. **Demo en vivo de la app con la noche del 3 de agosto de 2024.**
  4. Los números: 0.8 contra 3.5 °C, y el GFS que se equivoca en las dos direcciones.
  5. El botón de WhatsApp para llegar a la comunidad.
  6. Limitaciones honestas y próximos pasos.
  7. Cierre.

  Recomendación oficial: *"menos diapositivas, más demo"*.
- [ ] **Grabar y subir con acceso público** (YouTube o Drive, sin que pida permiso). Su link va en el README y en el reporte.

---

## 7. Lo que hará Jhonatan

- Revisar mañana la prueba larga de Kaggle (tanda 8) y decidir el modelo final: v4, salvo una mejora clara.
- Hacer el **notebook reproducible** `train/submission_notebook.ipynb`. Es obligatorio y todavía falta. Un notebook es un
  documento con código que se ejecuta paso a paso; este debe entrenar el modelo desde cero y generar la submission.
- Probar que el repositorio se instala limpio siguiendo solo el README.
- **Publicar el repositorio** y unir la rama `jact` con `main` (ver glosario: rama, commit, push).
- Elegir las **2 submissions finales** en Kaggle.

---

## 8. Glosario

| Término | Definición |
|---|---|
| **AIRE-ANDINO** | Proyecto de la PUCP que generó los datos del WRF a 3 km que usa la hackathon |
| **Anomalía** | Cuánto se aleja un valor de su promedio habitual. "Hoy está 3 °C más frío de lo normal" = anomalía de −3 °C |
| **Ancla GFS** | Punto de partida del modelo: promedio histórico a 3 km + anomalía del GFS de ese momento. La red solo aprende a corregirlo por el relieve. Ver 3.3 |
| **Caché** | Copia guardada de la última descarga del pronóstico, que se usa si la fuente falla |
| **Celda** | Cada cuadrado de la cuadrícula de un mapa del clima (27 km en el GFS, 3 km en el WRF y en nuestro modelo) |
| **Climatología** | Promedio histórico de cada lugar a cada hora del día. Es el pronóstico más simple y la vara mínima del score |
| **CNN** | Red neuronal convolucional: tipo de IA especializada en imágenes y mapas |
| **Commit** | Un "guardado" con nombre de los cambios en el repositorio (como una versión) |
| **Configuración** | Una receta de red (tamaño, profundidad, si usa ancla). Las nuestras se llaman `Gg`, `Hg`, `I`, `Igr`, `Ggr` |
| **Corte temporal** | Separar los datos de práctica por fecha (no al azar), para que el examen se parezca a predecir el futuro |
| **DEM** | Modelo digital de elevación: el mapa de alturas del terreno |
| **Detección** | De los casos de riesgo real, el porcentaje que la herramienta avisó |
| **Downscaling** | Pasar un pronóstico de baja resolución (27 km) a alta resolución (3 km) |
| **Ensamble** | Promedio de varios modelos, más estable que uno solo. El nuestro: 25 redes |
| **Época (entrenamiento)** | Una pasada completa del modelo por todos los datos de entrenamiento |
| **Época seca / de lluvias** | En la sierra: seca de mayo a septiembre (con heladas), lluvias de noviembre a marzo (casi sin heladas) |
| **Falsa alarma** | De los avisos de la herramienta, el porcentaje que no correspondía a un riesgo real |
| **GFS** | *Global Forecast System*: pronóstico global gratuito de EE. UU., con celdas de ~27 km |
| **GPU** | Tarjeta gráfica: acelera mucho el entrenamiento de la IA. Usamos las GPU gratuitas de Kaggle y la de la PC de Jhonatan |
| **Helada radiativa** | Enfriamiento fuerte en noches despejadas y sin viento, cuando el suelo pierde calor hacia el cielo |
| **Kaggle** | Plataforma de competencias de IA donde se sube la submission y se califica el modelo |
| **Leaderboard público / privado** | Tabla de posiciones. El público (30 % del test) se ve durante la competencia; el privado (70 %) se revela al final y **es el que cuenta** |
| **Open-Meteo** | Servicio gratuito que entrega el GFS actualizado; la app lo usa en vivo |
| **Pesos** | Los números aprendidos por la red: su "cerebro". Están en `models/` y la app usa los mismos que la submission |
| **Push** | Subir los commits de tu PC al repositorio en internet (GitHub) para que los demás los vean |
| **Rama (branch)** | Una línea de trabajo paralela en el repositorio. Trabajamos en `jact`; al final se une a `main`, la rama principal |
| **Repositorio (repo)** | La carpeta del proyecto en GitHub, con todo el código y el historial. Debe ser público al entregar |
| **RMSE** | Error típico del modelo, en las mismas unidades que la variable (°C, %, m/s). Menos es mejor |
| **Ruido entre semillas** | Variación del resultado solo por el azar del entrenamiento (±0.003 en nuestro caso). Mejoras menores no cuentan |
| **Score** | Nota de Kaggle: 0 = igual que la climatología, 1 = perfecto. El nuestro: 0.499 |
| **Semilla** | Número que fija el azar inicial del entrenamiento |
| **Sobreajuste** | Cuando un modelo (o una decisión) se adapta demasiado a los datos que ve y falla en datos nuevos |
| **Streamlit** | Herramienta en Python con la que está hecha la interfaz web de la app |
| **Submission** | Archivo de predicciones subido a Kaggle. Al final se eligen 2 |
| **Tanda** | Una ronda de experimentos en la GPU de Kaggle |
| **Test** | Datos de julio–agosto 2024 sin respuesta; Kaggle califica nuestras predicciones sobre ellos |
| **Tmin** | Temperatura mínima de la noche: lo que decide si hay helada |
| **Umbral** | Valor de corte que cambia la decisión (0 °C y 3 °C en la app) |
| **Validación (val)** | Datos apartados (16–30 jun 2024) para medir el modelo sin que los haya visto: el "examen de práctica" |
| **`wa.me`** | Enlace oficial de WhatsApp que abre un chat con un mensaje ya escrito |
| **WRF** | Modelo físico del clima a 3 km; su salida es la "respuesta correcta" con la que se entrenó la IA |

---

## 9. Fechas

| Fecha | Qué |
|---|---|
| **lun 7 dic** | Cierre de inscripciones (ya estamos inscritos como `TEAM NEXUS`) |
| **mar 8 dic, 23:59** | **Cierre de Kaggle y del formulario con los 4 entregables:** Kaggle, repo público, producto y video. Si falta uno, quedamos fuera |
| jue 10 dic | Anuncio de los 6–8 finalistas |
| sáb 12 dic, 2–5 p. m. | Final presencial en el auditorio de FACI (PUCP): pitch nuevo y producto en vivo. Basta 1 integrante |

**Mentorías útiles para tu parte** (opcionales; reservar con ≥ 6 h de anticipación, ir con el nombre del equipo y una duda concreta):

- **Laura Rodríguez:** prototipo y propuesta de valor.
- **Juan Carrasco:** del modelo al producto mínimo y la demo.
- **Brenda Hidalgo:** pitch y modelo de negocio.

La agenda de los mentores está en el grupo de participantes.

---

Más detalle técnico: decisiones y resultados en [`docs/BITACORA.md`](BITACORA.md); preguntas resueltas en
[`docs/PREGUNTAS.md`](PREGUNTAS.md); funcionamiento de la app en [`docs/APP.md`](APP.md).
