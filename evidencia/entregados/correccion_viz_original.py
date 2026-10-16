"""Lab 9 - graficos de correccion: IC 95% ARIMA MA, estacionalidad (% vs promedio), eventos.
Uso: python correccion_viz.py series_mensuales.csv carpeta_salida"""
import sys, warnings, numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings("ignore")
CSV, OUT = sys.argv[1], sys.argv[2]
VERDE, TURQ, OCRE, CREMA, INK, GRIS = "#124734", "#2E9CA6", "#C27C00", "#FAF6EC", "#2B2B2B", "#6B6B6B"
plt.rcParams.update({"font.family":"DejaVu Sans","axes.spines.top":False,"axes.spines.right":False,
    "axes.edgecolor":"#888","axes.grid":False,"font.size":11,"figure.facecolor":CREMA,"axes.facecolor":CREMA,
    "text.color":INK,"axes.labelcolor":INK,"xtick.color":INK,"ytick.color":INK})
k = lambda v,_: f"{v/1000:,.0f} mil"
d = pd.read_csv(CSV, encoding="utf-8-sig", parse_dates=["Fecha"], index_col="Fecha")
t = d["Total mensual"]; split = int(len(t)*0.7); tr, te = t.iloc[:split], t.iloc[split:]

# 1. Prediccion + IC 95% (mismo modelo del Lab 1)
fit = SARIMAX(np.log1p(tr.values), order=(0,1,1), trend="n",
              enforce_stationarity=False, enforce_invertibility=False).fit(disp=False, maxiter=150)
fc = fit.get_forecast(len(te)); pred = np.maximum(0, np.expm1(fc.predicted_mean))
ci = np.expm1(fc.conf_int(alpha=0.05)); lo = np.maximum(0, ci[:,0]); hi = ci[:,1]
print(f"RMSE={np.sqrt(((te.values-pred)**2).mean()):,.2f} MAE={np.abs(te.values-pred).mean():,.2f}")
fig, ax = plt.subplots(figsize=(11,5.4), dpi=200)
ax.fill_between(te.index, lo, hi, color=OCRE, alpha=.16, lw=0)
ax.plot(t.index, t, color=VERDE, lw=1.8)
ax.plot(te.index, pred, color=OCRE, lw=2.4, ls="--")
ax.axvline(te.index[0], color=GRIS, lw=1, ls=":")
ax.set_ylim(0, 650000); ax.set_xlim(t.index[0], te.index[-1]+pd.Timedelta(days=520))
ax.text(te.index[0], 635000, "inicio de prueba ", color=GRIS, va="top", ha="right", fontsize=9)
ax.text(t.index[40], 330000, "Observado", color=VERDE, fontweight="bold")
ax.text(te.index[-1], pred[-1], " Predicción\n ARIMA MA", color=OCRE, fontweight="bold", va="center", fontsize=10)
ax.text(te.index[len(te)//2], 535000, "Estimación (IC 95%)", color=OCRE, ha="center", fontweight="bold")
ax.text(te.index[len(te)//2], 485000, "El modelo no capturó la recuperación,\npor eso la banda es tan ancha", color=INK, ha="center", fontsize=9.5, va="top")
ax.text(te.index[-1], 640000, f"La banda sigue abriéndose fuera del gráfico\n(límite superior jun 2026: {hi[-1]/1e6:,.1f} millones)", color=GRIS, ha="right", va="top", fontsize=8.5)
ax.yaxis.set_major_formatter(k); ax.set_ylabel("Viajeros por mes")
ax.set_title("Predicción del total mensual en el período de prueba (abr 2021 – jun 2026)", loc="left", fontweight="bold")
fig.tight_layout(); fig.savefig(f"{OUT}/fig_prediccion_ic95.png", facecolor=CREMA); plt.close(fig)
pd.DataFrame({"pred":pred,"inf95":lo,"sup95":hi,"real":te.values},index=te.index).round(0).to_csv(f"{OUT}/prediccion_ic95.csv")

# 2. Estacionalidad: diferencia % contra el promedio del anio (sin 2020-2021), barras desde 0
x = t[~t.index.year.isin([2020,2021])]
peso = (x / x.groupby(x.index.year).transform("mean")).groupby(x.index.month).mean()
dif = (peso-1)*100; print(dif.round(1).to_string())
meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
fig, ax = plt.subplots(figsize=(11,4.8), dpi=200)
cols = [OCRE if v>20 else (VERDE if v>0 else TURQ) for v in dif.values]
ax.bar(meses, dif.values, color=cols, width=.68); ax.axhline(0, color=INK, lw=1)
for i,v in enumerate(dif.values):
    ax.text(i, v+(1.5 if v>=0 else -1.5), f"{v:+.0f}%", ha="center", va="bottom" if v>=0 else "top", fontsize=10, fontweight="bold" if abs(v)>=5 else "normal")
ax.text(11, dif.values[11]+10, "Aguinaldo y fiestas\nde fin de año", ha="center", color=OCRE, fontweight="bold", fontsize=9.5)
ax.set_ylim(-26, 52); ax.set_ylabel("Diferencia contra el promedio del año")
ax.yaxis.set_major_formatter(lambda v,_: f"{v:+.0f}%" if v else "0%")
ax.set_title("Estacionalidad: cuánto se aparta cada mes del promedio de su año (sin 2020 y 2021)", loc="left", fontweight="bold", fontsize=11.5)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_estacionalidad.png", facecolor=CREMA); plt.close(fig)

# 3. Serie con eventos
fig, ax = plt.subplots(figsize=(11,5), dpi=200)
ax.plot(t.index, t, color=VERDE, lw=1.8)
a,b = pd.Timestamp("2020-04-01"), pd.Timestamp("2021-03-31")
ax.axvspan(a, b, color=OCRE, alpha=.18, lw=0)
ax.text(a+(b-a)/2, 300000, "Pandemia (abr 2020 – mar 2021)", color=OCRE, rotation=90, ha="center", va="center", fontweight="bold", fontsize=10)
for nom,f in [("Influenza A H1N1 (abr 2009)\nsin cambio visible","2009-04-01"),("Erupción Volcán de Fuego (jun 2018)\nsin cambio visible","2018-06-01")]:
    ax.axvline(pd.Timestamp(f), color=GRIS, lw=1, ls="--"); ax.text(pd.Timestamp(f)+pd.Timedelta(days=(60 if "2009" in f else -60)), 40000, nom, fontsize=9, color=INK, ha=("left" if "2009" in f else "right"))
ax.set_ylim(0,None); ax.yaxis.set_major_formatter(k); ax.set_ylabel("Viajeros por mes")
ax.set_title("Solo la pandemia rompió la serie: H1N1 y el Volcán de Fuego no dejaron huella visible", loc="left", fontweight="bold", fontsize=11.5)
fig.tight_layout(); fig.savefig(f"{OUT}/fig_serie_eventos.png", facecolor=CREMA); plt.close(fig)
