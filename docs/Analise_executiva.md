# Análise Executiva — Segmentação de Clientes (RFM + Clusterização)

**Público-alvo:** liderança de Marketing, CRM e Comercial
**Metodologia:** RFM (Recência, Frequência, Valor Monetário) + Clusterização (KMeans, k=4)

>  **Nota sobre os números deste documento:** para que este projeto seja 100% executável e
> auditável sem depender de um dataset externo, os números abaixo foram gerados a partir de uma
> **execução de exemplo com dados sintéticos** representativos da estrutura do dataset real (ver
> `data/raw/README.md`). Ao rodar a pipeline com o dataset real (`data/raw/data.csv`), a tabela
> de segmentos deve ser **regenerada e os números deste documento atualizados** — a metodologia
> e a estrutura de recomendações permanecem válidas.

---

## 1. Contexto e pergunta de negócio

A empresa queria responder: **"quem são os nossos clientes, e como devemos tratar cada grupo de
forma diferente?"** Em vez de tratar toda a base de clientes com a mesma campanha de marketing,
segmentamos os clientes em **4 grupos com comportamentos de compra distintos**, para permitir
ações direcionadas por perfil.

## 2. Como a segmentação foi feita (em 3 frases)

Calculamos, para cada cliente, há quanto tempo ele comprou pela última vez (**Recência**), com
que frequência ele compra (**Frequência**) e qual o seu ticket médio (**Valor Monetário**).
Agrupamos os clientes com comportamento de compra semelhante usando um algoritmo de
clusterização (KMeans), testado contra alternativas e validado estatisticamente. O resultado são
4 segmentos, cada um com um perfil de risco/valor diferente.

## 3. Os 4 segmentos identificados

*(Números da execução de exemplo — ver nota no topo do documento)*

| Segmento | % da base | Recência média (dias) | Frequência média (pedidos) | Ticket médio |
|---|---|---|---|---|
|  **Clientes de alto valor e alta frequência** | ~24% | 13 | 25,9 | R$ 730 |
|  **Recorrentes de ticket moderado** | ~29,5% | 10 | 18,0 | R$ 632 |
|  **Recorrentes de ticket mais baixo** | ~29,5% | 11 | 24,7 | R$ 518 |
|  **Em risco de churn** | ~17% | 41 | 20,3 | R$ 641 |

###  Clientes de alto valor e alta frequência
Compram com frequência acima da média **e** com o maior ticket médio do grupo — o perfil mais
valioso da base. Compraram recentemente, o que indica engajamento ativo.

**Ações recomendadas:**
- Programa de fidelidade/VIP com benefícios exclusivos (frete grátis, acesso antecipado).
- Atendimento dedicado e comunicação personalizada.
- Campanhas de indicação ("indique um amigo") — são o grupo mais propenso a recomendar a marca.

###  Recorrentes de ticket moderado
Compram recentemente e com frequência razoável, com ticket médio saudável, mas ainda abaixo do
segmento de maior valor. Representam a maior fatia da base junto ao próximo segmento.

**Ações recomendadas:**
- Ofertas de upsell/cross-sell para elevar o ticket médio.
- Comunicação de novidades de catálogo, para estimular aumento de frequência.

###  Recorrentes de ticket mais baixo
Compram com frequência alta (próxima ao segmento de maior valor) e recentemente, mas com o menor
ticket médio da base — indicam engajamento presente, mas baixo valor por compra.

**Ações recomendadas:**
- Cross-sell de produtos complementares para aumentar o valor do carrinho.
- Testar frete grátis a partir de um valor mínimo, para incentivar tickets maiores.

###  Em risco de churn
O único grupo com Recência claramente acima da média (41 dias desde a última compra, o dobro
dos demais grupos) — sinal de afastamento. Frequência e ticket médio ainda saudáveis, o que
sugere que são clientes que já tiveram bom relacionamento com a marca e vale a pena reconquistar.

**Ações recomendadas:**
- Campanha de reativação com oferta de retorno (cupom, frete grátis).
- Pesquisa curta de motivo de afastamento.
- Monitorar: se a Recência continuar subindo sem resposta às campanhas, o risco de perda
  definitiva aumenta.

## 4. Recomendação de priorização

Com orçamento de marketing limitado, a ordem de prioridade sugerida é:

1. **Reter o segmento "Em risco de churn"** — é mais barato reter um cliente já conhecido do que
   adquirir um novo, e este grupo já demonstrou disposição de compra no passado.
2. **Aumentar o ticket do segmento "Recorrentes de ticket mais baixo"** — já compram com
   frequência, então o ganho marginal de aumentar o valor médio do carrinho tem retorno rápido.
3. **Fidelizar o segmento de alto valor** — proteger a receita mais valiosa da base contra
   concorrência.
4. **Nutrir o segmento "Recorrentes de ticket moderado"** rumo ao segmento de alto valor.

## 5. Como acompanhar o impacto

Recomenda-se **reexecutar esta análise periodicamente** (sugestão: trimestral) e acompanhar:

- **Migração entre segmentos** — quantos clientes saíram de "alto valor" para "em risco"? Isso é
  um alerta antecipado de queda de receita.
- **Tamanho relativo de cada segmento ao longo do tempo** — o segmento "em risco" está
  crescendo ou encolhendo?
- **Taxa de conversão das campanhas de reativação** — validação direta do ROI da estratégia.
- 

## 6. Limitações a considerar

- A segmentação reflete o comportamento **histórico** de compra; não prevê diretamente a
  probabilidade futura de churn (isso exigiria um modelo preditivo supervisionado, fora do
  escopo deste projeto).
- A análise não diferencia **categoria de produto** — dois clientes no mesmo segmento RFM podem
  comprar categorias completamente diferentes; vale complementar com análise de categoria antes
  de desenhar a oferta específica de cada campanha.

---

Para detalhes metodológicos completos, ver [`README_TECNICO.md`](README_TECNICO.md).
Para a versão em slides, ver [`ANALISE_EXECUTIVA.pptx`](ANALISE_EXECUTIVA.pptx).

