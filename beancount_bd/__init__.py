__version__ = '0.1.0'

from typing import Dict, Optional
import pandas as pd
from datetime import datetime

from beancount.ingest import importer
from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import Decimal


class BDImporter(importer.ImporterProtocol):
    """Beancount Importer for Caisse d'Epargne PDF and CSV statement.

    Attributes:
        account (str): Account name in beancount format (e.g. 'Assets:FR:BD:PEA')
        labels_lut (dict[str:str]): Look-up tables of the order labels (e.g. {'AM.E.P.SP500':'SP500'})
    """

    def __init__(
        self,
        account: str,
        labels_lut: Optional[Dict[str,str]] = None,
    ):
        self.account = account
        self.labels_lut = labels_lut
        self.expected_columns = {
            'Cours',
            'Date affectation',
            'Date opération',
            'Libellé',
            'Montant net',
            'Opération',
            'Qté',
        }

    ## API Methods ##
    #################

    def name(self):
        return 'Bourse Direct: {}'.format(self.__class__.__name__)

    def file_account(self, _):
        return self.account

    def file_date(self, file_):
        if not self.identify(file_):
            return None
        
        n = file_ if type(file_) == str else file_.name
        date = None
        bd_tables = pd.read_html(n)

        for bf_df in bd_tables:
            if "Date affectation" in set(bf_df.columns):
                for _, row in bf_df.iterrows():
                    try:
                        date_tmp = datetime.strptime(
                            str(row["Date affectation"]), '%d/%m/%Y'
                        ).date()
                    except ValueError:
                        continue
                    if not date or date_tmp > date:
                        date = date_tmp
        return date

    def file_name(self, _):
        return 'BourseDirect.html'

    def identify(self, file_) -> bool:
        n = file_ if type(file_) == str else file_.name
        try:
            bd_tables = pd.read_html(n)
            for df in bd_tables:
                if set(df.columns) == self.expected_columns:
                    break
            else:
                return False
        except:
            return False
        return True

    def extract(self, file_, existing_entries=None):

        entries = (
            list(existing_entries[:]) if existing_entries is not None else []
        )
        n = file_ if type(file_) == str else file_.name

        bd_tables = pd.read_html(n)
        for bf_df in bd_tables:
            if set(bf_df.columns) == self.expected_columns:
                for index, row in bf_df.iterrows():

                    meta = data.new_metadata(n, index)
                    op_date = datetime.strptime(
                        row["Date affectation"], '%d/%m/%Y'
                    ).date()
                    op_payee = (
                        f"{row['Opération']}: {row['Qté']}x {row['Libellé']}"
                    )
                    op_narration = ""

                    op_currency = 'EUR'
                    op_amount = Decimal(
                        row['Montant net'].replace("€", "").replace(",", ".")
                    )
                    postings = [
                        data.Posting(
                            self.account,
                            Amount(op_amount, op_currency),
                            None,
                            None,
                            None,
                            None,
                        ),
                        data.Posting(
                            self.account,
                            Amount(
                                row['Qté'],
                                self.labels_lut.get(row['Libellé']) if self.labels_lut is not None else row['Libellé'],
                            ),
                            None,
                            None,
                            None,
                            None,
                        ),
                        data.Posting(
                            "Expenses:Finances:Commission",
                            None,
                            None,
                            None,
                            None,
                            None,
                        ),
                    ]

                    entries.append(
                        data.Transaction(
                            meta=meta,
                            date=op_date,
                            flag=flags.FLAG_OKAY,
                            payee=op_payee,
                            narration=op_narration,
                            tags=data.EMPTY_SET,
                            links=data.EMPTY_SET,
                            postings=postings,
                        )
                    )
        return entries
