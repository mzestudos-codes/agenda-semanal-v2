"""Validação e ordenação: evolução do MVP main,py aprovado."""
from __future__ import annotations
from datetime import datetime, time, timedelta, date
import re

DAYS = [('segunda',4,8,'P4'),('terca',12,16,'AB4'),('quarta',20,24,'AN4'),('quinta',28,32,'AZ4'),('sexta',36,40,'BL4')]
CATEGORIES = ('divulgacoes','conferencias','investor_day')
MARKERS = {'divulgacoes':'VejaMaisDivulgacoes','conferencias':'VejaMaisConferencias','investor_day':'VejaMaisInvestorDay'}
PRIORITY = {'antes abert.':0,'após fech.':1,'-':2}
NON_TIMES = {'trad. simul.','sem informação','-'}

class AgendaError(Exception):
    pass

def clean_name(value):
    return str(value).strip() if value is not None else ''

def marker_type(value):
    name=clean_name(value).casefold()
    for category, marker in MARKERS.items():
        if name == marker.casefold():return category
    # Legado do script original: 'Veja+' como marcador contextual
    if name == 'veja+': return '*'
    return None

def empty(v):return v is None or isinstance(v,str) and not v.strip()

def normalized(v):
    if isinstance(v,(time,datetime)):return v.strftime('%H:%M:%S' if v.second else '%H:%M')
    if isinstance(v,timedelta):return str(v)
    return v

def parse_time(value):
    if empty(value): return None
    if isinstance(value,(time,datetime)):return value.hour*3600+value.minute*60+value.second
    if isinstance(value,timedelta):return int(value.total_seconds())%86400
    if isinstance(value,(int,float)) and not isinstance(value,bool) and 0<=value<1:return round(value*86400)
    s=str(value).strip()
    if s.casefold() in NON_TIMES:return None
    for pattern in ('%H:%M','%H:%M:%S','%I:%M %p','%I:%M:%S %p','%I:%M%p','%I:%M:%S%p'):
        try:
            d=datetime.strptime(s.upper(),pattern);return d.hour*3600+d.minute*60+d.second
        except ValueError:pass
    m=re.fullmatch(r'(\d{1,2})h(\d{2})',s,re.I)
    if m and int(m[1])<24 and int(m[2])<60:return int(m[1])*3600+int(m[2])*60
    raise AgendaError(f'Horário não interpretável: {value!r}')

def validate_and_sort(ws,logger):
    result={}
    for day,first,last,anchor in DAYS:
        groups={c:[] for c in CATEGORIES}
        for row in range(first,last+1):
            for category,company_col,extra_cols in [('divulgacoes','A',('J',)),('conferencias','C',('K','L')),('investor_day','F',('M','N'))]:
                name=clean_name(ws[f'{company_col}{row}'].value)
                if not name:continue
                m=marker_type(name)
                if m and m not in ('*',category):raise AgendaError(f'{day}: marcador {name} na categoria incorreta ({category}), linha {row}.')
                fields={key:normalized(ws[f'{col}{row}'].value) for key,col in zip({'divulgacoes':('periodo',),'conferencias':('horario_pt','horario_en'),'investor_day':('modalidade','horario')}[category],extra_cols)}
                event={'empresa':MARKERS[category] if m else name,**fields,'linha_excel':row,'posicao_original':len(groups[category])+1,'marcador':bool(m)}
                if not m:
                    if category=='divulgacoes':
                        p=fields['periodo']
                        if empty(p):raise AgendaError(f'{day}: período vazio em J{row} para {name}.')
                        if not isinstance(p,str) or p.strip().casefold() not in PRIORITY:raise AgendaError(f'{day}: período inválido em J{row}: {p!r}.')
                        event['_order']=(PRIORITY[p.strip().casefold()],name.casefold())
                    elif category=='conferencias':
                        try: vals=[parse_time(x) for x in (fields['horario_pt'],fields['horario_en'])]
                        except AgendaError as exc:raise AgendaError(f'{day}, linha {row}, {name}: {exc}') from exc
                        t=min((x for x in vals if x is not None),default=None)
                        event['_order']=(t is None,t if t is not None else float('inf'),name.casefold())
                    else:
                        try:t=parse_time(fields['horario'])
                        except AgendaError as exc:raise AgendaError(f'{day}, linha {row}, {name}: {exc}') from exc
                        event['_order']=(t is None,t if t is not None else float('inf'),name.casefold())
                    event['horario_ordenacao']=None if category=='divulgacoes' or (category!='divulgacoes' and t is None) else f'{t//3600:02d}:{t//60%60:02d}'
                groups[category].append(event)
        for category,events in groups.items():
            seen={}
            for ev in events:
                if ev['marcador']:continue
                k=ev['empresa'].casefold()
                if k in seen:raise AgendaError(f'{day}: empresa duplicada em {category}: {ev["empresa"]} (linhas {seen[k]} e {ev["linha_excel"]}).')
                seen[k]=ev['linha_excel']
            markers=[e for e in events if e['marcador']]
            if len(markers)>1:raise AgendaError(f'{day}: mais de um marcador em {category}.')
            companies=sorted((e for e in events if not e['marcador']),key=lambda e:e['_order'])
            if len(companies)>5:raise AgendaError(f'{day}: mais de cinco empresas em {category}; verifique o Excel.')
            # Em cinco posições, marcador existente ocupa sempre a quinta posição.
            displayed=companies[:4]+markers if markers else companies[:5]
            if len(displayed)>5:raise AgendaError(f'{day}: quantidade de eventos inválida em {category}.')
            for idx,event in enumerate(displayed,1):
                event['posicao_ordenada']=idx
                event.pop('_order',None)
                if idx != event['posicao_original']:
                    criterio = ('período em J e nome alfabético' if category == 'divulgacoes'
                                else 'menor horário disponível e nome alfabético')
                    logger.info('%s | %s | %s | posição %s -> %s | critério: %s',
                                day, category, event['empresa'], event['posicao_original'], idx, criterio)
            groups[category]=displayed
        result[day]=groups
        logger.info('%s | divulgação=%d conferências=%d investor=%d',day,*(len(groups[c]) for c in CATEGORIES))
    if not any(any(result[d][cat] for cat in CATEGORIES) for d,*_ in DAYS):raise AgendaError('Nenhum evento encontrado na semana. O Excel não será alterado.')
    return result

MONTHS=('Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro')
WEEK_DAYS=('Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira')

def read_week_dates(ws):
    """A planilha atual usa a data de segunda em I2 e datas das demais linhas."""
    items=[]
    for idx, row in enumerate((2,9,17,25,33)):
        raw=ws[f'I{row}'].value
        if isinstance(raw,datetime):d=raw.date()
        elif isinstance(raw,date):d=raw
        elif isinstance(raw,(int,float)):
            from openpyxl.utils.datetime import from_excel
            d=from_excel(raw).date()
        elif isinstance(raw,str):
            d=None
            for fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y'):
                try:d=datetime.strptime(raw.strip(),fmt).date();break
                except ValueError:pass
            if d is None:raise AgendaError(f'Data não reconhecida em I{row}: {raw!r}.')
        else:raise AgendaError(f'Data ausente em I{row}: salve a planilha após recalcular as fórmulas no Excel.')
        if d.weekday()!=idx:raise AgendaError(f'Data inconsistente em I{row}: {d:%d/%m/%Y}, esperado {WEEK_DAYS[idx]}.')
        if items and (d-items[-1]).days!=1:raise AgendaError('As datas da semana não são consecutivas.')
        items.append(d)
    return dict(zip((x[0] for x in DAYS),items))

def name_of_day(d):return f'{d.day:02d}{MONTHS[d.month-1]}'
