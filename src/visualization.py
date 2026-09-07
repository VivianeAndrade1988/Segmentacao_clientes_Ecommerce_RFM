"""
visualization.py
-----------------
Funções de plotagem usadas ao longo da análise exploratória e da
interpretação dos clusters. Centralizar aqui evita duplicar código de
estilo entre o notebook e eventuais scripts/dashboards.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

PALETTE = "tab10"


def set_plot_style() -> None:
    """Aplica um tema consistente a todos os gráficos matplotlib/seaborn
    gerados no projeto."""
    sns.set_theme(
        context="talk",
        style="ticks",
        font_scale=0.8,
        palette=PALETTE,
        rc={
            "figure.figsize": (12, 8),
            "axes.grid": True,
            "grid.alpha": 0.2,
            "axes.titlesize": "x-large",
            "axes.titleweight": "bold",
            "axes.titlepad": 20,
        },
    )


def plot_elbow(evaluation_df: pd.DataFrame, metric: str = "inertia", ax=None):
    """Plota a curva do método do cotovelo (ou de qualquer métrica) em
    função de k, a partir da tabela gerada por
    `src.clustering.evaluate_k_range`.
    """
    ax = ax or plt.gca()
    evaluation_df[metric].plot(marker="o", ax=ax)
    ax.set_xlabel("k (nº de clusters)")
    ax.set_ylabel(metric)
    ax.set_title(f"Método do cotovelo — {metric}")
    return ax


def plot_cluster_centers_bar(centers: pd.DataFrame):
    """Reproduz o gráfico de barras divergente por cluster (adaptado de
    'Practical Statistics for Data Scientists'): mostra, para cada
    cluster, se cada variável está acima (verde) ou abaixo (vermelho) da
    média geral.
    """
    n_clusters = len(centers)
    fig, axes = plt.subplots(nrows=n_clusters, figsize=(12, 3 * n_clusters), sharex=True)
    if n_clusters == 1:
        axes = [axes]
    for i, ax in enumerate(axes):
        center = centers.loc[i, :]
        max_pc = 1.01 * center.abs().max()
        colors = ["#2C5F2D" if v > 0 else "#B85042" for v in center]
        center.plot.bar(ax=ax, color=colors)
        ax.set_ylabel(f"Cluster {i}")
        ax.set_ylim(-max_pc, max_pc)
        ax.axhline(color="gray", linewidth=0.8)
        ax.xaxis.set_ticks_position("none")
    plt.xticks(rotation=0, ha="center")
    plt.tight_layout()
    return fig


def plot_rfm_boxplots(df_rfm: pd.DataFrame, title: str = "Distribuição das variáveis RFM"):
    fig, ax = plt.subplots(figsize=(10, 6))
    df_rfm.plot.box(ax=ax)
    ax.set_title(title)
    plt.tight_layout()
    return fig
