from unittest.case import TestCase

class TestClient(TestCase):

    def setUp(self):
        self.args = {
            'read_col': 0,
            'write_col': False,
            'min_probability': 95,
            'file': 'test/test.xls'

        }

    def test_(self):
        run(self.args)

    def _write(self):
        data = [
            ['daniel', ''],
            ['cristina', ''],
            ['cassandra', ''],
        ] * 34
        workbook = xlwt.Workbook()
        write_sheet = workbook.add_sheet("Sheet1", cell_overwrite_ok=True)
        for y, row in enumerate(data):
            for x, cell in enumerate(row):
                write_sheet.write(y, x, cell)
        workbook.save('test.xls')
