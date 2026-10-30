# Entrega 3 — Carga do Data Warehouse

**Disciplina:** Mineração de Dados — IFMT  
**Projeto:** Laboratório de ETL — Mercatto Varejo  
**Equipe:** ____________________________________  
**Data:** ____/____/2026  
**Versão do pipeline:** ____________________________________

## 1. Objetivo

Esta entrega documenta a carga da camada analítica do projeto: dimensões
conformadas, fatos de pedidos, itens de pedidos, atendimentos e avaliações.
Também registra as decisões que afetam a integridade referencial, a
granularidade e a reconciliação dos dados.

O ambiente foi gerado com a semente `20262`, escala `1.0` e
`2.205.843` registros distribuídos entre as fontes. As contagens de referência
são:

| Fonte | Registros |
|---|---:|
| Clientes do legado | 47.250 |
| Produtos do legado | 3.000 |
| Pedidos do legado | 130.000 |
| Itens do legado | 397.086 |
| Clientes do e-commerce | 85.000 |
| Produtos do e-commerce | 12.000 |
| Pedidos do e-commerce | 280.000 |
| Itens do e-commerce | 995.367 |
| Atendimentos SAC | 96.140 |
| Avaliações marketplace | 160.000 |

## 2. Escopo da carga

A etapa 3 executa as seguintes operações:

1. recriação da dimensão de tempo;
2. carga das dimensões de cliente, produto, status e canal;
3. carga do fato de pedidos;
4. carga do fato de itens de pedidos;
5. carga dos fatos auxiliares de atendimento e avaliação;
6. execução e registro das asserções de qualidade no esquema `qa`.

As tabelas do DW são recarregadas de forma idempotente. Antes da carga, cada
tabela é truncada com reinício das identidades e, depois, recebe somente o
lote calculado a partir da staging. Assim, uma nova execução não duplica
registros.

## 3. Modelo carregado

### Dimensões

- `dw.dim_tempo`: calendário entre `2022-12-01` e `2026-03-31`;
- `dw.dim_cliente`: identidade conformada entre legado e e-commerce;
- `dw.dim_produto`: catálogo combinado das duas origens;
- `dw.dim_status`: status de origem e status conformado;
- `dw.dim_canal`: canal de origem e canal conformado.

### Fatos

- `dw.fato_pedido`: **uma linha por pedido de origem**. A chave de negócio é
  formada por `sistema_origem` e `id_origem` (`LEG-...` ou `ECOM-...`);
- `dw.fato_item_pedido`: **uma linha por item de pedido**, mantendo a
  granularidade mais detalhada e a referência ao pedido;
- `dw.fato_atendimento`: **uma linha por protocolo de atendimento**;
- `dw.fato_avaliacao`: **uma linha por avaliação**.

Manter as granularidades separadas evita multiplicar pedidos quando um pedido
possui vários itens, atendimentos ou avaliações.

## 4. Registro de decisões da Entrega 3

### RDT-01 — Tipo de carga

**Decisão:** usar carga completa e idempotente.

**Alternativas consideradas:**

1. carga incremental por data de alteração;
2. `append` de todos os registros;
3. truncamento das tabelas analíticas seguido de carga completa.

**Escolha e justificativa:** as fontes não oferecem um mecanismo confiável de
controle de alterações ou de watermark. A carga completa é reproduzível e a
semente dos dados é fixa. O truncamento evita duplicidade em reexecuções.

**O que se perde:** não há histórico de versões entre duas execuções e o custo
computacional é maior. Essa perda é aceitável no escopo acadêmico.

**Registros afetados:** todas as tabelas do DW a cada execução; na escala
atual, a carga parte de aproximadamente 2,2 milhões de registros de origem.

### RDT-10 — Itens órfãos

**Decisão:** carregar somente itens cujo pedido foi localizado na tabela
`dw.fato_pedido`.

**Alternativas consideradas:**

1. inserir o item com pedido nulo;
2. criar um pedido artificial “desconhecido”;
3. excluir o item órfão e registrar a perda.

**Escolha e justificativa:** a FK de `fato_item_pedido` exige um pedido válido.
O item sem pedido não pode ser atribuído com segurança a outro pedido, portanto
é descartado da carga e deve ser quantificado na transformação/qualidade.

**O que se perde:** os valores e quantidades dos itens sem pedido não ficam
disponíveis para análise. A decisão preserva a integridade, mas pode reduzir o
total financeiro quando comparado diretamente à origem.

**Registros afetados:** a proporção esperada no cenário é de aproximadamente
1,5% dos itens de cada origem; o número final deve ser preenchido a partir da
asserção executada no ambiente:

`Itens órfãos identificados: ____________________`.

### RDT-11 — Granularidade dos fatos

**Decisão:** manter `fato_pedido` e `fato_item_pedido` como fatos distintos.

**Justificativa:** pedido e item têm grãos diferentes. Agregar itens ao pedido
na mesma tabela provocaria repetição de medidas como frete e valor total.

**O que se perde:** algumas consultas exigem uma junção ou uma agregação
explícita. Em compensação, as medidas não são infladas por cardinalidade.

**Registros afetados:** 410.000 pedidos de referência (130.000 do legado e
280.000 do e-commerce) e 1.392.453 itens de referência antes do tratamento de
órfãos.

### RDT-12 — Pedidos sem cliente correspondente

**Decisão:** utilizar a chave substituta da dimensão de cliente e manter um
cliente desconhecido quando a origem não puder ser pareada com segurança.

**Justificativa:** um pedido não deve desaparecer apenas porque o cadastro do
cliente está incompleto. O valor `NULL` na FK impediria análises por cliente e
quebraria a integridade referencial.

**O que se perde:** a atribuição individual do pedido ao cliente real quando
não existe evidência suficiente para o pareamento. O pedido continua
disponível nas análises agregadas.

**Registros afetados:** preencher após a execução da consulta de cobertura:

`Pedidos sem correspondência de cliente: ____________________`.

### RDT-13 — Atendimentos e avaliações sem pedido

**Decisão:** preservar os registros auxiliares, mas deixar a referência ao
pedido ausente como `NULL` quando não houver correspondência confiável.

**Justificativa:** atendimento e avaliação são eventos válidos mesmo quando a
origem não fornece uma chave de pedido localizável. Excluí-los apagaria
informação sobre a experiência do cliente.

Na correção da carga, as chaves foram normalizadas com o prefixo da origem:
`LEG-<id>` para o legado e `ECOM-<id>` para o e-commerce. A verificação
executada anteriormente registrou `0` correspondências ausentes para SAC e
avaliações após esse ajuste.

**O que se perde:** nesses casos, não é possível relacionar o evento a um
pedido específico nem calcular métricas por pedido.

## 5. Qualidade e asserções

A etapa registra as verificações em `qa.execucao_assercao`. As verificações
previstas para a carga são:

| Asserção | Critério |
|---|---|
| Quantidade de pedidos no DW | pedidos do DW = pedidos das duas origens |
| Reconciliação financeira — legado | diferença relativa inferior a 0,1% |
| Reconciliação financeira — e-commerce | diferença relativa inferior a 0,1% |
| FK de cliente em `fato_pedido` | zero órfãos |
| Dias de entrega negativos | zero ocorrências |
| Chaves de SAC e avaliações | correspondência feita quando a chave é válida |

Consulta para anexar a evidência da execução:

```sql
SELECT etapa, nome, valor_obtido, valor_esperado, aprovado, executado_em
FROM qa.execucao_assercao
WHERE etapa = '03_carga_dw'
ORDER BY id;
```

### Resultado da execução

Preencher esta tabela com a saída real do comando abaixo antes da submissão:

```bash
docker compose exec etl python 03_carga_dw.py
```

| Indicador | Resultado |
|---|---:|
| Linhas em `dw.fato_pedido` | ____________________ |
| Linhas em `dw.fato_item_pedido` | ____________________ |
| Linhas em `dw.fato_atendimento` | ____________________ |
| Linhas em `dw.fato_avaliacao` | ____________________ |
| Asserções aprovadas | ____________________ |
| Asserções com falha | ____________________ |

## 6. Reprodução da entrega

Executar na raiz do projeto:

```bash
docker compose down -v
docker compose up -d --build
docker compose logs -f seed

docker compose exec etl python 01_extracao.py
docker compose exec etl python 02_transformacao.py
docker compose exec etl python 03_carga_dw.py
```

O carregamento deve ser feito nessa ordem. A etapa 3 depende das tabelas de
staging e das dimensões produzidas pelas etapas anteriores.

## 7. Conclusão

A Entrega 3 implementa a passagem das fontes conformadas para um esquema
estrela, preservando a diferença de granularidade entre pedido e item e
mantendo a integridade referencial. O tratamento explícito das chaves de
origem de SAC e avaliações evita o erro de associar registros a pedidos
incorretos ou inserir FKs nulas por falha de padronização.

Antes da entrega final, devem ser anexados o resultado da execução limpa do
pipeline e a consulta de `qa.execucao_assercao`, especialmente para confirmar
as contagens finais e eventuais itens órfãos.
