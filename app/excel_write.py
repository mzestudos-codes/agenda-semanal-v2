"""Gravação seletiva das imagens, preservando fórmulas e resultados em cache.

O openpyxl não calcula fórmulas e remove os resultados previamente calculados ao
salvar o arquivo. Após atualizar apenas os desenhos, recuperamos os valores em
cache das fórmulas inalteradas a partir do XLSX original (OOXML). Dessa forma
uma segunda execução não depende de abrir e recalcular o Excel entre as rodadas.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile
import os
import posixpath
import tempfile

from lxml import etree
from openpyxl import load_workbook
from openpyxl.drawing.image import Image as ExcelImage

from .validation import DAYS, AgendaError

ANCHORS = {anchor for _, _, _, anchor in DAYS}
NS = {'s': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
S = '{' + NS['s'] + '}'
PKGREL = {'p': 'http://schemas.openxmlformats.org/package/2006/relationships'}


def image_anchor(image):
    anchor = image.anchor
    if isinstance(anchor, str):
        return anchor.upper()
    try:
        from openpyxl.utils import get_column_letter
        return f'{get_column_letter(anchor._from.col + 1)}{anchor._from.row + 1}'
    except (AttributeError, ValueError, TypeError):
        return None


def sheet_xml_path(zipfile, sheet_name):
    workbook = etree.fromstring(zipfile.read('xl/workbook.xml'))
    sheets = workbook.find(S + 'sheets')
    node = next((s for s in sheets if s.get('name') == sheet_name), None)
    if node is None:
        raise AgendaError(f'A aba {sheet_name} não existe.')
    rel_id = node.get('{' + NS['r'] + '}id')
    relations = etree.fromstring(zipfile.read('xl/_rels/workbook.xml.rels'))
    relation = next((r for r in relations if r.get('Id') == rel_id), None)
    if relation is None:
        raise AgendaError('Não foi possível encontrar o XML da aba Agenda.')
    target = relation.get('Target')
    return target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl', target))


def restore_formula_cache(original, candidate):
    """Devolve caches de fórmulas não modificadas, inclusive datas e textos.

    Os caches não são recalculados. São reutilizados somente quando a fórmula
    original e a fórmula gravada continuam idênticas.
    """
    original, candidate = Path(original), Path(candidate)
    with ZipFile(original) as source, ZipFile(candidate) as current:
        src_entry = sheet_xml_path(source, 'Agenda')
        dst_entry = sheet_xml_path(current, 'Agenda')
        src = etree.fromstring(source.read(src_entry))
        dst = etree.fromstring(current.read(dst_entry))
        source_cells = {
            cell.get('r'): cell
            for cell in src.iter(S + 'c')
            if cell.find(S + 'f') is not None
        }
        restored = 0
        for cell in dst.iter(S + 'c'):
            old = source_cells.get(cell.get('r'))
            if old is None:
                continue
            old_formula = old.find(S + 'f')
            new_formula = cell.find(S + 'f')
            if new_formula is None or (old_formula.text, dict(old_formula.attrib)) != (new_formula.text, dict(new_formula.attrib)):
                continue
            old_value = old.find(S + 'v')
            if old_value is None:
                continue
            existing = cell.find(S + 'v')
            if existing is not None:
                cell.remove(existing)
            insert_at = list(cell).index(new_formula) + 1
            cell.insert(insert_at, deepcopy(old_value))
            if old.get('t'):
                cell.set('t', old.get('t'))
            else:
                cell.attrib.pop('t', None)
            restored += 1
        updated = etree.tostring(dst, xml_declaration=False, encoding='utf-8')
        # Copiar todas as partes e alterar somente a planilha afetada.
        with tempfile.NamedTemporaryFile(dir=candidate.parent, suffix='.xlsx', delete=False) as temp:
            temp_path = Path(temp.name)
        try:
            with ZipFile(temp_path, 'w') as output:
                for item in current.infolist():
                    output.writestr(item, updated if item.filename == dst_entry else current.read(item.filename))
        except BaseException:
            temp_path.unlink(missing_ok=True)
            raise
    # Os arquivos ZIP de entrada precisam estar fechados antes do replace.
    # Em Windows, substituir um XLSX ainda aberto pelo ZipFile gera WinError 5.
    try:
        os.replace(temp_path, candidate)
    finally:
        temp_path.unlink(missing_ok=True)
    return restored


def make_excel_candidate(excel_path, images, output_path, logger=None):
    book = load_workbook(excel_path)
    try:
        if 'Agenda' not in book.sheetnames:
            raise AgendaError('A aba Agenda não existe.')
        sheet = book['Agenda']
        # Âncoras usadas pelo sistema de agendas. Outros desenhos permanecem.
        sheet._images[:] = [image for image in sheet._images if image_anchor(image) not in ANCHORS]
        for anchor, path in images.items():
            sheet.add_image(ExcelImage(str(path)), anchor)
        book.save(output_path)
    finally:
        book.close()
    retained = restore_formula_cache(excel_path, output_path)
    if logger:
        logger.info('Caches de %d fórmulas preservados na planilha atualizada', retained)
