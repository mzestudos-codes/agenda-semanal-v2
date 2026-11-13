import json
import logging
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

from PIL import Image
from openpyxl import Workbook, load_workbook
from openpyxl.drawing.image import Image as EmbeddedImage

from app.assets import obtain_assets
from app.engine import run
from app.excel_write import image_anchor
from app.validation import AgendaError, DAYS

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / 'repo_github'


@unittest.skipUnless((ASSETS / 'manifest.json').is_file(), 'Para integração local, extraia também os assets em repo_github/')
class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.parent = Path(self.tmp.name)
        self.excel = self.parent / 'NomesSemanal.xlsx'
        book = Workbook()
        sheet = book.active
        sheet.title = 'Agenda'
        for i, row in enumerate((2, 9, 17, 25, 33)):
            from datetime import datetime, timedelta
            sheet[f'I{row}'] = datetime(2025, 11, 17) + timedelta(days=i)
        # Um único dia com evento, demais vazios.
        sheet['A4'], sheet['J4'] = 'Ânima', '-'
        self.extra = self.parent / 'extra.png'
        Image.new('RGBA', (18, 18), (24, 50, 80, 255)).save(self.extra)
        sheet.add_image(EmbeddedImage(str(self.extra)), 'AB4')  # imagem antiga de terça
        sheet.add_image(EmbeddedImage(str(self.extra)), 'C42')  # desenho não pertencente à agenda
        book.save(self.excel)
        book.close()

    def test_days_without_events_and_unrelated_images(self):
        folder = run(self.excel, local_assets=ASSETS, open_results=False)
        self.assertEqual([p.name for p in folder.glob('Agenda_*.png')], ['Agenda_17Novembro.png'])
        # A pasta pode conter imagem antiga de um dia agora vazio: não pode sobreviver.
        stale = folder / 'Agenda_18Novembro.png'
        stale.write_bytes((folder / 'Agenda_17Novembro.png').read_bytes())
        self.assertTrue((self.parent / 'Logs').is_dir())
        after = load_workbook(self.excel)
        try:
            anchors = sorted(image_anchor(img) for img in after['Agenda']._images)
            self.assertEqual(anchors, ['C42', 'P4'])
        finally:
            after.close()
        # A segunda execução substitui a imagem sem duplicá-la.
        run(self.excel, local_assets=ASSETS, open_results=False)
        self.assertFalse(stale.exists(), 'PNG antigo de dia vazio não foi excluído')
        after = load_workbook(self.excel)
        try:
            self.assertEqual(sorted(image_anchor(img) for img in after['Agenda']._images), ['C42', 'P4'])
        finally:
            after.close()

    def test_missing_icon_blocks_without_modifying_excel(self):
        import hashlib
        before = hashlib.sha256(self.excel.read_bytes()).hexdigest()
        book = load_workbook(self.excel)
        book['Agenda']['A4'] = 'Empresa Inexistente'
        book.save(self.excel)
        book.close()
        before = hashlib.sha256(self.excel.read_bytes()).hexdigest()
        with self.assertRaisesRegex(AgendaError, 'Empresa Inexistente'):
            run(self.excel, local_assets=ASSETS, open_results=False)
        self.assertEqual(before, hashlib.sha256(self.excel.read_bytes()).hexdigest())

    def test_incorrect_hash_is_rejected(self):
        import os
        from app.assets import obtain_assets
        from app.validation import validate_and_sort
        book = load_workbook(self.excel, data_only=True)
        try:
            data = validate_and_sort(book['Agenda'], logging.getLogger('test.hash'))
        finally:
            book.close()
        # Manifesto íntegro em arquivo, mas com hash errado para um ícone necessário.
        with tempfile.TemporaryDirectory() as tmp:
            assets = Path(tmp) / 'assets'
            assets.mkdir()
            manifest = json.loads((ASSETS / 'manifest.json').read_text(encoding='utf8'))
            manifest['assets']['Icones/Ânima.png']['sha256'] = '0' * 64
            (assets / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf8')
            # Somente os recursos necessários para o teste são replicados.
            from app.assets import desired_paths, manifest_index
            index = manifest_index(manifest)
            for name in desired_paths(data, logging.getLogger('test.hash')):
                actual = index[name.casefold()][0]
                destination = assets / actual
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ASSETS / actual, destination)
            with self.assertRaisesRegex(AgendaError, 'Integridade inválida'):
                obtain_assets(data, Path(tmp) / 'download', logging.getLogger('test.hash'), local_assets=assets)



class FormulaCacheTests(unittest.TestCase):
    def test_formula_cached_values_preserved(self):
        example = ROOT / 'tests' / 'fixtures' / 'NomesSemanal.xlsx'
        if not example.is_file() or not (ASSETS / 'manifest.json').is_file():
            self.skipTest('Amostra real/recursos indisponíveis')
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'NomesSemanal.xlsx'
            shutil.copy2(example, path)
            for _ in range(2):
                run(path, local_assets=ASSETS, open_results=False)
                book = load_workbook(path, data_only=True, read_only=True)
                try:
                    sheet = book['Agenda']
                    self.assertEqual(sheet['J4'].value, 'Após Fech.')
                    self.assertEqual(sheet['K4'].value, '09:00')
                    self.assertIsNotNone(sheet['I9'].value)
                finally:
                    book.close()
            with zipfile.ZipFile(path) as archive:
                self.assertIsNone(archive.testzip())
            book = load_workbook(path, data_only=False)
            try:
                self.assertTrue(book['Agenda']['J4'].value.startswith('='))
            finally:
                book.close()

if __name__ == '__main__':
    unittest.main()
