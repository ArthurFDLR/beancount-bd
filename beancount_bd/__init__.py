__version__ = '1.0.0'

import sys, traceback

from typing import Dict, Optional
import pandas as pd
from datetime import datetime

from beancount.ingest import importer
from beancount.core import data, flags
from beancount.core.amount import Amount
from beancount.core.number import Decimal
from beancount.core.position import Cost


class BDImporter(importer.ImporterProtocol):
    """Beancount Importer for Caisse d'Epargne PDF and CSV statement.

    Attributes:
        account (str): Account name in beancount format (e.g. 'Assets:FR:BD:PEA')
        tickers_lut (dict[str:str]): Look-up tables of the order labels (e.g. {'AM.E.P.SP500':'SP500', ...})
        fee_category (str): Category in which to record fees (e.g. 'Expenses:Finances:Commission')
    """

    def __init__(
        self,
        account: str,
        tickers_lut: Dict[str, str] = dict(),
        fee_category: str = "Expenses:FIXME",
    ):
        self.account = account
        self.tickers_lut = tickers_lut
        self.fee_category = fee_category
        self.expected_columns = {
            'Cours',
            'Date affectation',
            'Date opération',
            'Libellé',
            'Montant net',
            'Opération',
            'Qté',
        }

    def _fetch_ticker(self, asset_name: str) -> Optional[str]:
        matches = []
        for name, ticker in self.tickers_lut.items():
            if name in asset_name:
                matches.append(ticker)
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            raise RuntimeError(f"Multiple asset name matched: {matches}")
        elif len(matches) == 0:
            return None

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

                    if (
                        isinstance(row['Opération'], str)
                        and "ACHAT" in row['Opération']
                    ):

                        try:
                            op_date = datetime.strptime(
                                row["Date affectation"], '%d/%m/%Y'
                            ).date()
                            op_payee = f"{row['Opération']}: {int(row['Qté'])}x {row['Libellé']}"
                            op_narration = ""

                            op_currency = 'EUR'
                            op_net_amount = Amount(
                                Decimal(
                                    row['Montant net']
                                    .replace("€", "")
                                    .replace(",", ".")
                                    .replace(" ", "")
                                ),
                                op_currency,
                            )
                            op_asset_ticker = self._fetch_ticker(
                                row['Libellé']
                            )
                            op_asset_qtt = Amount(
                                Decimal(
                                    row['Qté'],
                                ),
                                op_asset_ticker
                                if op_asset_ticker is not None
                                else "FIXME",
                            )
                            op_asset_amount = Decimal(
                                row['Cours']
                                .replace("€", "")
                                .replace(",", ".")
                                .replace(" ", ""),
                            )
                            op_asset_price = Amount(
                                op_asset_amount,
                                "EUR",
                            )
                            op_asset_cost = Cost(
                                op_asset_amount, "EUR", None, None
                            )
                        except Exception as e:
                            sys.stderr.write(
                                f"WARNING - Row {index} skipped:\n{traceback.format_exc()}\n"
                            )
                            continue

                        postings = [
                            data.Posting(
                                self.account,
                                op_net_amount,
                                None,
                                None,
                                None,
                                None,
                            ),
                            data.Posting(
                                account=self.account,
                                units=op_asset_qtt,
                                cost=op_asset_cost,
                                price=op_asset_price,
                                flag=None,
                                meta=None,
                            ),
                            data.Posting(
                                self.fee_category,
                                None,
                                None,
                                None,
                                None,
                                None,
                            ),
                        ]

                        entries.append(
                            data.Transaction(
                                meta=data.new_metadata(n, index),
                                date=op_date,
                                flag=flags.FLAG_OKAY,
                                payee=op_payee,
                                narration=op_narration,
                                tags=data.EMPTY_SET,
                                links=data.EMPTY_SET,
                                postings=postings,
                            )
                        )

                    elif (
                        isinstance(row['Opération'], str)
                        and "VIRT" in row['Opération']
                    ):
                        try:
                            op_date = datetime.strptime(
                                row["Date affectation"], '%d/%m/%Y'
                            ).date()
                            op_payee = str(row['Opération'])
                            op_narration = ""
                            op_currency = 'EUR'
                            op_net_amount = Amount(
                                Decimal(
                                    row['Montant net']
                                    .replace("€", "")
                                    .replace(",", ".")
                                    .replace(" ", "")
                                ),
                                op_currency,
                            )
                        except Exception as e:
                            sys.stderr.write(
                                f"WARNING - Row {index} skipped:\n{traceback.format_exc()}\n"
                            )
                            continue

                        postings = [
                            data.Posting(
                                account=self.account,
                                units=op_net_amount,
                                cost=None,
                                price=None,
                                flag=None,
                                meta=None,
                            ),
                            data.Posting(
                                account="Assets:FIXME",
                                units=-op_net_amount,
                                cost=None,
                                price=None,
                                flag=None,
                                meta=None,
                            ),
                        ]

                        entries.append(
                            data.Transaction(
                                meta=data.new_metadata(n, index),
                                date=op_date,
                                flag=flags.FLAG_OKAY,
                                payee=op_payee,
                                narration=op_narration,
                                tags=data.EMPTY_SET,
                                links=data.EMPTY_SET,
                                postings=postings,
                            )
                        )

                    else:
                        sys.stderr.write(
                            f"WARNING - Row {index} skipped: operation '{row['Opération']}' not supported.\n"
                        )
                        continue

        return entries
