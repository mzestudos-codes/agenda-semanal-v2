"""Agenda Diária: leitura, validação e desenho baseados no script diario legado."""
from datetime import date, datetime
from math import ceil
from openpyxl.utils.datetime import from_excel
from PIL import Image, ImageDraw, ImageFont
from .validation import AgendaError,CATEGORIES,PRIORITY,clean_name,marker_type,normalized,parse_time,arena_flag
from .render import ICONS,TITLES,paste_icon,draw_subtitles,paste_arena

WEEKDAYS=('Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sábado','Domingo')
DAY_INDEX={'segunda':0,'segunda-feira':0,'terça':1,'terça-feira':1,'terca':1,'terca-feira':1,'quarta':2,'quarta-feira':2,'quinta':3,'quinta-feira':3,'sexta':4,'sexta-feira':4,'sábado':5,'sabado':5,'domingo':6}

def read_daily_date(ws):
    v=ws['J2'].value
    if isinstance(v,datetime):d=v.date()
    elif isinstance(v,date):d=v
    elif isinstance(v,(float,int)) and not isinstance(v,bool):
        value=from_excel(v);d=value.date() if isinstance(value,datetime) else value
    elif isinstance(v,str):
        d=None
        for fmt in ('%d/%m/%Y','%Y-%m-%d','%d-%m-%Y'):
            try:d=datetime.strptime(v.strip(),fmt).date();break
            except ValueError:pass
    else:d=None
    if d is None:raise AgendaError('Diária!J2: data inválida. Abra e salve a planilha no Excel.')
    weekday=ws['J3'].value
    if not isinstance(weekday,str) or not weekday.strip():
        raise AgendaError('Diária!J3: dia da semana não calculado. Abra, recalcule e salve o Excel.')
    if DAY_INDEX.get(weekday.strip().casefold()) != d.weekday():
        raise AgendaError(f'Diária!J3: dia da semana incompatível com {d:%d/%m/%Y}.')
    return d

def validate_daily(ws,logger):
    groups={c:[] for c in CATEGORIES}
    specs=(('divulgacoes','A',('K',),('periodo',)),('conferencias','C',('L','M'),('horario_pt','horario_en')),('investor_day','F',('N','O'),('modalidade','horario')))
    for row in range(3,ws.max_row+1):
        for category,company_col,cols,fields in specs:
            company=clean_name(ws[f'{company_col}{row}'].value)
            if not company:continue
            if marker_type(company):raise AgendaError(f'Diária, linha {row}: marcador Veja Mais não é permitido.')
            details={key:normalized(ws[f'{col}{row}'].value) for key,col in zip(fields,cols)}
            event={'empresa':company,**details,'linha_excel':row,'marcador':False}
            if category=='investor_day':
                event['mz_arena']=arena_flag(ws[f'I{row}'].value,f'Diária, I{row}')
            if category=='divulgacoes':
                p=details['periodo']
                if not isinstance(p,str) or p.strip().casefold() not in PRIORITY:
                    raise AgendaError(f'Diária, K{row}: período inválido para {company}: {p!r}.')
                event['_order']=(PRIORITY[p.strip().casefold()],company.casefold())
            else:
                try:
                    values=([parse_time(details['horario_pt']),parse_time(details['horario_en'])] if category=='conferencias' else [parse_time(details['horario'])])
                except AgendaError as exc:raise AgendaError(f'Diária, linha {row}, {company}: {exc}') from exc
                t=min((v for v in values if v is not None),default=None)
                event['_order']=(t is None,t if t is not None else float('inf'),company.casefold())
            groups[category].append(event)
    for cat,events in groups.items():
        seen={}
        for event in events:
            key=event['empresa'].casefold()
            if key in seen:raise AgendaError(f'Diária: empresa duplicada em {cat}: {event["empresa"]} (linhas {seen[key]} e {event["linha_excel"]}).')
            seen[key]=event['linha_excel']
        events.sort(key=lambda e:e['_order'])
        for index,event in enumerate(events,1):event['posicao_ordenada']=index;event.pop('_order')
        logger.info('Diária: %s %d eventos',cat,len(events))
    if not any(groups.values()):raise AgendaError('A aba Diária não possui eventos. Nenhuma imagem será alterada.')
    return groups

def render_daily(groups,day,assets):
    present=[c for c in CATEGORIES if groups[c]]
    sections=[];head_y=30
    for cat in present:
        rows=ceil(len(groups[cat])/5)
        icon_y=head_y+(120 if cat=='divulgacoes' else 130)
        sections.append((cat,head_y,icon_y,rows))
        head_y=icon_y+(rows-1)*150+290
    _,_,last_y,last_rows=sections[-1]
    height=max(345,last_y+(last_rows-1)*150+195)
    image=Image.new('RGBA',(975,height),(0,0,0,0))
    draw=ImageDraw.Draw(image)
    draw.rounded_rectangle((0,0,974,height-1),radius=8,fill=(243,244,245,255),outline=(236,236,236,255),width=1)
    heading=ImageFont.truetype(str(assets['Fonte/Lato-SemiBold.ttf']),32)
    body=ImageFont.truetype(str(assets['Fonte/Lato-Bold.ttf']),20)
    for cat,head_y,icon_y,rows in sections:
        paste_icon(image,assets['Icones/MZ/'+ICONS[cat]],(47,head_y),(40,40))
        draw.text((102,head_y),TITLES[cat],font=heading,fill='#000000')
        y_line=head_y+(80 if cat=='divulgacoes' else 70)
        draw.line([(47,y_line),(928,y_line)],fill='#E1E1E1',width=2)
        for index,event in enumerate(groups[cat]):
            x=47+(index%5)*190;y=icon_y+(index//5)*150+(7 if cat=='divulgacoes' else 0)
            size=paste_icon(image,assets['Icones/'+event['empresa']+'.png'],(x,y))
            if cat=='divulgacoes':details=(event['periodo'],'','')
            elif cat=='conferencias':
                pt,en=event['horario_pt'],event['horario_en']
                details=('','Por: '+str(pt) if pt is not None else '','Ing. '+str(en) if en is not None else '')
            else:details=('',event['modalidade'],event['horario'])
            draw_subtitles(draw,details,x,y,size,body)
            if cat=='investor_day' and event.get('mz_arena'):
                paste_arena(image,assets,x,y,size,body)
    paste_icon(image,assets['Icones/MZ/icon-calendar@3x.png'],(652,30),(40,40))
    draw.text((700,30),f'{day.day:02d}',font=heading,fill='#33a0ff')
    draw.text((745,30),WEEKDAYS[day.weekday()],font=heading,fill='#33a0ff')
    return image
