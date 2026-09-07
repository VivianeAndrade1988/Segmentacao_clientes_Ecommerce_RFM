"""
pipeline.py
-----------
Ponto de entrada único que executa toda a pipeline de ponta a ponta:

    1. Carrega e limpa os dados brutos.
    2. Salva os dados limpos em data/processed/ (reaproveitável sem reprocessar o bruto).
    3. Calcula RFM por cliente e salva em data/processed/ (reaproveitável sem recalcular).
    4. Trata outliers (winsorização) e padroniza as variáveis.
    5. Treina o modelo final de clusterização (KMeans, k=4).
    6. Gera o perfil de cada cluster.
    7. Exporta os resultados para outputs/reports/cluster_segments.xlsx.

Uso:
    python -m src.pipeline --input data/raw/data.csv --output outputs/reports/cluster_segments.xlsx
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from src.clustering import cluster_profile, fit_kmeans
from src.data_processing import clean_data, load_raw_data
from src.rfm import clip_outliers, compute_rfm, scale_rfm

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

N_CLUSTERS = 4
CLUSTER_LABELS = {
    0: "Em risco (baixo engajamento)",
    1: "Possível churn",
    2: "Ativos de alta frequência",
    3: "Alto valor",
}


def run_pipeline(
    input_path: str | Path,
    output_path: str | Path,
    processed_dir: str | Path = "data/processed",
) -> pd.DataFrame:
    processed_dir = Path(processed_dir)
    processed_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Etapa 1/6 — carregando e limpando dados")
    df_raw = load_raw_data(input_path)
    df = clean_data(df_raw)

    dados_limpos_path = processed_dir / "dados_limpos.csv"
    df.to_csv(dados_limpos_path, index=False)
    logger.info("Dados limpos salvos em %s (%d linhas)", dados_limpos_path, len(df))

    logger.info("Etapa 2/6 — calculando RFM")
    df_rfm = compute_rfm(df)

    logger.info("Etapa 3/6 — tratando outliers e padronizando")
    df_rfm_clip = clip_outliers(df_rfm)
    df_rfm_scaled, _scaler = scale_rfm(df_rfm_clip)

    rfm_path = processed_dir / "rfm_tratado.csv"
    df_rfm_clip.to_csv(rfm_path)
    logger.info("RFM tratado (winsorizado, escala original) salvo em %s", rfm_path)

    logger.info("Etapa 4/6 — treinando KMeans (k=%d)", N_CLUSTERS)
    _model, labels = fit_kmeans(df_rfm_scaled, n_clusters=N_CLUSTERS)

    logger.info("Etapa 5/6 — gerando perfil de clusters")
    profile = cluster_profile(df_rfm_clip, labels)
    logger.info("\n%s", profile)

    logger.info("Etapa 6/6 — exportando resultado final")
    df_result = df_rfm_clip.assign(cluster=labels)
    df_result["segmento"] = df_result["cluster"].map(CLUSTER_LABELS)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path) as writer:
        profile.to_excel(writer, sheet_name="resumo_clusters")
        for cluster_id in sorted(df_result["cluster"].unique()):
            sheet = f"cluster_{cluster_id}"
            df_result.query("cluster == @cluster_id").to_excel(writer, sheet_name=sheet)

    logger.info("Resultados exportados para %s", output_path)
    return df_result


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de segmentação RFM + Clusterização")
    parser.add_argument("--input", default="data/raw/data.csv", help="Caminho do CSV bruto")
    parser.add_argument(
        "--output",
        default="outputs/reports/cluster_segments.xlsx",
        help="Caminho do Excel de saída",
    )
    parser.add_argument(
        "--processed-dir",
        default="data/processed",
        help="Pasta onde salvar os dados intermediários (limpos e RFM tratado)",
    )
    args = parser.parse_args()
    run_pipeline(args.input, args.output, args.processed_dir)


if __name__ == "__main__":
    main()
