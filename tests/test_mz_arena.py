import logging
import unittest
from datetime import datetime
from openpyxl import Workbook
from app.validation import AgendaError, validate_and_sort, read_week_dates
from app.daily import validate_daily, read_daily_date
from app.assets import desired_paths
from app.excel_write import ANCHORS

LOG = logging.getLogger('tests.arena')

class ArenaTests(unittest.TestCase):
    def test_daily_flag_and_column_shift(self):
        wb=Workbook();ws=wb.active;ws['J2']=datetime(2026,11,13);ws['J3']='sexta-feira'
        ws['F5']='ABC';ws['I5']=' SIM ';ws['N5']='Presencial';ws['O5']='14:00'
        self.assertEqual(read_daily_date(ws).day,13)
        data=validate_daily(ws,LOG)
        self.assertTrue(data['investor_day'][0]['mz_arena'])
        paths=desired_paths({'diaria':data},LOG)
        self.assertIn('Icones/MZ/MZArena.png',paths)
        ws['I5']='Não'
        with self.assertRaisesRegex(AgendaError,'I5'):validate_daily(ws,LOG)
        ws['I5']=None
        data=validate_daily(ws,LOG)
        self.assertFalse(data['investor_day'][0]['mz_arena'])
        self.assertNotIn('Icones/MZ/MZArena.png',desired_paths({'diaria':data},LOG))
        wb.close()

    def test_weekly_flag_and_anchors(self):
        wb=Workbook();ws=wb.active
        for offset,row in enumerate((2,9,17,25,33)):
            ws[f'J{row}']=datetime(2026,11,16+offset)
        ws['F4']='ABC';ws['I4']='sim';ws['N4']='Online';ws['O4']='09:00'
        data=validate_and_sort(ws,LOG)
        self.assertTrue(data['segunda']['investor_day'][0]['mz_arena'])
        self.assertEqual(read_week_dates(ws)['segunda'].day,16)
        self.assertIn('Q4',ANCHORS)
        self.assertEqual(len(ANCHORS),5)
        wb.close()

    def test_sem_informacao_is_valid(self):
        wb=Workbook();ws=wb.active;ws['J2']=datetime(2026,11,13);ws['J3']='sexta-feira'
        ws['A4']='AMBIPAR';ws['K4']='Sem informação'
        self.assertEqual(validate_daily(ws,LOG)['divulgacoes'][0]['periodo'],'Sem informação')
        wb.close()

if __name__=='__main__':unittest.main()
