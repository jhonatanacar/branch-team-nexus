"""TEAM NEXUS · ¿Riego esta tarde? Alerta de heladas para papa en el Callejón de Huaylas.

    GFS actual (Open-Meteo, 27 km) -> nuestro modelo de downscaling (3 km) -> mínima de esta noche
    en las chacras de 3,500-4,000 m cerca de tu pueblo -> decisión: regar o no esta tarde.

Uso:  streamlit run app/app_heladas.py
"""
from datetime import date, datetime, timedelta
from urllib.parse import quote

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

import ejemplo_producto as ep

# Pueblos de la zona elegida (Recuay-Huaraz-Carhuaz). Chacras de papa = celdas a 3,500-4,000 m a <= 10 km.
PUEBLOS = {"Huaraz": (-9.527, -77.528), "Carhuaz": (-9.282, -77.645), "Recuay": (-9.722, -77.456)}
RADIO_KM, ALT_MIN, ALT_MAX = 10, 3500, 4000

st.set_page_config(page_title="¿Riego esta tarde?", page_icon="🥔", layout="centered")


@st.cache_resource
def static():
    return dict(np.load(ep.RAIZ / "data" / "static.npz"))


@st.cache_data(ttl=3600, show_spinner="Descargando el GFS y corriendo nuestro modelo…")
def pronostico(dia_pasado=None):
    """-> (Y modelo, Y interpolación simple, times UTC, aviso). Y: (N,70,35,4), fila 0 = sur."""
    S = static()
    if dia_pasado:  # demo con fechas pasadas (p. ej. julio 2024, época de heladas)
        d = date.fromisoformat(dia_pasado)
        X, t = ep.get_gfs_forecast(start_date=str(d), end_date=str(d + timedelta(days=1)))
        aviso = None
    else:
        X, t, aviso = ep.descargar_gfs(48)
    Xw, t = ep.make_windows(X, t)
    return ep.predecir(Xw, S, t), ep._interpolar_a_wrf(Xw[:, -1], S["wrf_lats"], S["wrf_lons"]), np.asarray(t), aviso


def celdas_chacra(S, pueblo):
    la, lo = PUEBLOS[pueblo]
    LAT, LON = np.meshgrid(S["wrf_lats"], S["wrf_lons"], indexing="ij")
    km = np.hypot((LAT - la) * 111, (LON - lo) * 111 * np.cos(np.deg2rad(la)))
    return (km <= RADIO_KM) & (S["dem"] >= ALT_MIN) & (S["dem"] <= ALT_MAX)


def noche(t, desde_lima):
    """Índices de la primera noche (18:00-08:00 Lima) a partir de `desde_lima`."""
    lima = pd.to_datetime(t.astype(str), format="%Y%m%d%H") - pd.Timedelta(hours=5)
    es = ((lima.hour >= 18) | (lima.hour <= 8)) & (lima >= desde_lima)
    if not es.any():
        return np.array([], int), lima
    i0 = int(np.argmax(es))
    i1 = i0 + (int(np.argmin(es[i0:])) if not es[i0:].all() else len(t) - i0)
    return np.arange(i0, i1), lima


def decision(tmin):
    """Umbrales para papa: daña desde ~ -1 °C en la hoja; 0-2 °C a 2 m ya es riesgo en la chacra.
    El riesgo moderado llega a 3 °C porque el modelo suaviza los extremos: con 2 °C detecta el 51 % del riesgo real,
    con 3 °C el 91 % (modelo v4, val 16-30 jun, data/p40.py). Regar de más cuesta poco; perder una helada, la cosecha."""
    if tmin <= 0:
        return "error", "🚨 SÍ, riega esta tarde", (
            f"Se espera **{tmin:.1f} °C**. El suelo húmedo guarda el calor del día y lo suelta de noche. "
            "Riega antes de las 5 p. m." + (" Prepara **humo de madrugada** (4-6 a. m.)." if tmin <= -2 else ""))
    if tmin <= 3:
        return "warning", "⚠️ Riesgo moderado", (
            f"Se espera **{tmin:.1f} °C**. Si al atardecer el cielo está despejado y sin viento, riega.")
    return "success", "✅ No hace falta regar por helada", f"La mínima esperada es **{tmin:.1f} °C**."


# --------------------------------------------------------------------------- interfaz
st.title("🥔 ¿Riego esta tarde?")
st.caption("Alerta de heladas para papa · Recuay–Huaraz–Carhuaz · pronóstico a 3 km de TEAM NEXUS")

with st.sidebar:
    pueblo = st.selectbox("¿Cerca de qué pueblo está tu chacra?", list(PUEBLOS))
    modo = st.radio("Datos", ["Pronóstico de hoy (GFS en vivo)", "Fecha pasada (demo)"])
    dia = None
    if modo.startswith("Fecha"):
        dia = st.date_input("Noche de", date(2024, 7, 15), min_value=date(2022, 1, 1),
                            max_value=date.today() - timedelta(days=2)).isoformat()

S = static()
Y, Yi, t, aviso = pronostico(dia)
if aviso:
    st.warning(aviso)

ahora = pd.Timestamp(datetime.utcnow()) - pd.Timedelta(hours=5)
# la decisión es de la tarde: antes del mediodía se mira la noche que viene, no la que termina
desde = pd.Timestamp(dia) + pd.Timedelta(hours=12) if dia else max(ahora, ahora.normalize() + pd.Timedelta(hours=12))
idx, lima = noche(t, desde)
mask = celdas_chacra(S, pueblo)
if len(idx) == 0 or not mask.any():
    st.error("No hay horas de noche en los datos descargados.")
    st.stop()

T = Y[idx, ..., 1] - 273.15                       # (horas, 70, 35) °C
Ti = Yi[idx, ..., 1] - 273.15
tmin_hora = T[:, mask].min(1)                     # la chacra más fría a cada hora
tmin = float(tmin_hora.min())
hora = lima[idx[int(tmin_hora.argmin())]]

tipo, titulo, texto = decision(tmin)
getattr(st, tipo)(f"### {titulo}\n{texto}")
st.write(f"Noche del **{lima[idx[0]]:%a %d/%m}** · mínima a las **{hora:%H:00}** · "
         f"{mask.sum()} celdas de 3 km entre {ALT_MIN:,} y {ALT_MAX:,} m a ≤ {RADIO_KM} km de {pueblo}.")
# reenviar al grupo de la comunidad: wa.me abre WhatsApp con el texto listo, sin cuenta ni API
msg = (f"🥔 Alerta de heladas · chacras de {pueblo} (3,500–4,000 m)\nNoche del {lima[idx[0]]:%d/%m}: "
       f"{titulo.split(' ', 1)[1]}\n{texto.replace('**', '*')}\nPronóstico a 3 km de TEAM NEXUS")
st.link_button("📲 Compartir por WhatsApp", "https://wa.me/?text=" + quote(msg))

c1, c2 = st.columns(2)
c1.metric("Mínima con nuestro modelo (3 km)", f"{tmin:.1f} °C")
ti = float(Ti[:, mask].min())
c2.metric("Con el GFS sin modelo (27 km)", f"{ti:.1f} °C", f"{ti - tmin:+.1f} °C de diferencia", delta_color="off")
if (ti <= 0) != (tmin <= 0):
    st.info("👆 Aquí el GFS solo y nuestro modelo dan **decisiones distintas**: el GFS de 27 km no ve el relieve del valle.")

st.subheader("Temperatura en tus chacras durante la noche")
st.line_chart(pd.DataFrame({"Nuestro modelo (°C)": tmin_hora, "GFS sin modelo (°C)": Ti[:, mask].min(1)},
                           index=lima[idx]), height=250)

st.subheader("Mínima de la noche en la Cordillera Blanca")
fig, ax = plt.subplots(figsize=(5, 8))
lats, lons = S["wrf_lats"], S["wrf_lons"]
ext = [lons.min(), lons.max(), lats.min(), lats.max()]
im = ax.imshow(T.min(0), origin="lower", extent=ext, cmap="coolwarm", vmin=-8, vmax=15)  # fila 0 = sur
ax.contour(lons, lats, T.min(0), levels=[0], colors="navy", linewidths=1)
LAT, LON = np.meshgrid(lats, lons, indexing="ij")
ax.scatter(LON[mask], LAT[mask], s=6, c="k", marker="s", label="Tus chacras (3,500–4,000 m)")
for n, (la, lo) in PUEBLOS.items():
    ax.plot(lo, la, "k^", ms=6); ax.annotate(n, (lo, la), xytext=(4, 4), textcoords="offset points", fontsize=8)
fig.colorbar(im, ax=ax, shrink=0.6, label="°C (línea azul = 0 °C)")
ax.legend(loc="lower left", fontsize=7); ax.set_xlabel("Longitud"); ax.set_ylabel("Latitud")
st.pyplot(fig)

st.caption("Modelo: ensamble de CNN entrenado con WRF 3 km (AIRE-ANDINO, feb–jun 2024), mismos pesos que nuestra "
           "submission de Kaggle. Es una guía, no reemplaza la observación del cielo al atardecer.")
