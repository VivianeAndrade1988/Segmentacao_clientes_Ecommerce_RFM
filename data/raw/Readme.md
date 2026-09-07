# Dados brutos

Este projeto usa o **Online Retail Dataset**, um conjunto público de transações de um
e-commerce do Reino Unido entre dezembro/2010 e dezembro/2011.

## Como obter os dados reais

O arquivo `data.csv` **não é versionado neste repositório** (é um dataset de terceiros,
com ~45 MB e licença própria). Baixe-o em uma das fontes abaixo e salve como
`data/raw/data.csv`:

- UCI Machine Learning Repository: *Online Retail Dataset*
- Kaggle: busque por "Online Retail Dataset" (mesmas colunas)

Colunas esperadas:

| Coluna | Tipo | Descrição |
|---|---|---|
| InvoiceNo | string | Número da nota fiscal (prefixo "C" = cancelamento) |
| StockCode | string | Código do produto |
| Description | string | Descrição do produto |
| Quantity | int | Quantidade vendida |
| InvoiceDate | string (`%m/%d/%Y %H:%M`) | Data/hora da transação |
| UnitPrice | float | Preço unitário |
| CustomerID | float | ID do cliente (pode ser nulo) |
| Country | string | País do cliente |

## Dados sintéticos (`sample_data.csv`)

Para permitir que **qualquer pessoa execute o notebook e os testes sem precisar baixar o
dataset real**, este repositório inclui `sample_data.csv`: uma amostra **sintética**,
gerada por código (`tests/conftest.py` usa o mesmo gerador), com a mesma estrutura de
colunas do dataset real, incluindo nulos, duplicados e outliers propositais para exercitar
a limpeza de dados.

> ⚠️ Os números e conclusões de negócio deste repositório (README executivo, apresentação)
> são baseados em uma execução de exemplo. **Para uma análise real, substitua os dados
> pelo dataset oficial** e reexecute a pipeline (`python -m src.pipeline`) ou o notebook.

