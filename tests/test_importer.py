import pathlib
import pytest
import datetime

from beancount_bd import __version__, BDImporter
from beancount.core.number import Decimal

TEST_FILE_PATH = 'test_reference.html'

TEST_ACCOUNT_NAME = 'Assets:FR:BD:PEA'
TEST_DATE = datetime.date(2022, 8, 22)


def test_version():
    assert __version__ == '0.1.0'


@pytest.fixture
def filename():
    return pathlib.Path(__file__).parent.absolute() / TEST_FILE_PATH


@pytest.fixture
def importer():
    return BDImporter(
        account=TEST_ACCOUNT_NAME,
        tickers_lut={
            "AM.E.P.SP500": "PE500",
            "LY.PEANASD": "PUST",
            "MSC.EM": "PAEEM",
            "MSC.EUR": "PCEU",
        },
    )


def test_identify(importer, filename):
    with open(filename) as fd:
        assert importer.identify(fd)


def test_file_date(importer, filename):
    with open(filename) as fd:
        assert importer.file_date(fd) == TEST_DATE


def test_extract(importer, filename):
    with open(filename) as fd:
        operations = importer.extract(fd)

    operations_test = [
        {
            'date': datetime.date(2022, 8, 22),
            'amount': Decimal('-336.20'),
            'payee': 'ACHAT COMPTANT: 10x AM.ETF PEA SP500 U.ETF EUR FCP AM.E.P.SP500 EUR',
            'qtt': Decimal(10),
            'asset': 'PE500',
            'price': Decimal('33.521'),
        },
        {
            'date': datetime.date(2022, 8, 8),
            'amount': Decimal('-208.75'),
            'payee': 'ACHAT COMPTANT: 4x LYX.PEA NASDAQ-100 UC.ETF FCP LY.PEANASD.-100UC',
            'qtt': Decimal(4),
            'asset': 'PUST',
            'price': Decimal('51.94'),
        },
        {
            'date': datetime.date(2022, 7, 29),
            'amount': Decimal('1500.00'),
            'payee': 'VIRT MR ARTHUR FIN',
            'qtt': Decimal("-1500.00"),
            'asset': 'EUR',
            'price': None,
        },
        {
            'date': datetime.date(2022, 6, 1),
            'amount': Decimal('-220.24'),
            'payee': 'ACHAT COMPTANT: 10x AM.PEA MSCI EM.MKTS UC.ETF FCP AM.PEA MSC.EM M.UC',
            'qtt': Decimal(10),
            'asset': 'PAEEM',
            'price': Decimal('21.925'),
        },
    ]
    op_name_test = [op_test['payee'] for op_test in operations_test]

    assert len(operations) == len(operations_test)

    for op in operations:

        assert op.payee in op_name_test, 'Missing operation'
        op_test = operations_test[op_name_test.index(op.payee)]

        assert op.payee == op_test['payee'], 'Wrong payee name'
        assert op.date == op_test['date'], 'Wrong date'

        assert len(op.postings) >= 2, "Too few postings"

        assert (
            op.postings[0].account == TEST_ACCOUNT_NAME
        ), 'Wrong account name'
        assert op.postings[0].units.currency == 'EUR', 'Wrong amount currency'
        assert op.postings[0].units.number == op_test['amount'], 'Wrong amount'

        assert op.postings[1].units.number == op_test['qtt'], 'Wrong quantity'
        assert (
            op.postings[1].units.currency == op_test['asset']
        ), 'Wrong asset ticker symbol'
        if op.postings[1].price is not None:
            assert (
                op.postings[1].price.number == op_test['price']
            ), 'Wrong asset price'
            assert (
                op.postings[1].price.currency == 'EUR'
            ), 'Wrong price currency'
