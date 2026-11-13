"""Composição visual da agenda, conservando medidas e fontes do script original.

O renderer usa registros ordenados e recursos temporários resolvidos pelo manifesto.
Nenhuma alteração de ordenação é realizada aqui.
"""
from __future__ import annotations

from PIL import Image, ImageDraw, ImageFont

from .validation import CATEGORIES

TITLES = {
    'divulgacoes': 'Divulgações',
    'conferencias': 'Conferências',
    'investor_day': 'Investor Days',
}
ICONS = {
    'divulgacoes': 'icon-Divulgações@3x.png',
    'conferencias': 'icon-conferencias@3x.png',
    'investor_day': 'icon-investor-day@3x.png',
}
WEEKDAYS = ('Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira')


def paste_icon(base, path, position, size=None):
    with Image.open(path) as opened:
        icon = opened.copy()
    if size is not None:
        resized = icon.resize(size, Image.Resampling.LANCZOS)
        icon.close()
        icon = resized
    try:
        base.paste(icon, position, icon)
        return icon.size
    finally:
        icon.close()


def draw_subtitles(draw, details, x, y, icon_size, font):
    """Equivale a adicionar_textos() do original, sem desalinhamento de listas."""
    fills = ('#8F8F8F', '#202126', '#8F8F8F')
    for idx, subtitle in enumerate(details):
        value = '' if subtitle is None else str(subtitle)
        if not value:
            continue
        bbox = draw.textbbox((0, 0), value, font=font)
        # No código antigo era usada a coordenada x2 de textbbox.
        text_width = bbox[2]
        text_x = x + (icon_size[0] - text_width) // 2
        text_y = y + icon_size[1] + 12 + (30 if idx == 2 else 0)
        draw.text((text_x, text_y), value, font=font, fill=fills[idx])


ARENA_ASSET = 'Icones/MZ/MZArena.png'


def paste_arena(image, assets, x, y, company_icon_size, font, time_text):
    """Acrescenta selo abaixo do horário, sem mover textos ou alterar o canvas.

    Largura igual à palavra 'Presencial' na fonte atual, proporção original
    preservada, intervalo vertical igual ao intervalo modalidade/horário.
    """
    label_top = y + company_icon_size[1] + 12
    time_top = y + company_icon_size[1] + 42
    label_bbox = font.getbbox('Presencial')
    time_bbox = font.getbbox(str(time_text or ''))
    label_bottom = label_top + label_bbox[3]
    time_bottom = time_top + time_bbox[3]
    spacing = max(0, time_top - label_bottom)

    target_width = max(1, round(font.getlength('Presencial')))
    with Image.open(assets[ARENA_ASSET]) as opened:
        source_width, source_height = opened.size
        if source_width <= 0 or source_height <= 0:
            raise ValueError('O selo da MZ Arena tem dimensões inválidas.')
        target_height = max(1, round(target_width * source_height / source_width))
        logo = opened.convert('RGBA').resize(
            (target_width, target_height), Image.Resampling.LANCZOS
        )
    try:
        logo_x = x + (company_icon_size[0] - target_width) // 2
        logo_y = time_bottom + spacing + 5
        image.paste(logo, (logo_x, logo_y), logo)
    finally:
        logo.close()


def render_day(groups, day_index, day_date, assets):
    present = [cat for cat in CATEGORIES if groups[cat]]
    if not present:
        return None
    active = [int(cat in present) for cat in CATEGORIES]
    base_key = f'Fundo/Base{active[0]}Divul{active[1]}Conf{active[2]}Inv.png'
    with Image.open(assets[base_key]) as opened:
        image = opened.copy()

    draw = ImageDraw.Draw(image)
    heading_font = ImageFont.truetype(str(assets['Fonte/Lato-SemiBold.ttf']), 32)
    body_font = ImageFont.truetype(str(assets['Fonte/Lato-Bold.ttf']), 20)
    weekday_font = heading_font

    # Mesmos cabeçalhos do criar_base original: 30 / 325 / 660.
    section_heads = (30, 325, 660)
    for index, category in enumerate(present):
        head_y = section_heads[index]
        paste_icon(image, assets['Icones/MZ/' + ICONS[category]], (47, head_y), (40, 40))
        draw.text((102, head_y), TITLES[category], font=heading_font, fill='#000000')
        line_y = head_y + (80 if index == 0 else 70)
        draw.line([(47, line_y), (928, line_y)], fill='#E1E1E1', width=2)
        # Divulgações usam 150; outras categorias 130 + y do cabeçalho.
        icon_y = 150 if category == 'divulgacoes' else 130 + head_y
        for event in groups[category]:
            position = event['posicao_ordenada'] - 1
            icon_x = 47 + 190 * position
            icon_key = 'Icones/' + event['empresa'] + '.png'
            if event['marcador']:
                paste_icon(image, assets[icon_key], (icon_x - 15, icon_y))
                continue
            size = paste_icon(image, assets[icon_key], (icon_x, icon_y))
            if category == 'divulgacoes':
                subtitles = (event['periodo'], '', '')
            elif category == 'conferencias':
                pt, en = event.get('horario_pt'), event.get('horario_en')
                subtitles = ('', '' if pt is None else 'Por: ' + str(pt), '' if en is None else 'Ing. ' + str(en))
            else:
                subtitles = ('', event.get('modalidade'), event.get('horario'))
            draw_subtitles(draw, subtitles, icon_x, icon_y, size, body_font)
            if category=='investor_day' and event.get('mz_arena'):
                paste_arena(image,assets,icon_x,icon_y,size,body_font,event.get('horario'))

    paste_icon(image, assets['Icones/MZ/icon-calendar@3x.png'], (632, 30), (40, 40))
    draw.text((680, 30), f'{day_date.day:02d}', font=weekday_font, fill='#33a0ff')
    draw.text((725, 30), WEEKDAYS[day_index], font=weekday_font, fill='#33a0ff')
    return image
