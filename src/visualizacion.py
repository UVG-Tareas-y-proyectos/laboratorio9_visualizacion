"""Genera la infografía y las figuras desde tablas verificadas, sin valores dibujados a mano."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
VERDE, TURQ, OCRE, CREMA, INK, GRIS = '#124734','#2E9CA6','#C27C00','#FAF6EC','#2B2B2B','#666666'
OCRE_TEXTO = '#895700'
MONTHS = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
SHORT = {'Total mensual':'Total mensual','Región - América Del Centro':'América del Centro',
         'Región - América Del Norte':'América del Norte','Región - Europa':'Europa',
         'Frontera - 01 La Aurora':'La Aurora','Frontera - 07 Valle Nuevo':'Valle Nuevo',
         'Frontera - 09 San Cristóbal':'San Cristóbal'}


def style():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':CREMA,
        'axes.facecolor':CREMA,'text.color':INK,'axes.labelcolor':INK,'xtick.color':GRIS,'ytick.color':GRIS,
        'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':'#999999',
        'axes.grid':False,'pdf.fonttype':42,'axes.titleweight':'bold'})


def load():
    tb=ROOT/'results/tables'
    d=pd.read_csv(ROOT/'data/lab1/series_mensuales.csv',parse_dates=['Fecha'],index_col='Fecha')
    return (d,pd.read_csv(tb/'prediccion_total_ic95.csv',parse_dates=['Fecha'],index_col='Fecha'),
            pd.read_csv(tb/'estacionalidad_anios_completos.csv',index_col='mes').iloc[:,0],
            json.loads((tb/'auditoria.json').read_text(encoding='utf-8')),
            pd.read_csv(tb/'comparacion_modelos_lab1.csv'),pd.read_csv(tb/'resumen_series_lab1.csv'))


def events(ax,s,compact=False):
    ax.plot(s.index,s,color=VERDE,lw=1.6)
    ax.axvspan(pd.Timestamp('2020-04-01'),pd.Timestamp('2021-03-31'),color=OCRE,alpha=.16,lw=0)
    ax.set_ylim(0,490000)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v/1000:.0f} mil'))
    ax.xaxis.set_major_locator(mdates.YearLocator(2));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.set_xlim(s.index[0],pd.Timestamp('2026-12-01'))
    ax.tick_params(labelsize=8 if compact else 10)
    for date,label,y,ha in [('2009-04-01','H1N1 · abr 2009',470000,'left'),
                             ('2018-06-01','Volcán de Fuego · jun 2018',470000,'right')]:
        dt=pd.Timestamp(date)
        ax.axvline(dt,color=GRIS,ls=':',lw=.9)
        ax.text(dt+pd.Timedelta(days=35 if ha=='left' else -35),y,label,ha=ha,va='top',fontsize=7.5 if compact else 10,color=GRIS)
    ax.annotate('COVID-19\nventana de análisis',xy=(pd.Timestamp('2020-09-01'),50000),
                xytext=(pd.Timestamp('2021-05-01'),400000),arrowprops={'arrowstyle':'-','color':OCRE},
                color=OCRE_TEXTO,fontsize=8 if compact else 11)
    ax.set_ylabel('Viajeros / mes',fontsize=8 if compact else 11)


def seasonal(ax,s,compact=False):
    colors=[OCRE if i==11 else VERDE if v>=0 else TURQ for i,v in enumerate(s)]
    ax.bar(np.arange(12),s,width=.68,color=colors)
    ax.axhline(0,color=INK,lw=.8)
    ax.set_xticks(np.arange(12),MONTHS,fontsize=8 if compact else 11)
    ax.set_ylim(-26,45);ax.set_yticks([-20,0,20,40])
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v:+.0f}%' if v else '0%'))
    ax.tick_params(axis='y',labelsize=8 if compact else 10)
    for i,v in enumerate(s):
        ax.text(i,v+(1 if v>=0 else -1),f'{v:+.0f}%',ha='center',va='bottom' if v>=0 else 'top',
                fontsize=7.2 if compact else 10,fontweight='bold' if i==11 else 'normal')
    ax.spines[['top','right','left']].set_visible(False)
    if not compact:ax.set_ylabel('Diferencia respecto del promedio de su año')


def forecast(ax,s,f,compact=False,log=False):
    ax.fill_between(f.index,f.inferior95,f.superior95,color=OCRE,alpha=.18,lw=0)
    ax.plot(s.index,s,color=VERDE,lw=1.2 if compact else 1.7)
    ax.plot(f.index,f.prediccion,color=OCRE,lw=1.5 if compact else 2,ls='--')
    ax.axvline(f.index[0],color=GRIS,ls=':',lw=.9)
    ax.set_xlim(pd.Timestamp('2019-01-01') if compact else s.index[0],s.index[-1])
    if log:
        ax.set_yscale('log');ax.set_ylim(float(f.inferior95.min())*.7,max(f.superior95)*1.2)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v/1e6:g} M' if v>=1e6 else f'{v/1000:g} mil'))
    else:
        ax.set_ylim(0,650000);ax.set_yticks([0,200000,400000,600000])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v/1000:.0f} mil'))
    ax.xaxis.set_major_locator(mdates.YearLocator(2 if compact else 3));ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.tick_params(labelsize=7.5 if compact else 10)
    ax.text(.98,.94,'Estimación · intervalo 95%',transform=ax.transAxes,ha='right',va='top',fontsize=7.8 if compact else 11,color=OCRE_TEXTO,fontweight='bold')
    ax.text(.98,.77,'Observado',transform=ax.transAxes,ha='right',fontsize=7.5 if compact else 11,color=VERDE)
    ax.annotate('Predicción ARIMA(2,1,0)',xy=(f.index[-1],f.prediccion.iloc[-1]),
                xytext=(-5,10),textcoords='offset points',ha='right',
                fontsize=7.3 if compact else 10,color=OCRE_TEXTO)
    if not compact:ax.set_ylabel('Viajeros / mes')


def savefigure(fig,name):
    out=ROOT/'results/figures';out.mkdir(exist_ok=True,parents=True)
    fig.savefig(out/f'{name}.png',dpi=220,facecolor=CREMA,bbox_inches='tight')
    fig.savefig(out/f'{name}.pdf',facecolor=CREMA,bbox_inches='tight')
    plt.close(fig)


def individual(d,f,seas,a,models):
    s=d['Total mensual']
    fig,ax=plt.subplots(figsize=(11,4.7),layout='constrained');events(ax,s)
    ax.set_title('La caída de 2020 domina la historia del turismo',loc='left',fontsize=16,pad=22)
    fig.text(.02,-.03,'Eventos anotados como contexto. La inspección visual no identifica efectos causales. Enero 2009 a junio 2026.',fontsize=9,color=GRIS)
    savefigure(fig,'01_historia_eventos')
    fig,ax=plt.subplots(figsize=(11,4.5),layout='constrained');seasonal(ax,seas)
    ax.set_title('Diciembre supera en 35% el promedio de su año',loc='left',fontsize=16,pad=16)
    fig.text(.02,-.03,'Promedio de desviaciones mensuales por año. Años completos 2009–2019 y 2022–2025; se excluyen 2020, 2021 y 2026.',fontsize=9,color=GRIS)
    savefigure(fig,'02_estacionalidad')
    for log,name in [(False,'03_prediccion_ic95'),(True,'04_prediccion_intervalo_completo')]:
        fig,ax=plt.subplots(figsize=(11,4.8),layout='constrained');forecast(ax,s,f,log=log)
        ax.set_title('El modelo entrenado hasta marzo de 2021 subestima la recuperación',loc='left',fontsize=14,pad=18)
        note=f'Prueba: abril 2021–junio 2026. Límite superior final: {f.superior95.iloc[-1]/1e6:.2f} millones. '
        note+='Escala logarítmica para mostrar todo el intervalo.' if log else 'Eje limitado a 650 mil; el intervalo continúa fuera del área visible.'
        fig.text(.02,-.03,note,fontsize=9,color=GRIS)
        savefigure(fig,name)
    total=models[models.Serie.eq('Total mensual')].sort_values('RMSE')
    fig,axs=plt.subplots(1,2,figsize=(12,4.7),layout='constrained',sharey=True)
    labels=[short_model(x) for x in total.Modelo]
    for ax,metric in zip(axs,['MAE','RMSE']):
        ax.barh(np.arange(len(total)),total[metric],color=[OCRE]+[VERDE]*(len(total)-1))
        ax.set_yticks(np.arange(len(total)),labels,fontsize=9);ax.invert_yaxis() if metric=='MAE' else None
        ax.set_xlim(0,total[metric].max()*1.2)
        ax.xaxis.set_major_formatter(FuncFormatter(lambda v,_:f'{v/1000:.0f} mil'))
        for i,v in enumerate(total[metric]):ax.text(v+2000,i,f'{v:,.0f}',va='center',fontsize=8)
        ax.set_xlabel(f'{metric} · viajeros');ax.set_title('Menor error es mejor')
    fig.suptitle('Los ocho modelos del Lab 1 sobre los mismos 63 meses de prueba',fontsize=15,fontweight='bold')
    savefigure(fig,'05_comparacion_modelos_total')


def short_model(x):
    if x.startswith('SARIMA'):return 'SARIMA(2,1,2)×(1,0,1)₁₂'
    return {'Suavizamiento exponencial simple':'Exponencial simple','Holt-Winters aditivo':'Holt-Winters aditivo',
            'Seasonal naive':'Naive estacional','Prophet - respaldo aditivo':'Respaldo aditivo*'}.get(x,x)


def poster(d,f,seas,a,models,resumen):
    fig=plt.figure(figsize=(297/25.4,420/25.4),facecolor=CREMA)
    def text(x,y,s,size=10,color=INK,weight='normal',**kw):
        if color==OCRE and size<18:color=OCRE_TEXTO
        return fig.text(x,y,s,fontsize=size,color=color,fontweight=weight,va='top',**kw)
    def rule(y):fig.add_artist(Line2D([.055,.945],[y,y],transform=fig.transFigure,color='#D7D4CC',lw=.8))
    def section(y,n,title):
        text(.055,y,n,12,OCRE,'bold');text(.083,y,title,14,VERDE,'bold')
    text(.055,.973,'GUATEMALA  /  TURISMO Y MOVILIDAD  /  ENERO 2009 A JUNIO 2026',9,GRIS,'bold')
    text(.055,.948,'El turismo se recupera\npero el pronóstico quedó atrás',29,VERDE,'bold',linespacing=1.08)
    text(.055,.881,'Una caída de 89.7% durante la pandemia cambió la serie. El reto es anticipar la recuperación.',10.4)
    k=a['kpis']
    for x,num,label in [(.055,f'{k["promedio_mensual"]:,.0f}','viajeros por mes\npromedio del período'),
                        (.288,f'{k["maximo_mensual"]:,.0f}','máximo mensual\ndiciembre de 2019'),
                        (.521,f'−{100*k["caida_pandemia"]:.1f}%','promedio abr 2020–mar 2021\nfrente al promedio de 2019'),
                        (.754,f'{k["la_aurora_acumulado"]/1e6:.2f} M','viajeros por La Aurora\nacumulado del período')]:
        text(x,.853,num,25,OCRE if x==.521 else VERDE,'bold')
        text(x,.823,label,9.2,GRIS,linespacing=1.25)
    rule(.787)
    section(.777,'01','La pandemia marca el quiebre más visible')
    ax=fig.add_axes([.098,.649,.836,.101]);events(ax,d['Total mensual'],True)
    text(.055,.624,'H1N1 y la erupción se señalan como contexto; no se atribuyen efectos causales por inspección visual.',9,GRIS)
    text(.055,.609,'La banda destaca abr 2020–mar 2021, la ventana usada para medir la caída. 2026 contiene seis meses.',8.5,GRIS)
    rule(.591)
    section(.582,'02','Diciembre concentra el pico y la vía terrestre lidera')
    text(.065,.561,'Diferencia mensual respecto del promedio de su año',9.3,INK,'bold')
    ax=fig.add_axes([.092,.459,.433,.083]);seasonal(ax,seas,True)
    text(.065,.439,'Años completos sin 2020 y 2021. Diciembre: +35%; febrero: −18%.',8.3,GRIS)
    def ranking(pos,data,title):
        ax=fig.add_axes(pos)
        pairs=list(data.items())[:3]
        names=[('Estados Unidos' if 'Estados Unidos' in n else n) for n,v in pairs]
        vals=[v/1e6 for n,v in pairs]
        ax.barh(range(3),vals,color=VERDE,height=.55)
        ax.set_yticks(range(3),names,fontsize=8.3);ax.invert_yaxis()
        ax.set_xlim(0,max(vals)*1.45)
        for i,v in enumerate(vals):ax.text(v+.25,i,f'{v:.2f} M',va='center',fontsize=8.3)
        ax.set_xticks([]);ax.tick_params(length=0);ax.spines[:].set_visible(False)
        ax.set_title(title,loc='left',fontsize=9.3,pad=5)
    ranking([.683,.506,.255,.039],a['rankings']['vias'],'Vías · viajeros acumulados')
    ranking([.683,.449,.255,.039],a['rankings']['mercados'],'Mercados registrados · top 3')
    text(.594,.435,'País cambia de detalle después de 2023; Guatemala es una categoría\nde la base. No se interpreta como nacionalidad ni turismo interno.',7.9,GRIS,linespacing=1.2)
    text(.055,.411,'Seis series del equipo · comparación dentro de regiones y dentro de fronteras',9.3,INK,'bold')
    data=resumen[resumen.Serie.ne('Total mensual')].copy().reset_index(drop=True)
    cols=['Fuerza estacional','Crecimiento recuperación','Volatilidad','Caída pandemia']
    positions=[.055,.36,.54,.705,.866]
    for x,l in zip(positions,['Serie','Estacionalidad¹','Crecimiento²','Volatilidad³','Caída COVID']):text(x,.395,l,8.5,GRIS,'bold')
    for i,row in data.iterrows():
        y=.380-i*.0131
        text(.055,y,SHORT[row.Serie],8.8)
        for j,col in enumerate(cols):
            v=row[col];group=data.iloc[:3] if i<3 else data.iloc[3:]
            best=v==group[col].max()
            val=f'{v:.3f}' if j in [0,2] else f'{v:+.4f}' if j==1 else f'{100*v:.1f}%'
            text(positions[j+1],y,val,8.8,OCRE if best else INK,'bold' if best else 'normal')
    text(.055,.299,'¹ Fuerza STL en entrenamiento (0–1). ² Pendiente mensual de log(1+y), ene 2022–jun 2026; no es un porcentaje.',7.8,GRIS)
    text(.055,.287,'³ Desviación de cambios en log(1+y). Ocre: mayor valor en cada grupo. San Cristóbal lidera estacionalidad y crecimiento.',7.8,GRIS)
    rule(.272)
    section(.263,'03','El mejor modelo histórico tampoco anticipó la recuperación')
    text(.055,.244,'Total mensual · errores en viajeros · menor es mejor',9,INK,'bold')
    total=models[models.Serie.eq('Total mensual')].sort_values('RMSE').reset_index(drop=True)
    for x,l in [(.055,'Modelo'),(.378,'MAE'),(.459,'RMSE')]:text(x,.229,l,8.3,GRIS,'bold')
    for i,row in total.iterrows():
        y=.216-i*.0118
        color=OCRE if i==0 else INK
        text(.055,y,short_model(row.Modelo),8.4,color,'bold' if i==0 else 'normal')
        text(.427,y,f'{row.MAE:,.0f}',8.2,color,ha='right')
        text(.527,y,f'{row.RMSE:,.0f}',8.2,color,ha='right')
    ax=fig.add_axes([.605,.151,.334,.083]);forecast(ax,d['Total mensual'],f,True)
    text(.575,.139,f'Prueba abr 2021–jun 2026. Eje limitado a 650 mil; el intervalo\ncontinúa hasta {f.superior95.iloc[-1]/1e6:.2f} millones en jun 2026.',8.1,GRIS,linespacing=1.2)
    text(.055,.113,'* Modelo aditivo de respaldo del Lab 1, no Prophet oficial. Entrenamiento: ene 2009–mar 2021. El intervalo amplio no garantiza utilidad.',8.0,GRIS)
    rule(.100)
    section(.092,'04','Qué puede hacer INGUAT con esta evidencia')
    text(.055,.073,'1  Preparar capacidad para diciembre (+35%) y probar campañas en febrero y septiembre, los meses más bajos.',9.0)
    text(.055,.055,'2  Segmentar por región y frontera: Europa sufrió −94.1%; Valle Nuevo, −96.3%. Validar la demanda actual antes de asignar presupuesto.',9.0)
    text(.055,.037,'3  Reentrenar con datos recientes y validar por ventanas móviles; el corte en pandemia deja pronósticos persistentemente bajos.',9.0)
    text(.055,.016,'Fuente: Base de Migración 2009–jun 2026 INGUAT/IGM, facilitada en el curso. Serie: Turista + Excursionista; sin Crucerista ni Viajero.\nUso académico. Créditos: Ihan Marroquin 23108 y Diego Patzan 23525 · UVG · Data Science · Laboratorio 9.',7.2,GRIS,linespacing=1.25)
    out=ROOT/'entrega';out.mkdir(exist_ok=True)
    fig.savefig(out/'Infografia_turismo_Guatemala.png',dpi=300,facecolor=CREMA)
    fig.savefig(out/'Infografia_turismo_Guatemala_A3.pdf',facecolor=CREMA)
    fig.set_size_inches(11,17)
    fig.savefig(out/'Infografia_turismo_Guatemala_11x17.pdf',facecolor=CREMA)
    plt.close(fig)


def main():
    style()
    d,f,seas,a,models,resumen=load()
    individual(d,f,seas,a,models)
    poster(d,f,seas,a,models,resumen)
    print('Infografía PNG y PDF A3 y 11x17; cinco figuras exportadas.')


if __name__=='__main__':main()
