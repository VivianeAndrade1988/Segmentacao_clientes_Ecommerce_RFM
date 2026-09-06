"""
data_processing.py
-------------------
Funções de carga e limpeza do dataset transacional de e-commerce
(Online Retail Dataset - UCI / Kaggle).

Responsabilidades desta camada:
    1. Carregar o arquivo bruto (CSV) com o encoding correto.
    2. Padronizar tipos de dados (datas, categorias, inteiros).
    3. Remover nulos, duplicados e inconsistências (quantidade/preço <= 0).
    4. Tratar outliers extremos identificados na análise exploratória.
    5. Criar a coluna derivada `price_total` (Quantity * UnitPrice).

Este módulo NÃO calcula RFM nem faz clusterização — ver `src/rfm.py`
e `src/clustering.py`."""


from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)

# Limites de corte identificados na análise exploratória (EDA) do notebook
# original. Ficam centralizados aqui para facilitar auditoria e ajuste.
MAX_QUANTITY = 8_000
MAX_UNIT_PRICE = 8_000


def load_raw_data(path: str | Path, encoding: str = "latin1") -> pd.DataFrame:
    """Carrega o CSV bruto do Online Retail Dataset.

    Parameters
    ----------
    path:
        Caminho para o arquivo .csv (ex.: data/raw/data.csv).
    encoding:
        O dataset original usa `latin1` (contém caracteres não-UTF8).

    Returns
    -------
    pd.DataFrame
        DataFrame bruto, sem qualquer tratamento.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado em '{path}'. Baixe o dataset "
            "'Online Retail Dataset' (UCI Machine Learning Repository / Kaggle) "
            "e salve como data/raw/data.csv. Veja instruções em data/raw/README.md."
        )
    logger.info("Carregando dados brutos de %s", path)
    df = pd.read_csv(path, encoding=encoding)
    logger.info("Shape bruto: %s", df.shape)
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica a pipeline completa de limpeza sobre o DataFrame bruto.

    Etapas (na ordem em que são aplicadas):
        1. Remove linhas duplicadas.
        2. Remove linhas sem CustomerID (não é possível atribuir RFM
           a um cliente desconhecido).
        3. Converte `InvoiceDate` para datetime e `CustomerID` para int.
        4. Converte `Country` para categoria (menor uso de memória).
        5. Remove linhas com Quantity <= 0 ou UnitPrice <= 0
           (devoluções, erros de lançamento, brindes).
        6. Remove outliers extremos (Quantity/UnitPrice acima dos limites
           definidos em MAX_QUANTITY / MAX_UNIT_PRICE), identificados
           via boxplot na EDA.
        7. Cria a coluna `price_total`.

    Notes
    -----
    No notebook original a remoção de duplicados era apenas diagnosticada
    (`df.duplicated().sum()`) mas nunca aplicada — aqui a duplicidade é
    de fato removida, pois compras duplicadas infladas distorcem as
    métricas de Frequência (F) e Monetário (M) do RFM.
    """
    n0 = len(df)
    df = df.drop_duplicates().copy()
    logger.info("Duplicados removidos: %d", n0 - len(df))

    df = df.dropna(subset=["CustomerID"]).copy()

    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M")
    df["CustomerID"] = df["CustomerID"].astype(int)
    df["Country"] = df["Country"].astype("category")

    below_zero = df[["Quantity", "UnitPrice"]].le(0).any(axis=1)
    df = df[~below_zero].copy()
    logger.info("Linhas removidas por Quantity/UnitPrice <= 0: %d", below_zero.sum())

    extreme = (df["Quantity"] >= MAX_QUANTITY) | (df["UnitPrice"] >= MAX_UNIT_PRICE)
    df = df[~extreme].copy()
    logger.info("Outliers extremos removidos: %d", extreme.sum())

    df["price_total"] = df["Quantity"] * df["UnitPrice"]

    logger.info("Shape final após limpeza: %s", df.shape)
    return df


def data_quality_report(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna um pequeno relatório de qualidade de dados (nulos, dtypes).

    Útil para logar/exibir no notebook ou em um dashboard de monitoramento.
    """
    report = pd.DataFrame(
        {
            "dtype": df.dtypes.astype(str),
            "n_nulos": df.isna().sum(),
            "pct_nulos": (df.isna().mean() * 100).round(2),
            "n_unicos": df.nunique(),
        }
    )
    return report.sort_values("pct_nulos", ascending=False)
