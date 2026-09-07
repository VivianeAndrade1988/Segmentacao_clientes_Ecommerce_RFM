"""
test_pipeline.py
-----------------
Testes de unidade/integração para as três camadas da pipeline:
data_processing -> rfm -> clustering.

Rodar com: pytest -v
"""

from __future__ import annotations

import pandas as pd

from src.clustering import cluster_profile, evaluate_k_range, fit_kmeans
from src.data_processing import MAX_QUANTITY, MAX_UNIT_PRICE, clean_data
from src.rfm import clip_outliers, compute_rfm, scale_rfm


def test_clean_data_removes_nulls_duplicates_and_negatives(synthetic_raw_df):
    df_clean = clean_data(synthetic_raw_df)

    assert df_clean["CustomerID"].isna().sum() == 0
    assert not df_clean.duplicated().any()
    assert (df_clean["Quantity"] > 0).all()
    assert (df_clean["UnitPrice"] > 0).all()
    assert (df_clean["Quantity"] < MAX_QUANTITY).all()
    assert (df_clean["UnitPrice"] < MAX_UNIT_PRICE).all()
    assert "price_total" in df_clean.columns
    assert pd.api.types.is_datetime64_any_dtype(df_clean["InvoiceDate"])


def test_compute_rfm_has_expected_columns_and_positive_values(synthetic_raw_df):
    df_clean = clean_data(synthetic_raw_df)
    df_rfm = compute_rfm(df_clean)

    assert list(df_rfm.columns) == ["R", "F", "M"]
    assert (df_rfm["R"] >= 0).all()
    assert (df_rfm["F"] >= 1).all()
    assert (df_rfm["M"] > 0).all()
    # cada CustomerID deve aparecer uma única vez
    assert df_rfm.index.is_unique


def test_clip_outliers_caps_at_quantile(synthetic_raw_df):
    df_clean = clean_data(synthetic_raw_df)
    df_rfm = compute_rfm(df_clean)
    df_clip = clip_outliers(df_rfm, upper_quantile=0.95)

    for col in df_rfm.columns:
        assert df_clip[col].max() <= df_rfm[col].quantile(0.95) + 1e-9


def test_scale_rfm_produces_zero_mean_unit_variance(synthetic_raw_df):
    df_clean = clean_data(synthetic_raw_df)
    df_rfm = compute_rfm(df_clean)
    df_scaled, scaler = scale_rfm(df_rfm)

    assert abs(df_scaled.mean().mean()) < 1e-8
    assert df_scaled.shape == df_rfm.shape
    assert scaler is not None


def test_evaluate_k_range_returns_metrics_for_each_k(synthetic_raw_df):
    df_clean = clean_data(synthetic_raw_df)
    df_rfm = compute_rfm(df_clean)
    df_scaled, _ = scale_rfm(df_rfm)

    result = evaluate_k_range(df_scaled, algorithm="kmeans", k_min=2, k_max=4)

    assert set(result.index) == {2, 3, 4}
    assert "silhouette_score" in result.columns
    assert "davies_bouldin_score" in result.columns
    assert "calinski_harabasz_score" in result.columns


def test_fit_kmeans_and_cluster_profile_end_to_end(synthetic_raw_df):
    df_clean = clean_data(synthetic_raw_df)
    df_rfm = compute_rfm(df_clean)
    df_clip = clip_outliers(df_rfm)
    df_scaled, _ = scale_rfm(df_clip)

    model, labels = fit_kmeans(df_scaled, n_clusters=4)

    assert len(labels) == len(df_rfm)
    assert labels.nunique() <= 4
    assert model.cluster_centers_.shape[0] == 4

    profile = cluster_profile(df_clip, labels)
    assert "n_clientes" in profile.columns
    assert profile["n_clientes"].sum() == len(df_rfm)
