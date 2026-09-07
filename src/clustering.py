"""
clustering.py
-------------
Ajuste e avaliação de algoritmos de clusterização sobre as variáveis
RFM padronizadas, e utilitários para interpretação dos clusters
resultantes (perfil por segmento).

Algoritmos comparados (conforme desafio original):
    - KMeans
    - Agglomerative (Hierarchical) Clustering
    - Gaussian Mixture Model (GMM)

Métricas de avaliação:
    - Silhouette Score        (quanto maior, melhor)
    - Davies-Bouldin Score    (quanto menor, melhor)
    - Calinski-Harabasz Score (quanto maior, melhor)
"""

from __future__ import annotations

import logging

import pandas as pd
from sklearn.cluster import AgglomerativeClustering, KMeans
from sklearn.mixture import GaussianMixture
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)

logger = logging.getLogger(__name__)

METRICS = (silhouette_score, davies_bouldin_score, calinski_harabasz_score)


def evaluate_k_range(X: pd.DataFrame, algorithm: str = "kmeans", k_min: int = 2, k_max: int = 10, random_state: int = 42) -> pd.DataFrame:
    """Ajusta o algoritmo escolhido para uma faixa de k e retorna uma
    tabela comparativa de métricas — usada para decidir o número ideal
    de clusters.

    Parameters
    ----------
    algorithm:
        'kmeans' ou 'agglomerative'.
    """
    results = []
    for k in range(k_min, k_max + 1):
        if algorithm == "kmeans":
            model = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        elif algorithm == "agglomerative":
            model = AgglomerativeClustering(n_clusters=k)
        else:
            raise ValueError("algorithm deve ser 'kmeans' ou 'agglomerative'")

        labels = model.fit_predict(X)
        row = {"k": k}
        if hasattr(model, "inertia_"):
            row["inertia"] = model.inertia_
        for metric in METRICS:
            row[metric.__name__] = metric(X, labels)
        results.append(row)

    return pd.DataFrame(results).set_index("k")


def evaluate_gmm(X: pd.DataFrame, k_min: int = 1, k_max: int = 8, covariance_types=("full", "tied", "diag", "spherical"), random_state: int = 42) -> pd.DataFrame:
    """Avalia GMM por BIC para diferentes números de componentes e tipos
    de covariância (abordagem recomendada em 'Practical Statistics for
    Data Scientists').
    """
    results = []
    for n_components in range(k_min, k_max + 1):
        for covariance_type in covariance_types:
            model = GaussianMixture(
                n_components=n_components,
                covariance_type=covariance_type,
                n_init=5,
                random_state=random_state,
            )
            model.fit(X)
            results.append(
                {
                    "n_components": n_components,
                    "covariance_type": covariance_type,
                    "bic": model.bic(X),
                }
            )
    return pd.DataFrame(results)


def fit_kmeans(X: pd.DataFrame, n_clusters: int, random_state: int = 42) -> tuple[KMeans, "pd.Series[int]"]:
    """Treina o modelo final de KMeans e retorna (modelo, labels)."""
    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    labels = model.fit_predict(X)
    return model, pd.Series(labels, index=X.index, name="cluster")


def cluster_profile(df_rfm: pd.DataFrame, labels: "pd.Series[int]") -> pd.DataFrame:
    """Retorna o perfil médio (R, F, M) de cada cluster, ordenado pelo
    índice do cluster — a base para a interpretação de negócio.
    """
    profile = df_rfm.assign(cluster=labels).groupby("cluster").mean()
    profile["n_clientes"] = df_rfm.assign(cluster=labels).groupby("cluster").size()
    profile["pct_clientes"] = (profile["n_clientes"] / profile["n_clientes"].sum() * 100).round(1)
    return profile.round(2)
