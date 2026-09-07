# Documentação Técnica

Este documento descreve, em profundidade, as decisões de arquitetura, metodologia estatística
e escolhas de engenharia do projeto de segmentação de clientes via RFM + clusterização.

## Índice

1. [Arquitetura da solução](#1-arquitetura-da-solução)
2. [Dataset](#2-dataset)
3. [Pipeline de dados](#3-pipeline-de-dados)
4. [Metodologia RFM](#4-metodologia-rfm)
5. [Tratamento estatístico](#5-tratamento-estatístico)
6. [Seleção do algoritmo de clusterização](#6-seleção-do-algoritmo-de-clusterização)
7. [Avaliação de clusters](#7-avaliação-de-clusters)
8. [Decisões de correção em relação à análise original](#8-decisões-de-correção-em-relação-à-análise-original)
9. [Como reproduzir](#9-como-reproduzir)
10. [Testes](#10-testes)
11. [Limitações e trabalhos futuros](#11-limitações-e-trabalhos-futuros)

---

## 1. Arquitetura da solução

O projeto segue uma separação clara entre **código de produção** (`src/`) e **análise
exploratória/narrativa** (`notebooks/`), um padrão comum em projetos de ciência de dados que
precisam evoluir de protótipo para pipeline confiável:

```
data/raw/  →  src/data_processing.py  →  src/rfm.py  →  src/clustering.py  →  outputs/
                        ↑                                        ↑
                        └────────── src/visualization.py ────────┘
                                          ↑
                              notebooks/*.ipynb (importa src/, narra a análise)
```

- **`src/data_processing.py`** — I/O e limpeza. Não conhece RFM nem clusterização.
- **`src/rfm.py`** — cálculo de métricas RFM e tratamento estatístico (outliers, escala).
  Não conhece a origem dos dados nem o algoritmo de clusterização usado depois.
- **`src/clustering.py`** — ajuste/avaliação de modelos e geração de perfis de cluster.
  Recebe apenas DataFrames numéricos — desacoplado de como o RFM foi calculado.
- **`src/visualization.py`** — plotagem, sem lógica de negócio.
- **`src/pipeline.py`** — orquestra as camadas acima em um único comando de CLI, para uso em
  lote/produção (ex.: um job agendado que roda mensalmente).
- **`notebooks/`** — usa as mesmas funções de `src/`, mas foca em contar a história da análise
  (EDA, comparação de algoritmos, interpretação) — o notebook não duplica lógica de limpeza ou
  modelagem, apenas a invoca e visualiza.

Essa separação garante que a lógica testada em `tests/` é **exatamente** a mesma usada no
notebook e na pipeline de produção — não há risco de "no notebook funciona, em produção não".

## 2. Dataset

**Online Retail Dataset** (UCI Machine Learning Repository / Kaggle): transações de um
e-commerce do Reino Unido entre 01/12/2010 e 09/12/2011.

| Coluna | Tipo original | Observação |
|---|---|---|
| InvoiceNo | object | Contém letras (ex.: prefixo "C" = cancelamento) — por isso não é numérico |
| StockCode | object | Código do produto |
| Description | object | ~4.100 descrições distintas |
| Quantity | int64 | Contém negativos (devoluções) |
| InvoiceDate | object | Convertido para `datetime64` com formato `%m/%d/%Y %H:%M` |
| UnitPrice | float64 | Contém zeros e valores muito altos (outliers) |
| CustomerID | float64 | ~25% de nulos no dataset original — descartados (sem cliente, sem RFM) |
| Country | object | 38 países distintos; ~91% Reino Unido |

O arquivo real não é versionado no repositório (ver `data/raw/README.md`); os testes e a
demonstração do notebook usam uma **amostra sintética** gerada por código, com a mesma
estrutura de colunas e as mesmas classes de problema (nulos, duplicados, outliers) do dataset
real, para que a pipeline seja 100% reprodutível sem depender de um download externo.

## 3. Pipeline de dados

Implementada em `src/data_processing.clean_data`, nesta ordem (a ordem importa — cada etapa
assume que a anterior já rodou):

1. **Remoção de duplicados exatos** (`df.drop_duplicates()`).
2. **Remoção de nulos em `CustomerID`** — sem ID de cliente não há como atribuir RFM.
3. **Conversão de tipos**: `InvoiceDate` → `datetime64`, `CustomerID` → `int`, `Country` →
   `category` (reduz uso de memória em colunas de baixa cardinalidade).
4. **Remoção de `Quantity` ≤ 0 ou `UnitPrice` ≤ 0** — devoluções, brindes e erros de
   lançamento não representam receita real.
5. **Remoção de outliers extremos** (`Quantity ≥ 8.000` ou `UnitPrice ≥ 8.000`) — identificados
   via boxplot na EDA como pontos isolados que distorcem a escala de qualquer análise
   subsequente (ex.: uma única compra corporativa de milhares de unidades).
6. **Criação de `price_total`** = `Quantity × UnitPrice`.

Os limiares (`MAX_QUANTITY`, `MAX_UNIT_PRICE`) ficam como constantes nomeadas no topo do
módulo — centralizados para facilitar auditoria, versionamento e ajuste fino sem caça a
números mágicos espalhados pelo código.

## 4. Metodologia RFM

Implementada em `src/rfm.compute_rfm`:

```python
R = (data_de_referência − última_compra_do_cliente).dias
F = nº de InvoiceNo únicos do cliente   # nº de pedidos, não de itens
M = média de price_total por pedido do cliente   # ticket médio, não soma total
```

**Data de referência:** calculada automaticamente como `max(InvoiceDate) + 1 dia`. Essa é uma
diferença deliberada em relação à análise original (que fixava `2012-01-01` diretamente no
código) — calcular a partir dos próprios dados torna a função **genérica e reprodutível** para
qualquer corte temporal do dataset (ex.: se a pipeline rodar mensalmente sobre uma janela mais
recente de dados, a data de referência se ajusta automaticamente).

**Por que Monetário = ticket médio, e não gasto total?** Gasto total confunde "cliente que
compra muito por pedido" com "cliente que compra com muita frequência" — e frequência já é
capturada por F. Usar a média por pedido isola a dimensão de "quanto o cliente costuma gastar
de cada vez", complementar (e não redundante) a F.

## 5. Tratamento estatístico

Após o cálculo do RFM bruto, duas transformações são aplicadas antes da clusterização
(`src/rfm.clip_outliers` e `src/rfm.scale_rfm`):

1. **Winsorização (clipping) no percentil 95** — em vez de descartar outliers (o que perderia
   clientes de negócio potencialmente relevantes, como grandes compradores), seus valores são
   "achatados" no percentil 95 de cada variável. Isso preserva o cliente no dataset mas evita
   que ele, sozinho, puxe um centróide inteiro de cluster para longe do restante da base.
2. **Padronização (Z-score, `StandardScaler`)** — R, F e M estão em escalas completamente
   diferentes (dias vs. contagem de pedidos vs. valor monetário). Sem padronização, a variável
   de maior magnitude (tipicamente R, em dias) dominaria o cálculo de distância euclidiana
   usado por KMeans e Clusterização Hierárquica.

> A análise original também identificava e removia manualmente um cliente outlier específico
> (ID 15098, com ticket médio incoerente). Neste projeto, a winsorização no percentil 95
> generaliza esse tratamento para **qualquer** outlier semelhante, sem exigir intervenção
> manual cliente a cliente — importante para que a pipeline rode de forma autônoma em lotes
> futuros de dados, onde os IDs de outliers específicos mudam a cada execução.

## 6. Seleção do algoritmo de clusterização

Três algoritmos foram comparados (`src/clustering.py`):

| Algoritmo | Pressuposto | Prós | Contras |
|---|---|---|---|
| **KMeans** | Clusters esféricos, variância similar | Rápido, muito interpretável (centróides), escala bem | Sensível a outliers residuais e a k mal escolhido |
| **Agglomerative (Hierárquico)** | Nenhum pressuposto de forma fixo | Não exige k a priori (dendrograma), robusto a formas variadas | Mais custoso computacionalmente em bases grandes |
| **Gaussian Mixture Model (GMM)** | Clusters gaussianos, podem ter formas elípticas | Atribuição probabilística (soft clustering) | Mais complexo de explicar a stakeholders de negócio; maior risco de overfitting sem regularização |

Para KMeans e Hierárquico, o número de clusters `k` foi avaliado no intervalo de 2 a 10 usando
três métricas complementares (nenhuma métrica isolada é suficiente):

- **Silhouette Score** — mede coesão intra-cluster vs. separação inter-cluster (-1 a 1, quanto
  maior melhor).
- **Davies-Bouldin Score** — razão entre dispersão intra-cluster e distância entre centróides
  (quanto menor, melhor).
- **Calinski-Harabasz Score** — razão entre variância inter-cluster e intra-cluster (quanto
  maior, melhor; sensível ao tamanho da amostra, por isso usado em conjunto com as outras duas).

Para GMM, a seleção de `n_components` e do tipo de covariância seguiu o critério **BIC**
(Bayesian Information Criterion), que penaliza modelos excessivamente complexos.

**Decisão final: KMeans, k=4.** Critérios:

1. Melhor (ou muito próximo do melhor) resultado nas três métricas de separação entre os
   algoritmos comparados.
2. Centróides diretamente interpretáveis (a média de R, F, M de cada cluster tem leitura de
   negócio direta), o que não é tão direto no GMM (parâmetros de covariância).
3. k=4 produz segmentos de negócio acionáveis (nem poucos demais para diferenciar estratégias,
   nem tantos a ponto de fragmentar demais as campanhas de CRM).

## 7. Avaliação de clusters

Após o ajuste do modelo final, `src/clustering.cluster_profile` calcula, por cluster:

- Média de R, F, M (na escala original, não padronizada — para leitura de negócio direta).
- Número absoluto e percentual de clientes.

Essa tabela é a base para o mapeamento de cada cluster a um rótulo de negócio (ex.: "Alto
valor", "Possível churn") em `docs/ANALISE_EXECUTIVA.md`.

## 8. Decisões de correção em relação à análise original

Durante a reestruturação do notebook original em pipeline de produção, os seguintes problemas
foram identificados e corrigidos:

| # | Problema no notebook original | Correção aplicada |
|---|---|---|
| 1 | Linhas duplicadas eram diagnosticadas (`df.duplicated().sum()`) mas nunca removidas | `clean_data` agora remove duplicados antes de qualquer cálculo |
| 2 | Data de referência do RFM fixada como constante (`'2012-01-01'`) | Calculada dinamicamente como `max(InvoiceDate) + 1 dia`, reprodutível para qualquer corte temporal |
| 3 | Outlier de cliente específico (ID 15098) removido manualmente, não generalizável | Substituído por winsorização estatística no percentil 95, aplicável a qualquer execução futura |
| 4 | Célula de interpretação de cluster referenciava `cluster_0` antes de sua definição (erro de ordem de execução) | Lógica reescrita em `cluster_profile`, sem dependência de ordem de células |
| 5 | Resultados de GMM (`results.append`) sem a chave `covariance_type`, usada depois em `hue=` do gráfico | Corrigido em `evaluate_gmm`, que inclui `covariance_type` em cada linha de resultado |
| 6 | Dependência de ambiente Google Colab (`/content/data.csv`, `google.colab.files.download`) | Caminhos parametrizados via CLI/argumentos; export para arquivo local em `outputs/reports/` |
| 7 | Protótipo de dashboard Dash com dados de exemplo hardcoded, desconectado do pipeline real | Removido do escopo deste projeto (fica como sugestão de trabalho futuro, seção 11) |

## 9. Como reproduzir

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Com dados sintéticos (já incluídos):
python -m src.pipeline --input data/raw/sample_data.csv --output outputs/reports/cluster_segments.xlsx

# Com o dataset real (após baixar conforme data/raw/README.md):
python -m src.pipeline --input data/raw/data.csv --output outputs/reports/cluster_segments.xlsx

# Notebook interativo:
jupyter notebook notebooks/01_rfm_clustering_analysis.ipynb
```

## 10. Testes

`tests/` cobre as três camadas centrais da pipeline com dados sintéticos gerados em
`tests/conftest.py` (mesma estrutura do dataset real, incluindo nulos, duplicados e outliers
propositais):

- limpeza de dados remove nulos, duplicados e valores inválidos corretamente;
- RFM tem as colunas esperadas e valores estatisticamente coerentes (F ≥ 1, M > 0, R ≥ 0);
- winsorização respeita o limite de percentil configurado;
- padronização produz média ~0 e desvio padrão ~1;
- avaliação de k produz as três métricas para cada k testado;
- o pipeline completo (fit + profile) roda de ponta a ponta sem erros.

```bash
pytest -v
```

Rodado em CI a cada push/PR (`.github/workflows/ci.yml`).

## 11. Regenerando a apresentação executiva

O arquivo `docs/ANALISE_EXECUTIVA.pptx` é gerado programaticamente pelo script
`scripts/build_pptx.js` (via `pptxgenjs`), o que permite atualizar os números após rodar a
pipeline com o dataset real, mantendo o mesmo design:

```bash
npm install pptxgenjs   # se ainda não estiver instalado
node scripts/build_pptx.js
```

Atualize os valores de `metrics` no script com o resultado de
`src.clustering.cluster_profile` obtido na execução com dados reais.

## 12. Limitações e trabalhos futuros

- **Estabilidade temporal dos clusters não avaliada.** Não foi medido quanto os clusters se
  mantêm estáveis se a pipeline rodar em janelas de tempo diferentes (ex.: mês a mês). Sugestão:
  acompanhar a migração de clientes entre segmentos ao longo do tempo como métrica adicional.
- **RFM tradicional não captura sazonalidade nem categoria de produto.** Uma extensão natural
  é incorporar variáveis de categoria de produto predominante por cliente, ou RFM segmentado por
  categoria.
- **KMeans assume clusters aproximadamente esféricos.** Se a distribuição real dos clientes for
  fortemente não-convexa, vale reavaliar DBSCAN ou HDBSCAN (mencionados, mas não aprofundados,
  na análise original).
- **Dashboard interativo não implementado neste escopo.** O protótipo Dash do notebook original
  foi removido por estar desconectado da pipeline real; um dashboard (Streamlit/Dash) consumindo
  diretamente `outputs/reports/cluster_segments.xlsx` é uma extensão natural para consumo
  self-service pelo time de marketing.
- **Sem monitoramento de drift.** Para uso contínuo em produção, recomenda-se instrumentar a
  pipeline com alertas caso a distribuição de R, F ou M mude significativamente entre execuções.
