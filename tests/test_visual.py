"""Compara pixel a pixel o renderer com a saída do Agenda_Semanal_Old.py.

O conjunto de referência foi gerado pelo script original sobre a planilha
fornecida, antes da ordenação. O teste mantém essa ordem exclusivamente para
isolar o desenho; a ordem real do programa é testada separadamente.
"""
import json
import logging
import unittest
from pathlib import Path

from PIL import Image, ImageChops
from openpyxl import load_workbook
from app.validation import DAYS, CATEGORIES, read_week_dates, validate_and_sort
from app.render import render_day
from app.assets import desired_paths, manifest_index

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'repo_github'
SAMPLE = ROOT / 'tests' / 'fixtures' / 'NomesSemanal.xlsx'
VISUAL = ROOT / 'tests' / 'fixtures' / 'visual'


@unittest.skipUnless(ASSETS.exists() and SAMPLE.exists() and VISUAL.exists(),
                     'Para teste visual, forneça repo_github/ e os exemplos de referência.')
class VisualRegressionTests(unittest.TestCase):
    def test_five_days_are_pixel_identical_to_legacy(self):
        logger = logging.getLogger('agenda.visual')
        book = load_workbook(SAMPLE, data_only=True, read_only=True)
        try:
            ws = book['Agenda']
            data = validate_and_sort(ws, logger)
            dates = read_week_dates(ws)
        finally:
            book.close()
        index = manifest_index(json.loads((ASSETS / 'manifest.json').read_text(encoding='utf-8')))
        needed = desired_paths(data, logger)
        resources = {key: ASSETS / index[key.casefold()][0] for key in needed}
        for day_index, (day, _, _, _) in enumerate(DAYS):
            rows = {category: sorted(data[day][category], key=lambda event: event['linha_excel'])
                    for category in CATEGORIES}
            for category in CATEGORIES:
                for position, event in enumerate(rows[category], 1):
                    event['posicao_ordenada'] = 5 if event['marcador'] else position
            actual = render_day(rows, day_index, dates[day], resources)
            with Image.open(VISUAL / f'original_{day_index}.png') as reference:
                actual_rgb = actual.convert('RGB')
                reference_rgb = reference.convert('RGB')
                self.assertEqual(actual_rgb.size, reference_rgb.size, day)
                self.assertIsNone(ImageChops.difference(actual_rgb, reference_rgb).getbbox(), day)
            actual.close()

if __name__ == '__main__':
    unittest.main()
