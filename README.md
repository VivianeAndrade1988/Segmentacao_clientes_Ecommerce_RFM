# Segmentação de Clientes de E-commerce via RFM + Clusterização


Projeto de ciência de dados que segmenta a base de clientes de um e-commerce a partir do
comportamento de compra (**R**ecência, **F**requência, **M**onetário) e de algoritmos de
clusterização, para orientar estratégias de marketing e fidelização.

>  **Desafio original:** análise de RFM + clusterização sobre o *Online Retail Dataset*
> (transações de dez/2010 a dez/2011 de um e-commerce do Reino Unido). Este repositório
> reorganiza, corrige e documenta a análise original como um projeto de portfólio completo.

---

##  Objetivo de negócio

Uma empresa de e-commerce quer entender melhor seus clientes para:

- identificar clientes de **alto valor** e fortalecer o relacionamento com eles;
- identificar clientes em **risco de churn** e agir antes que deixem de comprar;
- direcionar **campanhas de marketing segmentadas** em vez de campanhas genéricas.

A resposta é um modelo de **segmentação RFM** que agrupa os clientes em 4 perfis
comportamentais, cada um com recomendações de ação específicas.

##  O que tem neste repositório

| Você quer... | Veja |
|---|---|
| Entender a análise e as recomendações em linguagem de negócio | [`docs/ANALISE_EXECUTIVA.md`](docs/ANALISE_EXECUTIVA.md) |
| Apresentar os resultados a stakeholders | [`docs/ANALISE_EXECUTIVA.pptx`](docs/ANALISE_EXECUTIVA.pptx) |
| Entender decisões técnicas, metodologia e como reproduzir | [`docs/README_TECNICO.md`](docs/README_TECNICO.md) |
| Ver a análise exploratória e a modelagem passo a passo | [`notebooks/rfm_clustering_analysis.ipynb`](notebooks/rfm_clustering_analysis.ipynb) |
| Rodar a pipeline em produção/lote | [`src/pipeline.py`](src/pipeline.py) |

##  Quickstart

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd desafio7-rfm-customer-segmentation

# 2. Criar ambiente virtual e instalar dependências
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. (Opcional) baixar o dataset real — veja data/raw/README.md
#    Sem esse passo, o projeto roda com dados sintéticos de exemplo.

# 4. Rodar os testes
pytest -v

# 5. Rodar a pipeline completa (gera outputs/reports/cluster_segments.xlsx)
python -m src.pipeline --input data/raw/sample_data.csv --output outputs/reports/cluster_segments.xlsx

# 6. Ou explorar interativamente
jupyter notebook notebooks/01_rfm_clustering_analysis.ipynb
```

##  Estrutura do projeto

```
.
├── README.md                       ← você está aqui (visão geral)
├── LICENSE
├── requirements.txt
├── .github/workflows/ci.yml        ← testes automatizados a cada push
│
├── data/
│   ├── raw/                        ← dados brutos (dataset real não versionado — ver README.md interno)
│   └── processed/                  ← dados intermediários (criada e preenchida ao rodar a pipeline)
│
├── notebooks/
│   └── 01_rfm_clustering_analysis.ipynb   ← EDA + modelagem + interpretação, passo a passo
│
├── src/                             ← pipeline de produção, testada e reutilizável
│   ├── data_processing.py          ← carga e limpeza dos dados
│   ├── rfm.py                      ← cálculo de RFM, tratamento de outliers, padronização
│   ├── clustering.py               ← ajuste e avaliação de modelos de clusterização
│   ├── visualization.py            ← funções de plotagem reutilizáveis
│   └── pipeline.py                 ← orquestração ponta a ponta (CLI)
│
├── tests/                           ← testes automatizados (pytest) com dados sintéticos
│
├── outputs/
│   ├── figures/                    ← gráficos exportados
│   └── reports/                    ← planilhas de clientes segmentados (.xlsx)
│
└── docs/
    ├── README_TECNICO.md           ← documentação técnica detalhada
    ├── ANALISE_EXECUTIVA.md        ← resumo executivo em linguagem de negócio
    └── ANALISE_EXECUTIVA.pptx      ← apresentação executiva
```

##  Metodologia (resumo)

1. **Limpeza de dados** — remoção de duplicados, nulos, valores inconsistentes (quantidade/preço
   ≤ 0) e outliers extremos.
2. **Cálculo de RFM** por cliente — Recência, Frequência e Valor Monetário médio.
3. **Tratamento estatístico** — winsorização (clipping no percentil 95) + padronização (z-score).
4. **Seleção de algoritmo** — comparação entre KMeans, Clusterização Hierárquica e Gaussian
   Mixture Model, usando Silhouette Score, Davies-Bouldin e Calinski-Harabasz.
5. **Modelo final** — KMeans com k=4, escolhido pelo melhor equilíbrio entre separação
   estatística dos clusters e interpretabilidade de negócio.
6. **Interpretação e recomendações** — perfil de cada cluster traduzido em estratégias de CRM.

Detalhes de cada decisão (por que winsorização, por que k=4, por que KMeans e não GMM, etc.)
estão documentados em [`docs/README_TECNICO.md`](docs/README_TECNICO.md).

##  Qualidade e testes

O código em `src/` é coberto por testes automatizados (`tests/`) que validam cada etapa da
pipeline (limpeza, RFM, clusterização) usando dados sintéticos, e roda em CI a cada push.

```bash
pytest -v
```

##  Licença

Este projeto está sob a licença MIT — veja [`LICENSE`](LICENSE).
