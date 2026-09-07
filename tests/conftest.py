"""
conftest.py
-----------
Gera um dataset sintético (fixture pytest) com a MESMA estrutura do
Online Retail Dataset, usado para testar a pipeline sem depender do
arquivo de dados real (que não é versionado no repositório por ser
um dataset de terceiros — ver data/raw/README.md).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_raw_df() -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    n_rows = 3000
    n_customers = 150

    customer_ids = rng.integers(10000, 10000 + n_customers, size=n_rows).astype(float)
    invoice_ids = rng.integers(536000, 540000, size=n_rows).astype(str)
    countries = rng.choice(
        ["United Kingdom", "Germany", "France", "Eire"], size=n_rows, p=[0.85, 0.06, 0.05, 0.04]
    )
    dates = pd.to_datetime("2011-01-01") + pd.to_timedelta(
        rng.integers(0, 365, size=n_rows), unit="D"
    )
    date_strings = dates.strftime("%m/%d/%Y %H:%M")

    quantity = rng.integers(-5, 50, size=n_rows)  # inclui negativos (devoluções) de propósito
    unit_price = np.round(rng.uniform(0.5, 50, size=n_rows), 2)

    # injeta alguns outliers extremos de propósito, para testar a remoção
    quantity[0] = 9000
    unit_price[1] = 9000

    df = pd.DataFrame(
        {
            "InvoiceNo": invoice_ids,
            "StockCode": rng.integers(10000, 99999, size=n_rows).astype(str),
            "Description": "PRODUTO TESTE",
            "Quantity": quantity,
            "InvoiceDate": date_strings,
            "UnitPrice": unit_price,
            "CustomerID": customer_ids,
            "Country": countries,
        }
    )

    # injeta duplicados e nulos de propósito, para testar a limpeza
    df = pd.concat([df, df.iloc[:20]], ignore_index=True)
    df.loc[df.sample(frac=0.05, random_state=1).index, "CustomerID"] = np.nan

    return df
