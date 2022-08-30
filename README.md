# Beancount Bourse Direct Importer

[![GitHub Workflow Status](https://img.shields.io/github/workflow/status/ArthurFDLR/beancount-bd/beancount-bd?style=for-the-badge)](https://github.com/ArthurFDLR/beancount-bd/actions)
[![PyPI](https://img.shields.io/pypi/v/beancount-bd?style=for-the-badge)](https://pypi.org/project/beancount-bd/)
[![PyPI - Version](https://img.shields.io/pypi/pyversions/beancount-bd.svg?style=for-the-badge)](https://pypi.org/project/beancount-bd/)
[![GitHub](https://img.shields.io/github/license/ArthurFDLR/beancount-bd?style=for-the-badge)](https://github.com/ArthurFDLR/beancount-bd/blob/master/LICENSE.txt)
[![Linting](https://img.shields.io/badge/code%20style-black-000000.svg?style=for-the-badge)](https://github.com/psf/black)

`beancount-bd` provides an order history importer for the brooker [Bourse Direct](http://www.boursedirect.fr) to the [Beancount](http://furius.ca/beancount/) format.

## Installation

```console
    $ pip install beancount-bd
```

## Usage

Add ```BDImporter``` to your [Beancount importers config file](https://beancount.github.io/docs/importing_external_data.html#configuration).

```python
CONFIG = [
    BDImporter(
        account='Assets:FR:BD:PEA',
        fee_category='Expenses:Finances:Commission',
        tickers_lut={
            "AM.E.P.SP500": "PE500",
            "LY.PEANASD": "PUST",
            "MSC.EM": "PAEEM",
            "MSC.EUR": "PCEU",
        }
    ),
]
```

## Contribution

Feel free to contribute!

Please make sure you have Python 3.6+ and [`Poetry`](https://poetry.eustace.io/) installed.

1. Git clone the repository - `git clone https://github.com/ArthurFDLR/beancount-bd`

2. Install the packages required for development - `poetry install`

3. That's basically it. You should now be able to run lint checks and the test suite - `make lint test`.
