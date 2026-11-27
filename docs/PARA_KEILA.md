# Para Keila · Estado del proyecto (26 nov 2026)

Resumen de lo avanzado por Jhonatan, qué necesitamos de ti y los números clave para el reporte y el video.
Faltan **12 días** para la entrega (**mar 8 dic, 23:59**).

---

## 1. En una frase

Tenemos un modelo competitivo en Kaggle (**0.499**, cerca del 1.º con ~0.519) y una app que funciona de punta a punta:
**"¿Riego esta tarde?"**, una alerta de heladas para agricultores de papa de Recuay–Huaraz–Carhuaz.
Lo que falta es sobre todo **tu parte**: validar el producto, el video y el relato.

## 2. Cómo va el modelo (Kaggle)

| Versión | Score público | Qué cambió |
|---|---|---|
| Starter (plantilla) | 0.428 | — |
| v1 | 0.474 | Ensamble de CNN más anchas |
| v2 | 0.477 | Más configuraciones en el ensamble |
| **v4 (actual)** | **0.499** | **"Ancla GFS"**: el modelo parte del GFS y solo corrige el efecto del relieve |

- En puntos de la rúbrica, el modelo ya da **≈ 33.6 de 35**. Llegar al 1.º sumaría solo ~1.4 puntos.
- Por eso **el modelo está congelado** y el tiempo va al producto, que vale 65 puntos.
- Esta noche quedó corriendo una última prueba larga. Mañana Jhonatan la revisa; solo cambiamos de modelo si mejora claramente.
- **Ojo:** el score que cuenta es el **privado**, el 70 % del test que no vemos. Por eso decidimos con nuestra validación y
  no persiguiendo el leaderboard público.

## 3. El producto: "¿Riego esta tarde?"

- **Usuario:** pequeño agricultor de papa con chacras entre 3,500 y 4,000 m, cerca de Huaraz, Carhuaz o Recuay.
- **Decisión:** ¿riego esta tarde, antes del turno de agua de las 5 p. m., para proteger la papa de la helada de esta noche?
  El suelo húmedo guarda el calor del día y lo suelta de noche.
- **Qué hace la app:**
  1. Eliges tu pueblo.
  2. Recibes la respuesta en grande:

     | Mínima esperada en tus chacras | Mensaje de la app |
     |---|---|
     | 0 °C o menos | 🚨 **Sí, riega esta tarde**, y humo de madrugada si baja de −2 °C |
     | Entre 0 y 3 °C | ⚠️ **Riesgo moderado** |
     | Más de 3 °C | ✅ **No hace falta regar** |

  3. Ves la comparación con el GFS solo (lo que usa cualquier app del clima).
  4. Ves la curva de la noche y el mapa de la Cordillera Blanca.
  5. Con un botón, **compartes la alerta por WhatsApp** al grupo de la comunidad.
- **Robusta:** si la fuente del pronóstico (Open-Meteo) falla, usa la última descarga guardada y lo avisa.
- **Modo demo:** se puede elegir una noche pasada. Así mostramos heladas aunque ahora (época de lluvias) casi no haya.

### Cómo correrla en tu PC

```bash
git clone <repo> && cd <carpeta>      # rama jact
pip install -r requirements.txt
streamlit run app/app_heladas.py
```

Se abre en <http://localhost:8501>. No necesitas bajar la data de Kaggle. Explicación completa en [`docs/APP.md`](APP.md).

## 4. Números clave para el reporte y el pitch

Medidos con datos que el modelo **no vio** al entrenar (16–30 jun 2024, 112 celdas de la zona papera):

| | **Nuestro modelo (3 km)** | GFS solo (27 km) |
|---|---|---|
| Error de la temperatura mínima de cada noche | **0.84 °C** | 3.45 °C |
| Casos con error mayor a 2 °C | **3 %** | 62 % |
| Celdas en riesgo real detectadas | **91 %** | 29 % (y 87 % de falsas alarmas) |
| Noches acertadas en la zona | **16 de 16** | 14 de 16 |

**La frase para el video:** *"La app del clima se equivoca por 3.5 °C en las chacras; nosotros, por menos de 1 °C."*

**El hallazgo más fuerte: el GFS solo se equivoca en las dos direcciones.** Lo vimos en todas las noches de julio y agosto de 2024:

- En **Huaraz** sale 3–4 °C **más cálido**: no avisa la helada y el agricultor pierde la cosecha.
- En **Carhuaz y Recuay** sale 3–7 °C **más frío**, porque su celda de 27 km incluye los nevados: diría "riega" casi
  todas las noches. Con tantas falsas alarmas, el agricultor deja de creerle.

**Noche para la demo del video: 3 de agosto de 2024 en Huaraz.** Nuestro modelo dice −0.2 °C, "**SÍ, riega**". El GFS
solo dice 4.9 °C, "no hace falta". La app abre esa noche por defecto en el modo demo.

## 5. Lo que necesitamos de ti

**Validación del producto (lo más importante):**
- [ ] **Umbrales:** ¿0 °C para "riega" y 3 °C para "riesgo moderado" tienen sentido? Si puedes, confírmalo con un
      agricultor, un técnico de la agencia agraria o información de SENAMHI o INIA. Usamos 3 °C porque el modelo da la
      temperatura del aire a 2 m, y la hoja queda 2–3 °C más fría en noches despejadas.
- [ ] **Pueblos y zona:** revisa las coordenadas de Huaraz, Carhuaz y Recuay (en `app/app_heladas.py`). Revisa también si
      "chacras entre 3,500 y 4,000 m a ≤ 10 km del pueblo" representa bien dónde se siembra papa.
- [ ] **Recomendaciones:** ¿riego en la tarde y humo de madrugada son prácticas reales de la zona? ¿Falta alguna, como
      cubrir con paja o mantas?
- [ ] **Un testimonio:** aunque sea una conversación corta con un agricultor o técnico, suma mucho al video y al
      criterio "Valor para el usuario" (20 pts).

**Documentos:**
- [ ] **Leer y corregir [`REPORTE_PRODUCTO.md`](../REPORTE_PRODUCTO.md)**: ya está completo, con las 6 preguntas y números
      reales. Revisa sobre todo las preguntas 2, 3 y 4 (usuario, valor y diferencia), que son tu parte.
- [ ] Revisar el [`README.md`](../README.md) desde los ojos de alguien externo.

**Video pitch (máximo 5 min, 10 pts):**
- [ ] Guion. Sugerencia: problema (helada + GFS de 27 km) → usuario → **demo en vivo de la app con la noche del 3 de agosto**
      → números (0.8 vs 3.5 °C) → botón de WhatsApp → limitaciones → cierre. *"Menos diapositivas, más demo."*
- [ ] Grabar y subir con acceso público (sin pedir permiso). Su link va en el README y en el reporte.

## 6. Lo que hará Jhonatan

- Revisar mañana la prueba larga de Kaggle y decidir el modelo final (v4 salvo una mejora clara).
- El notebook reproducible `train/submission_notebook.ipynb`. Es obligatorio y todavía falta.
- Probar que el repo se instala limpio solo con el README.
- Hacer público el repo y fusionar la rama `jact` en `main`.
- Elegir las **2 submissions finales** en Kaggle: la mejor en validación y un modelo distinto como seguro.

## 7. Fechas

| Fecha | Qué |
|---|---|
| **lun 7 dic** | Cierre de inscripciones (ya estamos inscritos como `TEAM NEXUS`) |
| **mar 8 dic, 23:59** | **Cierre de Kaggle y del formulario con los 4 entregables:** Kaggle, repo público, producto y video. Si falta uno, quedamos fuera |
| jue 10 dic | Anuncio de los 6–8 finalistas |
| sáb 12 dic, 2–5 p. m. | Final presencial en FACI (PUCP): pitch nuevo y producto en vivo. Basta 1 integrante |

**Mentorías útiles para tu parte** (reservar con ≥ 6 h de anticipación, con una duda concreta):
- Laura Rodríguez: prototipo y propuesta de valor.
- Juan Carrasco: del modelo al MVP y la demo.
- Brenda Hidalgo: pitch.

---

Más detalle: decisiones y resultados en [`docs/BITACORA.md`](BITACORA.md); preguntas resueltas en [`docs/PREGUNTAS.md`](PREGUNTAS.md).
