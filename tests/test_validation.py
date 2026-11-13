import logging
import unittest
from datetime import datetime
from types import SimpleNamespace

from app.validation import AgendaError, validate_and_sort, parse_time, read_week_dates


class DummyWorksheet:
    def __init__(self):
        self.values = {}
        for offset, row in enumerate((2, 9, 17, 25, 33)):
            self.values[f'J{row}'] = datetime(2025, 11, 17 + offset)

    def __getitem__(self, key):
        return SimpleNamespace(value=self.values.get(key))

    def put(self, cell, value):
        self.values[cell] = value
        return self


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.ws = DummyWorksheet()
        self.log = logging.getLogger('agenda.tests')

    def test_period_and_alphabetical_order_with_hyphen_last(self):
        for i, (name, period) in enumerate([
            ('Zeta', '-'), ('Bravo', 'Após Fech.'), ('Delta', 'Antes Abert.'),
            ('Alpha', 'Antes Abert.'), ('Contax', '-')
        ], 4):
            self.ws.put('A' + str(i), name).put('K' + str(i), period)
        result = validate_and_sort(self.ws, self.log)
        self.assertEqual([e['empresa'] for e in result['segunda']['divulgacoes']],
                         ['Alpha', 'Delta', 'Bravo', 'Contax', 'Zeta'])

    def test_missing_period_blocks(self):
        self.ws.put('A4', 'Empresa Exemplo')
        with self.assertRaisesRegex(AgendaError, 'K4'):
            validate_and_sort(self.ws, self.log)

    def test_duplicate_case_insensitive(self):
        self.ws.put('A4', 'CONTAX').put('K4', '-').put('A5', 'contax').put('K5', '-')
        with self.assertRaisesRegex(AgendaError, 'duplicada'):
            validate_and_sort(self.ws, self.log)

    def test_marker_at_fifth_position_and_no_time_errors(self):
        for i, (name, pt, en) in enumerate([
            ('Zeta', '11:00', '11:00 AM'), ('Vejamaisconferencias', '-', '-'),
            ('Bravo', '10:00', 'Trad. Simul.'), ('Alpha', '09:30 AM', '-'),
            ('Delta', 'Sem informação', '-')
        ], 4):
            self.ws.put(f'C{i}', name).put(f'L{i}', pt).put(f'M{i}', en)
        result = validate_and_sort(self.ws, self.log)
        events = result['segunda']['conferencias']
        self.assertEqual([x['empresa'] for x in events],
                         ['Alpha', 'Bravo', 'Zeta', 'Delta', 'VejaMaisConferencias'])
        self.assertEqual(events[-1]['posicao_ordenada'], 5)
        self.assertTrue(events[-1]['marcador'])

    def test_time_formats_and_unknown(self):
        self.assertEqual(parse_time('09:30 AM'), 9 * 3600 + 30 * 60)
        self.assertEqual(parse_time('10h05'), 10 * 3600 + 5 * 60)
        for x in ('-', 'Trad. Simul.', 'Sem informação', None):
            self.assertIsNone(parse_time(x))
        with self.assertRaises(AgendaError):
            parse_time('talvez às dez')

    def test_empty_week_is_not_committed(self):
        with self.assertRaisesRegex(AgendaError, 'Nenhum evento'):
            validate_and_sort(self.ws, self.log)

    def test_date_mapping(self):
        self.assertEqual(read_week_dates(self.ws)['sexta'].isoformat(), '2025-11-21')

    def test_marker_from_wrong_category_is_invalid(self):
        self.ws.put('A4', 'VejaMaisInvestorDay').put('K4', '-')
        with self.assertRaisesRegex(AgendaError, 'categoria incorreta'):
            validate_and_sort(self.ws, self.log)

if __name__ == '__main__':
    unittest.main()
