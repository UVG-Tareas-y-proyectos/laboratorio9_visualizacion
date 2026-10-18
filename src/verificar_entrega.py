"""Comprueba los requisitos de entrega y coherencia de los resultados exportados."""
from pathlib import Path
import json
import hashlib
import numpy as np
import pandas as pd
from PIL import Image
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]


def main():
    out=ROOT/'entrega';tb=ROOT/'results/tables'
    a=json.loads((tb/'auditoria.json').read_text(encoding='utf-8'))
    checks={}
    with Image.open(out/'Infografia_turismo_Guatemala.png') as im:
        checks['png_dimensiones']=[im.width,im.height]
        assert im.width>=1200 and im.height>=2400
    for name,expected in [('A3',(297/25.4*72,420/25.4*72)),('11x17',(792,1224))]:
        pdf=PdfReader(out/f'Infografia_turismo_Guatemala_{name}.pdf')
        assert len(pdf.pages)==1
        size=(float(pdf.pages[0].mediabox.width),float(pdf.pages[0].mediabox.height))
        assert np.allclose(size,expected,atol=.02),(name,size,expected)
        text=pdf.pages[0].extract_text()
        for token in ['222,438','449,114','18.99','ARIMA(2,1,0)','Estimación']:
            assert token in text,(name,token)
        checks[f'pdf_{name}']={'paginas':len(pdf.pages),'puntos':size}
    doc=PdfReader(ROOT/'Informe_Laboratorio9.pdf')
    checks['explicacion_paginas']=len(doc.pages)
    assert 8<=len(doc.pages)<=14
    doc_text='\n'.join(p.extract_text() for p in doc.pages)
    for token in ['156,261.29','170,915.02','10.63','Ihan','Diego']:
        assert token in doc_text,token
    cover=doc.pages[0].extract_text()
    assert 'UNIVERSIDAD DEL VALLE DE GUATEMALA' in cover
    assert 'GUATEMALA, 18 de octubre del 2026' in cover
    links=[]
    for page in doc.pages:
        for annot in page.get('/Annots',[]):
            action=annot.get_object().get('/A',{})
            if action.get('/URI'):links.append(action['/URI'])
    assert len(links)==2
    assert any(x.endswith('/laboratorio9_visualizacion') for x in links)
    assert any(x.endswith('/entrega/Infografia_turismo_Guatemala.png') for x in links)
    assert 'Enlaces del trabajo' not in doc_text and 'Material de entrega' not in doc_text
    assert 'Repositorio:' in doc.pages[1].extract_text() and 'Infografia:' in doc.pages[1].extract_text()
    last_size=(float(doc.pages[-1].mediabox.width),float(doc.pages[-1].mediabox.height))
    assert np.allclose(last_size,(297/25.4*72,420/25.4*72),atol=.02)
    assert '222,438' in doc.pages[-1].extract_text()
    assert not (ROOT/'docs').exists()
    assert not [p for p in ROOT.rglob('*.docx') if not any(x in p.relative_to(ROOT).parts for x in ['tmp','.git'])]
    checks['formato_documento']='PDF en la raíz con dos enlaces superiores e infografía en una página A3 completa.'
    f=pd.read_csv(tb/'prediccion_total_ic95.csv')
    assert len(f)==63
    assert (f.inferior95<=f.prediccion).all() and (f.prediccion<=f.superior95).all()
    assert np.isfinite(f.iloc[:,1:].to_numpy()).all()
    assert abs(a['validacion']['RMSE_recalculado']-a['validacion']['RMSE_guardado'])<.01
    models=pd.read_csv(tb/'comparacion_modelos_lab1.csv')
    assert len(models[models.Serie.eq('Total mensual')])==8
    for name,digest in a['sha256_entradas'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
    for path in sorted((ROOT/'results/figures').glob('*.png')):
        with Image.open(path) as im:im.verify()
    checks['datos_y_metricas']='Verificados'
    checks['inspeccion_visual']='Requiere revisión de las imágenes renderizadas además de estas comprobaciones automáticas.'
    (tb/'verificacion_entrega.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(checks,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
