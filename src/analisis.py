"""Reconstruye las tablas y el intervalo usados en el Laboratorio 9.

Conserva las métricas originales del Lab 1; registra aparte la validación del
pronóstico para no sustituir resultados históricos por ajustes posteriores.
"""
from pathlib import Path
import argparse
import ast
import hashlib
import json
import platform

import numpy as np
import pandas as pd
import statsmodels
from statsmodels.tsa.statespace.sarimax import SARIMAX

ROOT = Path(__file__).resolve().parents[1]


def analizar(root=ROOT):
    tables = root / 'results/tables'
    tables.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(root/'data/lab1/series_mensuales.csv', parse_dates=['Fecha'], index_col='Fecha')
    if d.index.has_duplicates or not d.index.equals(pd.date_range('2009-01-01', '2026-06-01', freq='MS', name='Fecha')):
        raise ValueError('La serie debe contener exactamente 210 meses consecutivos sin duplicados.')
    if not np.isfinite(d.to_numpy()).all() or (d < 0).any().any():
        raise ValueError('Hay valores faltantes, no finitos o negativos.')
    s = d['Total mensual']
    split = int(len(s)*0.7)
    resumen = pd.read_csv(root/'data/lab1/resumen_series.csv')
    modelos = pd.read_csv(root/'data/lab1/comparacion_modelos.csv')
    ganadores = modelos.sort_values(['RMSE', 'MAE']).groupby('Serie', sort=False).first().reindex(d.columns).rename_axis('Serie').reset_index()
    row = ganadores.loc[ganadores['Serie'].eq('Total mensual')].iloc[0]
    order = ast.literal_eval(row['Orden'])
    train, test = s.iloc[:split], s.iloc[split:]
    fit = SARIMAX(np.log1p(train.to_numpy()), order=order,
                  seasonal_order=(0,0,0,12), trend='n',
                  enforce_stationarity=False, enforce_invertibility=False).fit(disp=False, maxiter=150)
    fc = fit.get_forecast(len(test))
    pred = np.maximum(0, np.expm1(fc.predicted_mean))
    interval = np.maximum(0, np.expm1(fc.conf_int(alpha=0.05)))
    forecast = pd.DataFrame({'observado':test.to_numpy(), 'prediccion':pred,
                             'inferior95':interval[:,0], 'superior95':interval[:,1]}, index=test.index)
    forecast.to_csv(tables/'prediccion_total_ic95.csv', index_label='Fecha')
    # La curva exp(mu)-1 es la mediana condicional en la escala original.
    # Se conserva esa convención porque es la empleada en las métricas del Lab 1.
    error = test.to_numpy()-pred
    mae, rmse = float(np.abs(error).mean()), float(np.sqrt(np.mean(error**2)))
    validation = {'modelo':row['Modelo'], 'MAE_guardado':float(row['MAE']),
                  'RMSE_guardado':float(row['RMSE']), 'MAE_recalculado':mae,
                  'RMSE_recalculado':rmse, 'convergencia':bool(fit.mle_retvals.get('converged',False)),
                  'cobertura_observada':float(((test>=interval[:,0])&(test<=interval[:,1])).mean()),
                  'primer_inferior95':float(interval[0,0]), 'primer_superior95':float(interval[0,1]),
                  'ultimo_superior95':float(interval[-1,1]),
                  'nota':'Intervalo predictivo condicionado al modelo; no incluye incertidumbre por cambio estructural.'}
    if abs(rmse-float(row['RMSE'])) > 0.01:
        raise ValueError(f'El ajuste no reproduce las métricas del Lab 1: {validation}. Revisar versiones antes de exportar.')
    # Un año parcial no es comparable con el promedio de un año completo.
    counts = s.groupby(s.index.year).size()
    years = counts[counts.eq(12)].index.difference([2020,2021])
    full = s[s.index.year.isin(years)]
    ratios = 100*(full/full.groupby(full.index.year).transform('mean')-1)
    season = ratios.groupby(ratios.index.month).mean().rename('desviacion_porcentaje')
    season.index.name = 'mes'
    season.to_csv(tables/'estacionalidad_anios_completos.csv')
    # Se registra el método anterior para explicar el cambio, sin ocultarlo.
    old = s[~s.index.year.isin([2020,2021])]
    old_ratio = (100*(old/old.groupby(old.index.year).transform('mean')-1)).groupby(old.index.month).mean()
    pd.DataFrame({'avance_incluye_2026_parcial':old_ratio,'final_solo_anios_completos':season}).to_csv(tables/'auditoria_estacionalidad.csv')
    raw = pd.read_excel(root/'data/raw/Base_Migracion_2009-2026jun.xlsx')
    raw.columns = raw.columns.str.strip()
    for col in ['Tipo de Viajero','Vía','País','Frontera']:
        raw[col] = raw[col].astype('string').str.strip()
    raw['Viajero'] = pd.to_numeric(raw['Viajero'],errors='raise')
    comp = raw[raw['Tipo de Viajero'].isin(['Turista','Excursionista'])]
    raw_monthly = comp.groupby(['Año','Mes cod'])['Viajero'].sum()
    if not np.allclose(raw_monthly.to_numpy(), s.to_numpy(), rtol=1e-10, atol=1e-5):
        raise ValueError('La base de origen no coincide con la serie mensual conservada.')
    rankings = {}
    for key,label in [('Vía','vias'),('País','mercados'),('Frontera','fronteras')]:
        x = comp.groupby(key)['Viajero'].sum().sort_values(ascending=False)
        x.rename('viajeros').to_csv(tables/f'{label}.csv')
        rankings[label] = {str(k):float(v) for k,v in x.items()}
    kpis = {'promedio_mensual':float(s.mean()),'maximo_mensual':float(s.max()),
            'mes_maximo':str(s.idxmax().date()), 'total_acumulado':float(s.sum()),
            'caida_pandemia':float(1-s.loc['2020-04':'2021-03'].mean()/s.loc['2019'].mean()),
            'la_aurora_acumulado':float(d['Frontera - 01 La Aurora'].sum()),
            'observaciones':len(s),'entrenamiento':split,'prueba':len(test),
            'anios_estacionalidad':[int(y) for y in years]}
    resumen.to_csv(tables/'resumen_series_lab1.csv',index=False)
    modelos.to_csv(tables/'comparacion_modelos_lab1.csv',index=False)
    ganadores.to_csv(tables/'ganadores_lab1.csv',index=False)
    hashes = {str(p.relative_to(root)).replace('\\','/'):hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted((root/'data').rglob('*')) if p.is_file()}
    result = {'kpis':kpis,'validacion':validation,'rankings':rankings,
              'versiones':{'python':platform.python_version(),'numpy':np.__version__,
                          'pandas':pd.__version__,'statsmodels':statsmodels.__version__},
              'sha256_entradas':hashes}
    (tables/'auditoria.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'kpis':kpis,'validacion':validation},ensure_ascii=False,indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    analizar(parser.parse_args().root)
