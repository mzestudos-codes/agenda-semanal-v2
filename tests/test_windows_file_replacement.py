"""Regressão: não substituir um arquivo ainda aberto por ZipFile (WinError 5)."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

from openpyxl import Workbook
from app.excel_write import restore_formula_cache


class WindowsReplacementTests(unittest.TestCase):
    def test_zip_handles_closed_before_replace(self):
        with tempfile.TemporaryDirectory() as directory:
            original = Path(directory) / 'original.xlsx'
            candidate = Path(directory) / 'candidate.xlsx'
            wb = Workbook()
            wb.active.title = 'Agenda'
            wb.active['J4'] = '=1+1'
            wb.save(original)
            wb.save(candidate)
            wb.close()

            opened = []
            def track_zip(*args, **kwargs):
                archive = ZipFile(*args, **kwargs)
                opened.append(archive)
                return archive

            real_replace = os.replace
            def verify_and_replace(source, destination):
                self.assertEqual(Path(destination), candidate)
                self.assertTrue(opened)
                self.assertTrue(all(item.fp is None for item in opened),
                                'Arquivo ZIP ainda aberto durante os.replace')
                return real_replace(source, destination)

            with patch('app.excel_write.ZipFile', side_effect=track_zip), \
                 patch('app.excel_write.os.replace', side_effect=verify_and_replace):
                restore_formula_cache(original, candidate)
            with ZipFile(candidate) as archive:
                self.assertIsNone(archive.testzip())

if __name__ == '__main__':
    unittest.main()
