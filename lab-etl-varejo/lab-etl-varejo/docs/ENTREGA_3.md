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

### RDT-02 — Unificação da identidade do cliente

**Decisão:** parear clientes por CPF válido e complementar os não pareados pela
combinação de nome padronizado, cidade e UF.

**Alternativas consideradas:**

1. manter clientes de legado e e-commerce como entidades totalmente separadas;
2. parear somente por CPF, descartando o pareamento por atributos textuais;
3. parear por CPF válido e, em seguida, por nome + cidade + UF.

**Escolha e justificativa:** a primeira opção preservaria a separação, mas
impediria a análise unificada da mesma pessoa nos canais. A segunda aumenta a
possibilidade de falsos negativos porque o CPF pode estar ausente ou inválido.
A terceira usa uma chave forte quando disponível e uma regra complementar
determinística; os nomes são normalizados removendo acentos e espaços extras.

**O que se perde:** atributos textuais podem produzir uma falsa união e o CPF
inválido não é corrigido por dígito verificador. Um cliente sem CPF válido que
não tenha uma chave textual única permanece em entidades distintas.

**Registros afetados:** o cenário contém 12.605 CPFs sobrepostos; o pareamento
por CPF cobre 84,9% dos 14.850 clientes sobrepostos. Os demais registros devem
ser tratados pela combinação nome + cidade + UF ou pela dimensão de cliente
como entidades distintas.

### RDT-03 — Duplicatas internas do legado

**Decisão:** remover duplicatas exatas ou normalizadas dentro da origem legado
antes da carga da dimensão, preservando uma única representação do cliente e da
chave de origem.

**Alternativas consideradas:**

1. carregar todas as linhas de cliente sem depuração;
2. remover somente duplicatas com chave exatamente igual;
3. remover duplicatas exatas e normalizadas, combinando CPF ou regra textual
   quando a evidência permitisse.

**Escolha e justificativa:** a carga sem depuração pode deixar representações
redundantes da mesma entidade. A deduplicação controlada evita que o universo
de clientes contenha versões artificiais, mantendo uma linha candidata por
identidade. CPF normalizado, nome e localização são usados como evidência.

**O que se perde:** metadados redundantes, observações de cadastro ou variantes
de texto associados às linhas descartadas podem não ser recuperados. Há risco
limitado de agregar erroneamente duas pessoas quando os dados não são
suficientes para distinguir nomes semelhantes.

**Registros afetados:** aproximadamente 5% das linhas de cliente do legado são
duplicatas exatas ou aproximadas; esse valor corresponde a cerca de 5% da base
de clientes dessa origem.

### RDT-04 — Conformação dos status

**Decisão:** conformar os status das duas origens em `ENTREGUE`,
`CANCELADO`, `EM_TRANSITO` ou `SEPARACAO`, registrando o motivo `CLIENTE` ou
`PAGAMENTO` apenas quando conhecido.

**Alternativas consideradas:**

1. manter os status de origem como strings distintas;
2. criar classes amplas sem informar o motivo do cancelamento;
3. mapear para um vocabulário comum e separar a causa de cancelamento em
   atributo próprio.

**Escolha e justificativa:** o vocabulário comum permite comparar pedidos dos
canais sem alterar o grão. O atributo de motivo preserva parte da distinção
introduzida pelo status e-commerce `payment_declined`, sem misturar essa
informação com status operacionais.

**O que se perde:** o legado não fornece uma causa equivalente para cada
cancelamento, e o valor `canceled` deixa de representar diferenças específicas
do catálogo da origem. Os status não reconhecidos devem ser classificados como
`DESCONHECIDO` ou tratados explicitamente, não silenciosamente.

**Registros afetados:** todos os pedidos das duas origens usam status
conformado. Isso corresponde aos 410.000 pedidos do universo da carga.

### RDT-05 — Definição do valor total do pedido

**Decisão:** usar o total financeiro correto em cada origem: no legado, a soma
de mercadoria + frete; no e-commerce, o `total_amount` já representa a soma dos
itens, e o frete é tratado separadamente.

**Alternativas consideradas:**

1. carregar `VALOR_TOTAL` e `total_amount` diretamente como se fossem iguais;
2. no legado, interpretar o total como somente mercadoria;
3. reconciliar cada sistema contra os itens, interpretando a semântica própria
de cada campo.

**Escolha e justificativa:** a verificação contra os itens mostrou que o legado
bate 130.000 pedidos somando mercadoria + frete, enquanto o e-commerce bate
280.000 pedidos com itens sem frete. Portanto, `total_amount` não recebe o
frete de novo no cálculo de valor total. Essa reconcilição evita comparação
financeira distorcida entre canais.

**O que se perde:** valores agregados diretamente aos campos não terão uma
representação única do mesmo conceito do sistema se a consulta não considerar a
regra de origem. Cada métrica deve indicar se se refere a mercadoria, frete ou
total.

**Registros afetados:** 130.000 pedidos do legado e 280.000 pedidos do
e-commerce; todas as linhas do fato precisam da semântica financeira definida.

### RDT-06 — Frete negativo e desconto igual a menos um

**Decisão:** converter fretes negativos em valor absoluto, preservar a
informação de frete original para auditoria e interpretar `-1` em desconto como
ausência, não como valor monetário válido.

**Alternativas consideradas:**

1. carregar os valores negativos e ausência `-1` sem alteração;
2. excluir pedidos ou itens afetados;
3. corrigir o sinal e converter a ausência em `NULL`, registrando a quantidade
de registros corrigidos.

**Escolha e justificativa:** excluir pedidos reduziria a base, enquanto manter
os sinais distorce medidas financeiras. O valor absoluto corrige o frete e
convertê-lo em `NULL` impede que `-1` seja interpretado como desconto real.

**O que se perde:** a representação original da anomalia deixa de ser visível
nas medidas finais, embora possa ser mantida em auditoria ou logs da asserção.
Não é possível recuperar o motivo exato do valor negativo sem documentação da
fonte.

**Registros afetados:** 362 pedidos ou registros têm frete negativo no legado;
cerca de 1% dos itens apresentam desconto `-1`.

### RDT-07 — Categorias de produto

**Decisão:** padronizar texto e acentos quando inequívocos, manter a categoria
original como evidência e atribuir os casos sem conteúdo ou sem granularidade
segura ao nível `OUTROS`.

**Alternativas consideradas:**

1. usar o texto original sem normalização;
2. inventar uma hierarquia única para todos os casos ambíguos;
3. normalizar grafias resolvíveis, manter evidência da origem e preservar
   ambiguidade como `OUTROS` ou na categoria original.

**Escolha e justificativa:** variantes como `ELETRO`, `Eletro` e
`eletrodomesticos` podem ser conformadas com segurança por normalização textual.
Casos como `informatica e games` e `TV E SOM` misturam ramos ou filhos de uma
hierarquia sem regras fornecidas. Não é seguro inferir uma classificação mais
fina nesses casos.

**O que se perde:** a granularidade detalhada é reduzida para os rótulos
ambíguos. `DIVERSOS`, `OUTROS`, vazios e categorias compostas não fornecem
informação suficiente para uma atribuição de nível 1 ou 2.

**Registros afetados:** o legado tem 103 produtos sem categoria ou com
categoria vazia. Casos ambíguos representam parte dos 27 vocabulários do texto
livre e devem ser mantidos na coluna original.

### RDT-08 — Classificação das ausências

**Decisão:** classificar cada ausência pela sua semântica, converter sentinelas
concretas em `NULL` quando exigido e criar indicadores ou colunas de auditoria
para não apagar a origem da ausência.

**Alternativas consideradas:**

1. imputar valores médios ou frequentes;
2. excluir registros incompletos;
3. distinguir ausência, sentinela, categoria vazia e entrega sem registro;
   manter `NULL` quando o valor real é desconhecido.

**Escolha e justificativa:** imputação inventaria uma informação e excluí-los
reduz a população sem evidência. Manter `NULL` preserva a dúvida; a indicação
separada permite analisar a ausência como comportamento.

**O que se perde:** métricas que dependem da ausência deixam de ser calculadas
para esses registros, como prazo de entrega. No caso de `1900-01-01`, a data
real de entrega é irrecuperável; cerca de 28.808 entregas do legado são nulas
ou sentinelas equivalentes.

**Registros afetados:** 28.808 entregas nulas, 1.025 registros com a sentinela
`1900-01-01`, 103 produtos sem categoria e ausências correspondentes em
campos auxiliares.

### RDT-09 — Padronização de fusos horários

**Decisão:** preservar os timestamps do e-commerce como UTC e converte-los para
a representação local compatível com o contexto brasileiro; no legado, assumir
horário local de referência por não haver informação de fuso na origem.

**Alternativas consideradas:**

1. comparar datas sem converter nenhum timestamp;
2. atribuir o mesmo fuso a todos os registros sem verificar a origem;
3. converter e-commerce com UTC explícito e documentar a falta de fuso real no
   legado.

**Escolha e justificativa:** o e-commerce possui timestamps explicitamente em
UTC, preservados por `pd.to_datetime(..., utc=True)`. Para o legado, não há
metadado de timezone; atribuir UTC ou inventar outra região alteraria a hora
registrada sem evidência. A análise usa datas e dias de entrega calculados
depois da normalização.

**O que se perde:** não é possível reconstruir com precisão o deslocamento
histórico de cada pedido legado. Conversões podem ter ocorrido em torno da
zona brasileira, mas não há evidência suficiente para afirmar horários reais.

**Registros afetados:** pedidos, entregas e datas calculadas das duas origens;
todas as datas do fato participam da padronização temporal.

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

### RDT-14 — Atributos da ABT e prevenção de vazamento

**Decisão:** definir a população pelos pedidos realizados até o corte de
`2025-06-30` e calcular atributos somente com pedidos até essa mesma data. O
alvo é observado em uma janela posterior de 90 dias, até `2025-09-28`.

**Alternativas consideradas:**

1. usar toda a história disponível para atributos e alvo;
2. usar pedidos posteriores ao corte em atributos e ainda assim prever o alvo;
3. separar estritamente atributo, corte e janela de observação.

**Escolha e justificativa:** a alternativa 3 reproduz uma situação preditiva
realista. Os atributos incluem recência, frequência, valor, ticket médio,
prazo médio de entrega e cancelamento calculados antes ou até o corte. O alvo
só pode usar compras posteriores à data de corte na janela de 90 dias.

**O que se perde:** clientes elegíveis podem ter comportamento posterior não
incluído nos atributos. A separação reduz a informação disponível no treino,
mas evita a superestimação causada por vazamento temporal.

**Registros afetados:** todos os clientes elegíveis presentes na base, com
uma linha por cliente na ABT correta. As contagens devem ser confirmadas pela
saída do script da etapa 4.

### RDT-15 — Vazamentos introduzidos na versão de comparação

**Decisão:** manter uma segunda ABT deliberadamente vazada, contendo atributos
calculados com pedidos posteriores ao corte, para demonstrar e comparar o efeito
de vazamento temporal.

**Alternativas consideradas:**

1. criar uma única ABT sem documentação de vazamento;
2. alterar dados aleatoriamente sem conexão temporal;
3. manter uma versão vazada controlada com os campos originais e três atributos
   derivados adicionais claramente identificados.

**Escolha e justificativa:** a terceira opção permite comparar duas versões
ideais para a atividade. A versão vazada preserva os atributos originais e
adiciona `recencia_dias_vazado`, `frequencia_pedidos_vazado` e
`valor_monetario_z`, calculados com conhecimento posterior indevido ao corte.

**O que se perde:** essa versão não representa dados disponíveis no momento da
previsão e não deve ser usada como modelo válido de produção. O uso dos campos
vazados pode inflar artificialmente métricas e sugerir que eventos futuros já
são conhecidos na etapa de treino.

**Registros afetados:** o vazamento corresponde aos clientes e pedidos da
ABT usados na janela posterior ao corte, não à população alvo. A quantidade de
linhas deve permanecer igual entre as versões correta e vazada.

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
