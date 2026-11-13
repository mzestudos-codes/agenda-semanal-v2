"""Regras da nova modalidade sem dependências de GitHub ou planilhas pessoais."""
import logging
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook,load_workbook

from app.daily import read_daily_date,validate_daily
from app.mercado import image_name,period_folder,run
from app.validation import AgendaError

LOGGER=logging.getLogger('tests.mercado')


def daily_sheet():
    book=Workbook();sheet=book.active;sheet.title='Diária'
    sheet['J2']=datetime(2026,11,13);sheet['J3']='sexta-feira'
    return book,sheet


class DailyTests(unittest.TestCase):
    def test_date_and_weekday(self):
        book,ws=daily_sheet()
        self.assertEqual(read_daily_date(ws).isoformat(),'2026-11-13')
        ws['J3']='segunda-feira'
        with self.assertRaises(AgendaError):read_daily_date(ws)
        ws['J3']=None
        with self.assertRaises(AgendaError):read_daily_date(ws)
        book.close()

    def test_unlimited_items_sorted_without_losing_metadata(self):
        book,ws=daily_sheet()
        for row,name,clock in [(3,'A','15:00'),(4,'B','08:00'),(5,'C','11:00'),(6,'D','12:00'),(7,'E','07:30'),(8,'F','09:00')]:
            ws[f'C{row}']=name;ws[f'L{row}']=clock;ws[f'M{row}']='-'
        groups=validate_daily(ws,LOGGER)
        self.assertEqual([x['empresa'] for x in groups['conferencias']],['E','B','F','C','D','A'])
        self.assertEqual([x['horario_pt'] for x in groups['conferencias']],['07:30','08:00','09:00','11:00','12:00','15:00'])
        self.assertEqual(len(groups['conferencias']),6)
        book.close()

    def test_duplicate_same_category_and_different_category(self):
        book,ws=daily_sheet();ws['A3']='XP';ws['K3']='Antes Abert.'
        ws['C3']='xp';ws['L3']='09:30';ws['M3']='-'
        validate_daily(ws,LOGGER)
        ws['A4']='xp';ws['K4']='Após Fech.'
        with self.assertRaisesRegex(AgendaError,'duplicada'):validate_daily(ws,LOGGER)
        book.close()

    def test_filenames(self):
        day=datetime(2026,11,13).date()
        self.assertEqual(image_name('diaria',day),'Agenda_Diaria_13-Novembro-2026.png')
        self.assertEqual(image_name('semanal',day),'Agenda_Semanal_13-Novembro-2026.png')

    def test_period_folders(self):
        from datetime import date
        self.assertEqual(
            period_folder('semanal', date(2026, 11, 16), date(2026, 11, 20)),
            'Agenda Semanal de 16-Novembro-2026 até 20-Novembro-2026'
        )
        self.assertEqual(
            period_folder('diaria', date(2026, 11, 18)),
            'Agenda Diária de 18-Novembro-2026'
        )
        self.assertEqual(
            period_folder('semanal', date(2026, 12, 28), date(2027, 1, 1)),
            'Agenda Semanal de 28-Dezembro-2026 até 01-Janeiro-2027'
        )

    def test_ambas_validation_prevents_excel_modification(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'agenda.xlsx'
            wb=Workbook();wb.active.title='Semanal';daily=wb.create_sheet('Diária')
            daily['J2']=datetime(2026,11,13);daily['J3']='sexta-feira'
            wb.save(path);wb.close()
            original=path.read_bytes()
            with self.assertRaises(AgendaError):run(path,mode='ambas',open_results=False)
            self.assertEqual(path.read_bytes(),original)
            self.assertFalse((Path(tmp)/'Imagens').exists())


if __name__=='__main__':unittest.main()
