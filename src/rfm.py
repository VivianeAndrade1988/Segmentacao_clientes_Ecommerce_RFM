"""
rfm.py
------
Cálculo das métricas RFM (Recência, Frequência, Valor Monetário) por
cliente, e tratamento estatístico das variáveis antes da clusterização.

RFM:
    R (Recency)   - dias desde a última compra até a data de referência.
    F (Frequency) - número de pedidos (InvoiceNo únicos) do cliente.
    M (Monetary)  - ticket médio do cliente (média de price_total por pedido).
"""

from __future__ import annotations

import logging

import pandas as pd
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


def compute_rfm(df: pd.DataFrame, reference_date: pd.Timestamp | None = None) -> pd.DataFrame:
    """Calcula RFM por CustomerID.

    Parameters
    ----------
    df:
        DataFrame já limpo (ver `src.data_processing.clean_data`), deve
        conter as colunas: CustomerID, InvoiceDate, InvoiceNo, price_total.
    reference_date:
        Data de referência para o cálculo de Recência. Se None, usa
        (data máxima de compra no dataset + 1 dia) — abordagem padrão em
        projetos de RFM, que evita "hardcodar" uma data que só funciona
        para este dataset específico (o notebook original fixava
        '2012-01-01').

    Returns
    -------
    pd.DataFrame
        Indexado por CustomerID, com colunas R, F, M.
    """
    if reference_date is None:
        reference_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
        logger.info("Data de referência calculada automaticamente: %s", reference_date)

    df_rfm = df.groupby("CustomerID").agg(
        R=("InvoiceDate", lambda x: (reference_date - x.max()).days),
        F=("InvoiceNo", "nunique"),
        M=("price_total", "mean"),
    )
    return df_rfm


def remove_rfm_outliers(df_rfm: pd.DataFrame, customer_ids: list[int]) -> pd.DataFrame:
    """Remove clientes específicos identificados como outliers extremos
    na análise exploratória do RFM (ex.: ticket médio incoerente)."""
    return df_rfm.drop(index=[c for c in customer_ids if c in df_rfm.index])


def clip_outliers(df_rfm: pd.DataFrame, upper_quantile: float = 0.95) -> pd.DataFrame:
    """Faz winsorização (clipping) das variáveis RFM no percentil superior
    informado, reduzindo a influência de outliers sem descartar clientes.
    """
    return df_rfm.apply(lambda col: col.clip(upper=col.quantile(upper_quantile)))


def scale_rfm(df_rfm: pd.DataFrame) -> tuple[pd.DataFrame, StandardScaler]:
    """Padroniza (z-score) as variáveis RFM para uso em algoritmos de
    clusterização baseados em distância (KMeans, Hierárquico, GMM).

    Returns
    -------
    (df_scaled, scaler)
        DataFrame padronizado e o objeto `StandardScaler` já ajustado,
        para permitir transformações inversas (ex.: reconverter os
        centróides para a escala original).
    """
    scaler = StandardScaler()
    scaled_values = scaler.fit_transform(df_rfm)
    df_scaled = pd.DataFrame(scaled_values, index=df_rfm.index, columns=df_rfm.columns)
    return df_scaled, scaler
