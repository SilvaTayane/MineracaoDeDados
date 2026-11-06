# Execução do pipeline ETL — Mercatto Varejo

Este README registra a saída real de cada etapa do pipeline após a limpeza dos
resultados. A execução válida foi feita dentro da pasta que contém o
`docker-compose.yml`:

```powershell
cd C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo
```

## Erro ao executar fora da pasta do Compose

Na pasta `MineracaoDeDados`, o comando retornou:

```text
docker compose exec etl python 00_perfilamento.py
no configuration file provided: not found
```

Depois de entrar na pasta correta, a execução ocorreu na ordem exigida.

## Transcrição da execução

```text
PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> dir


    Diretório: C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo


Mode                 LastWriteTime         Length Name                                                                                                                           
----                 -------------         ------ ----                                                                                                                           
d-----        29/10/2026     21:17                dados                                                                                                                          
d-----        29/10/2026     21:17                docs                                                                                                                           
d-----        29/10/2026     21:17                etl                                                                                                                            
d-----        29/10/2026     21:17                gerador                                                                                                                        
d-----        29/10/2026     21:17                saida                                                                                                                          
d-----        29/10/2026     21:17                sql                                                                                                                            
-a----        29/10/2026     21:17            116 .env                                                                                                                           
-a----        29/10/2026     21:17            116 .env.example                                                                                                                   
-a----        29/10/2026     21:17           3367 docker-compose.yml                                                                                                             
-a----        29/10/2026     21:17           4614 README.md                                                                                                                      


PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> 
 *  History restored 

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados> 
 *  History restored 

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados> 
 *  History restored 

PS C:\Users\fabbh\OneDrive\Documento
 *  History restored 

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados> 
 *  History restored 

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados> docker compose exec etl python 00_perfilamento.py
no configuration file provided: not found
PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados> cd .\lab-etl-varejo\lab-etl-varejo\
PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> dir


    Diretório: C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo


Mode                 LastWriteTime         Length Name                                                                     
----                 -------------         ------ ----                                                                     
d-----        30/10/2026     20:29                .ows                                                                     
d-----        05/11/2026     21:57                dados                                                                    
d-----        04/11/2026     18:49                docs                                                                     
d-----        29/10/2026     21:17                etl                                                                      
d-----        05/11/2026     21:55                gerador                                                                  
d-----        30/10/2026     21:03                pdf                                                                      
d-----        05/11/2026     21:47                saida                                                                    
d-----        29/10/2026     21:17                sql                                                                      
-a----        29/10/2026     21:17            116 .env                                                                     
-a----        29/10/2026     21:17            116 .env.example                                                             
-a----        29/10/2026     21:17           3367 docker-compose.yml                                                       
-a----        29/10/2026     21:17           4614 README.md                                                                


PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 00_perfilamento.py

========================================================================
FONTE 1 — MySQL · loja_legado
========================================================================

--- legado.CLIENTES (47250 linhas) ---
             linhas  nulos  %_nulos  vazios  distintos  min      max    media  negativos    tipo                                                mais_frequentes  tam_min  tam_max
coluna                                                                                 
ID_CLIENTE    47250      0      0.0       0      47250  1.0  47250.0  23625.5        0.0   int64                                                            NaN      NaN      NaN
NOME          47250      0      0.0       0      40813  NaN      NaN      NaN        NaN  object            CARLA COSTA MARTINS (5); ANA NASCIMENTO MACHADO (5); HELENA MOREIRA MOREIRA (5)     13.0     32.0
CPF           47250      0      0.0    4423      41955  NaN      NaN      NaN        NaN  object                 (4423); 842.466.587-23 (2); 875.643.768-48 (2)      0.0     14.0
EMAIL         47250      0      0.0       0      45000  NaN      NaN      NaN        NaN  object  mariana44974@exemplo.com.br (2); helena23@exemplo.com.br (2); marcia18@exemplo.com.br (2)     20.0     30.0
DT_CADASTRO   47250      0      0.0       0       1095  NaN      NaN      NaN        NaN  object              2023-04-28 (66); 2024-06-29 (64); 2023-05-07 (64)     10.0     10.0
CIDADE        47250      0      0.0       0         24  NaN      NaN      NaN        NaN  object             Salvador (2174); Curitiba (2072); São Paulo (2065)      3.0     14.0
UF            47250      0      0.0       0         16  NaN      NaN      NaN        NaN  object                                MT (8227); SP (6151); PR (4180)      2.0      2.0
TELEFONE      47250      0      0.0       0      45000  NaN      NaN      NaN        NaN  object  (98) 96480-1892 (2); (16) 92350-6536 (2); (40) 99109-5422 (2)     15.0     15.0

--- legado.PRODUTOS (3000 linhas) ---
              linhas  nulos  %_nulos  vazios  distintos    min     max    media  negativos     tipo                                  mais_frequentes  tam_min  tam_max
coluna                                                                   
ID_PRODUTO      3000      0      0.0       0       3000   1.00  3000.0  1500.50        0.0    int64                                              NaN      NaN      NaN
DESCRICAO       3000      0      0.0       0       2996    NaN     NaN      NaN        NaN   object  DESKTOP NORDIC 270 (2); PARAFUSADEIRA BRAVA 396 (2); MESA AURORA 514 (2)     12.0     27.0
CATEGORIA       3000      0      0.0     103         27    NaN     NaN      NaN        NaN   object      FERRAMENTAS (138); CASA (134); MOVEIS (131)      0.0     24.0
PRECO_TABELA    3000      0      0.0       0       2934  37.32  3497.3   380.07        0.0  float64                                              NaN      NaN      NaN
ATIVO           3000      0      0.0       0          2    NaN     NaN      NaN        NaN   object                                S (2660); N (340)      1.0      1.0

--- legado.PEDIDOS (130000 linhas) ---
             linhas  nulos  %_nulos  vazios  distintos    min        max     media  negativos            tipo                                                mais_frequentes  tam_min  tam_max
coluna                                                                                 
ID_PEDIDO    130000      0     0.00       0     130000   1.00  130000.00  65000.50        0.0           int64                                                            NaN      NaN      NaN
ID_CLIENTE   130000      0     0.00       0      44253   1.00   47250.00  23667.83        0.0           int64                                                            NaN      NaN      NaN
DT_PEDIDO    130000      0     0.00       0     121077    NaN        NaN       NaN        NaN  datetime64[ns]     2023-05-01 11:32:00 (5); 2024-06-18 21:15:00 (4); 2023-08-13 20:03:00 (4)     19.0     19.0
DT_ENTREGA   130000  28808    22.16       0      95057    NaN        NaN       NaN        NaN  datetime64[ns]  1900-01-01 00:00:00 (1025); 2025-03-15 11:34:00 (3); 2023-01-19 16:07:00 (3)     19.0     19.0
STATUS       130000      0     0.00       0          4    NaN        NaN       NaN        NaN          object       ENTREGUE (101192); CANCELADO (15774); EM TRANSITO (7798)      8.0     11.0
VALOR_TOTAL  130000      0     0.00       0     112745   4.78   14810.98   2162.19        0.0         float64                                                            NaN      NaN      NaN
VALOR_FRETE  130000      0     0.00       0       9258 -88.78      89.00     44.31      362.0         float64                                                            NaN      NaN      NaN
CANAL        130000      0     0.00       0          3    NaN        NaN       NaN        NaN          object                 LOJA (58392); SITE (45368); TELEVENDAS (26240)      4.0     10.0

--- legado.ITENS_PEDIDO (200000 linhas) ---
             linhas  nulos  %_nulos  vazios  distintos    min        max      media  negativos     tipo
coluna                                                                                                 
ID_ITEM      200000      0      0.0       0     200000   1.00  200000.00  100000.50          0    int64
ID_PEDIDO    200000      0      0.0       0      66493   1.00   66493.00   33273.12          0    int64
ID_PRODUTO   200000      0      0.0       0       3000   1.00    3000.00    1499.08          0    int64
QTD          200000      0      0.0       0          3   1.00       3.00       2.00          0    int64
VL_UNITARIO  200000      0      0.0       0      73258  34.37    3670.09     373.69          0  float64
VL_DESCONTO  200000      0      0.0       0      20528  -1.00    1280.88      44.37       2009  float64

· distribuição de STATUS:
     STATUS      n
   ENTREGUE 101192
  CANCELADO  15774
EM TRANSITO   7798
  SEPARACAO   5236

· valores distintos de CATEGORIA (texto livre):
               CATEGORIA   n
        ELETRODOMÉSTICOS 214
             Informática 211
                  ELETRO 209
             FERRAMENTAS 138
                    CASA 134
                  MOVEIS 131
        Casa e decoracao 130
                  OUTROS 121
                 ESPORTE 118
             Televisores 118
                DIVERSOS 116
             AUDIO/VIDEO 115
               TELEFONIA 113
     informatica e games 112
                TV E SOM 111
       Eletro-domesticos 110
               Celulares 109
      CELULAR/SMARTPHONE 107
                   GAMES 104
                         103
        Esportes e lazer 103
Ferramentas e construcao  92
        Games e consoles  92
                    INFO  89

· formatos de CPF encontrados:
        formato     n
        ausente  4423
    com máscara 40416
somente dígitos  2411

>> gravado em /saida/perfilamento_legado.md

========================================================================
FONTE 2 — PostgreSQL · shop
========================================================================

--- shop.customer (85000 linhas) ---
             linhas  nulos  %_nulos  vazios  distintos  min      max    media  negativos                 tipo                                                                     mais_frequentes  tam_min  tam_max
coluna                                                                                                      
customer_id   85000      0     0.00       0      85000  1.0  85000.0  42500.5        0.0                int64                                                                                 NaN      NaN      NaN
full_name     85000      0     0.00       0      66802  NaN      NaN      NaN        NaN               object        Antônio Oliveira Soares (6); Patrícia Fonseca Nascimento (6); Thiago Gonçalves Teixeira (6)     13.0     32.0
tax_id        85000   6855     8.06       0      78142  NaN      NaN      NaN        NaN               object                                   86527372230 (2); 84390192973 (2); 66928971061 (2)     11.0     11.0
email         85000      0     0.00       0      85000  NaN      NaN      NaN        NaN               object          cliente84999@correio.com.br (1); cliente0@correio.com.br (1); cliente1@correio.com.br (1)     23.0     27.0
created_at    85000      0     0.00       0       1095  NaN      NaN      NaN        NaN  datetime64[ns, UTC]  2023-12-07 03:00:00+00:00 (105); 2025-05-09 03:00:00+00:00 (105); 2024-07-04 03:00:00+00:00 (101)     25.0     25.0
city          85000      0     0.00       0         23  NaN      NaN      NaN        NaN               object                                   Fortaleza (3805); Goiânia (3786); Curitiba (3773)      5.0     14.0
state         85000      0     0.00       0         16  NaN      NaN      NaN        NaN               object                                                   MT (14630); SP (11079); PR (7529)      2.0      2.0
phone         85000      0     0.00       0      84958  NaN      NaN      NaN        NaN               object                          +5566982575873 (2); +5566947313261 (2); +5566927372761 (2)     14.0     14.0

--- shop.product (12000 linhas) ---
             linhas  nulos  %_nulos  vazios  distintos    min     max    media  negativos     tipo                             mais_frequentes  tam_min  tam_max
coluna                                                              
product_id    12000      0      0.0       0      12000      1   12000  6000.50        0.0    int64                                         NaN      NaN      NaN
sku           12000      0      0.0       0      12000    NaN     NaN      NaN        NaN   object                        SKU-111983 (1); SKU-111982 (1); SKU-111981 (1)     10.0     10.0
title         12000      0      0.0       0      11923    NaN     NaN      NaN        NaN   object  Desktop Nordic 610 (2);Jogo Vertex 915 (2); Soundbar Veloce 136 (2)     12.0     27.0
category_id   12000      0      0.0       0         15      2      21    11.55        0.0    int64                                         NaN      NaN      NaN
list_price    12000      0      0.0       0      11069  42.93  5477.8   419.58        0.0  float64                                         NaN      NaN      NaN
active        12000      0      0.0       0          2  False    True     0.92        0.0     bool                                         NaN      NaN      NaN

--- shop.orders (200000 linhas) ---
                linhas  nulos  %_nulos  vazios  distintos    min        max      media  negativos                 tipo                                                                        mais_frequentes  tam_min  tam_max
coluna                                                                                                         
order_id        200000      0     0.00       0     200000   1.00  200000.00  100000.50        0.0                int64                                                                                    NaN      NaN      NaN
customer_id     200000      0     0.00       0      76898   1.00   85000.00   42474.58        0.0                int64                                                                                    NaN      NaN      NaN
placed_at       200000      0     0.00       0     187778    NaN        NaN        NaN        NaN  datetime64[ns, UTC]  2023-08-11 23:10:00+00:00 (4); 2025-12-24 19:33:00+00:00 (4); 2023-04-29 21:43:00+00:00 (4)     25.0     25.0
delivered_at    200000  51877    25.94       0     141491    NaN        NaN        NaN        NaN  datetime64[ns, UTC]  2023-02-02 16:31:00+00:00 (4); 2024-02-20 17:18:00+00:00 (4); 2023-11-29 09:44:00+00:00 (4)     25.0     25.0
status          200000      0     0.00       0          5    NaN        NaN        NaN        NaN               object                                  delivered (148123); shipped (16064); canceled (15991)      7.0     16.0
total_amount    200000      0     0.00       0     168163  37.37   29403.87    2626.06        0.0              float64                                                                                    NaN      NaN      NaN
freight_amount  200000      0     0.00       0       8489 -78.86      79.00      39.22      612.0              float64                                                                                    NaN      NaN      NaN
channel         200000      0     0.00       0          3    NaN        NaN        NaN        NaN               object                                          web (83722); app (80294); marketplace (35984)      3.0     11.0

--- shop.order_item (200000 linhas) ---
               linhas  nulos  %_nulos  vazios  distintos    min        max      media  negativos     tipo
coluna                                                                                                   
order_item_id  200000      0      0.0       0     200000   1.00  984845.00  101328.10          0    int64
order_id       200000      0      0.0       0      57499   1.00  289902.00   29051.63          0    int64
product_id     200000      0      0.0       0      12000   1.00   12000.00    6001.82          0    int64
quantity       200000      0      0.0       0          3   1.00       3.00       2.00          0    int64
unit_price     200000      0      0.0       0      75958  39.13    5617.33     403.57          0  float64
discount       200000      0      0.0       0      25578   0.00    2050.62      60.52          0  float64

· distribuição de status:
          status      n
       delivered 207204
        canceled  22413
         shipped  22375
      processing  14018
payment_declined  13990

· taxonomia de categorias:
 category_id                    name              pai
           1        Eletrodomésticos             None
           2         Eletroportáteis Eletrodomésticos
           3            Linha Branca Eletrodomésticos
           4             Informática             None
           5               Notebooks      Informática
           6             Periféricos      Informática
           7             Componentes      Informática
           8                   Games             None
           9                Consoles            Games
          10                   Jogos            Games
          11               Telefonia             None
          12             Smartphones        Telefonia
          13 Acessórios de Telefonia        Telefonia
          14        Casa e Decoração             None
          15                  Móveis Casa e Decoração
          16      Cama, Mesa e Banho Casa e Decoração
          17         Esporte e Lazer             None
          18             Ferramentas             None
          19              Áudio e TV             None
          20             Televisores       Áudio e TV
          21                   Áudio       Áudio e TV

>> gravado em /saida/perfilamento_ecommerce.md

========================================================================
FONTE 3 — CSV · atendimentos_sac.csv
========================================================================
Dica: tente ler com encoding='utf-8' e observe o erro. Depois leia certo.

--- SAC (96140 linhas) ---
                       linhas  nulos  %_nulos  vazios  distintos     mais_frequentes  tam_min  tam_max    tipo
coluna                                              
protocolo               96140      0     0.00       0      95000                               P2023032129 (2); P2023068611(2); P2023042405 (2)       11       11  object
origem_sistema          96140      0     0.00       0          2                                                    ECOM (59613); LEGADO (36527)        4        6  object
id_pedido_origem        96140      0     0.00       0      78808                                                 87794 (6);15665 (6); 27133 (5)        1        6  object
cpf_cliente             96140      0     0.00       0      75982                      044.318.425-94 (7); 924.181.794-29 (7); 219.218.326-73 (7)       11       14  object
data_abertura           96140      0     0.00       0       1095                            15/10/2024 (117); 08/11/2023 (116); 27/07/2023 (113)       10       10  object
data_fechamento         96140   5856     6.09       0       1097                            27/07/2023 (113); 07/05/2024 (109); 07/11/2023 (108)       10       10  object
canal                   96140      0     0.00       0          6                                   CHAT (16228); telefone (16120); EMAIL (16084)        4        8  object
motivo                  96140      0     0.00       0         36  Produto avariado (5494); ATRASO NA ENTREGA (5367); Produto não recebido (5357)        5       64  object
nota_satisfacao         96140   8682     9.03       0          6                                                 3 (16982);2 (16974); 1 (16950)        1        1  object
tempo_resolucao_horas   96140      0     0.00       0       6744                                                 9,54 (56);8,63 (56); 9,70 (55)        4        6  object

· origem_sistema: {'ECOM': 59613, 'LEGADO': 36527}
· linhas idênticas repetidas: 1140
· notas fora do domínio 1..5: 2830
· campos com quebra de linha interna: 1377
· motivos distintos (texto livre): 36

>> gravado em /saida/perfilamento_sac.md

========================================================================
FONTE 4 — NDJSON · avaliacoes_marketplace.json
========================================================================
registros: 160000

· presença de cada chave de primeiro nível:
    review_id              160000 (100.0%)
    order                  160000 (100.0%)
    product                160000 (100.0%)
    submitted_at           160000 (100.0%)
    rating                 155169 ( 97.0%)
    verified_purchase      144269 ( 90.2%)
    title                  135736 ( 84.8%)
    comment                112186 ( 70.1%)
    helpful_votes           87871 ( 54.9%)

· tipo do campo rating: {'int': 139061, 'NoneType': 4831, 'str': 16108}
· prefixo de order.ref: {'ECOM': 119984, 'LEG': 40016}
· submitted_at com fuso: 128085 | sem fuso: 31915

========================================================================
PRÓXIMO PASSO
========================================================================

Com este retrato em mãos, o Relatório de Diagnóstico deve responder:

  1. Quais campos são candidatos a chave de junção entre as fontes?
     Qual a cobertura real de cada candidato?
  2. Onde há heterogeneidade SEMÂNTICA — o mesmo rótulo com significados
     diferentes? Liste ao menos três casos com evidência numérica.
  3. VALOR_TOTAL no legado e total_amount no e-commerce medem a mesma coisa?
     Prove sua resposta comparando com a soma dos itens.
  4. Quais anomalias você consegue quantificar agora, e quais só aparecerão
     depois da integração?

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 01_extracao.py
stg.legado_clientes: 47250 linhas
stg.legado_produtos: 3000 linhas
stg.legado_pedidos: 130000 linhas
stg.legado_itens_pedido: 397086 linhas
stg.ecom_customer: 85000 linhas
stg.ecom_product: 12000 linhas
stg.ecom_orders: 280000 linhas
stg.ecom_order_item: 995367 linhas
stg.atendimentos_sac: 96140 linhas
stg.avaliacoes_marketplace: 160000 linhas

=== asserções · 01_extracao ==============================
  [OK  ] linhas legado.PEDIDOS  obtido=130000.0  esperado = 130000
  [OK  ] protocolo do SAC       obtido=0  esperado = 0 nulos
  [OK  ] review_id              obtido=0  esperado = 0 duplicados
  3 asserções, 0 falha(s)

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 02_transformacao.py
   
=== asserções · 02_transformacao ==============================
  [OK  ] dim_cliente sem CPF duplicado    obtido=0.0  esperado = 0
  [OK  ] origem da dimensão cliente       obtido=0  esperado todos em ['AMBOS', 'ECOM', 'LEGADO']
  [OK  ] status conformado por pedido     obtido=9.0  esperado [0, 9]
  [OK  ] valor legado em perspectiva      obtido=2162.191977923077  esperado [0, 100000]
  [OK  ] valor e-commerce em perspectiva  obtido=2624.4967855357145  esperado [0, 100000]
  [OK  ] categorias de produto            obtido=3000.0  esperado [1, 3000]
  [OK  ] entregas anteriores ao pedido    obtido=1800.0  esperado [0, 10000]
  [OK  ] prazos e-commerce                obtido=280000.0  esperado [1, 280000]
  [OK  ] atendimentos e avaliações        obtido=256140.0  esperado [2, 256140]
  9 asserções, 0 falha(s)

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 03_carga_dw.py
dim_tempo: 1217 datas
dw.fato_pedido: 410000 linhas
dw.fato_item_pedido: 1371876 linhas
/etl/03_carga_dw.py:313: UserWarning: Parsing dates in %d/%m/%Y format when dayfirst=False (the default) was specified. Pass `dayfirst=True` or specify a format to silence this warning.
  sac["data_abertura_sk"] = pd.to_datetime(sac["data_abertura"], errors="coerce").dt.date
/etl/03_carga_dw.py:314: UserWarning: Parsing dates in %d/%m/%Y format when dayfirst=False (the default) was specified. Pass `dayfirst=True` or specify a format to silence this warning.
  sac["data_fechamento_sk"] = pd.to_datetime(sac["data_fechamento"], errors="coerce").dt.date
/etl/qualidade/assercoes.py:90: FutureWarning: Calling int on a single element Series is deprecated and will raise a TypeError in the future. Use int(ser.iloc[0]) instead
  orfaos = int((~filhos.isin(pais)).sum())

=== asserções · 03_carga_dw ==============================
  [OK  ] dimensões carregadas                obtido=1.0  esperado = 1
  [OK  ] quantidade de pedidos no DW         obtido=410000.0  esperado = 410000
  [OK  ] reconciliação financeira legado     obtido=0.0  esperado [0, 0.1]
  [OK  ] reconciliação financeira ecommerce  obtido=0.0  esperado [0, 0.1]
  [FALHA] FK órfã em fato_pedido              obtido=409999  esperado = 0 órfãos
           -> não pode haver cliente desaparecido
  [FALHA] dias de entrega negativos           obtido=2458.0  esperado = 0
           -> qualquer entrega antes do pedido deve ser tratada e normalizada
  6 asserções, 2 falha(s)

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 04_abt.py --correta
alvo: 98580 clientes | taxa de recompra = 0.209
abt.recompra_90d: 98580 linhas, 9 colunas

=== asserções · 04_abt_correta ==============================
  [OK  ] taxa do alvo             obtido=0.2086021505376344  esperado [0.02, 0.6]
  [OK  ] cliente_sk no alvo       obtido=0  esperado = 0 duplicados
  [OK  ] junção alvo x atributos  obtido=98580  esperado <= 98580
  3 asserções, 0 falha(s)

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 04_abt.py --vazamento
alvo: 98580 clientes | taxa de recompra = 0.209
abt.recompra_90d_vazamento: 98580 linhas, 12 colunas

=== asserções · 04_abt_vazamento ==============================
  [OK  ] taxa do alvo             obtido=0.2086021505376344  esperado [0.02, 0.6]
  [OK  ] cliente_sk no alvo       obtido=0  esperado = 0 duplicados
  [OK  ] junção alvo x atributos  obtido=98580  esperado <= 98580
  3 asserções, 0 falha(s)

PS C:\Users\fabbh\OneDrive\Documentos\GitHub\MineracaoDeDados\lab-etl-varejo\lab-etl-varejo> docker compose exec etl python 05_exportar_orange.py
exportando para o Orange:
  /saida/abt_recompra_correta.csv  (98580 linhas, 9 colunas)
     alvo: 0.209 de positivos
  /saida/abt_recompra_vazamento.csv  (98580 linhas, 12 colunas)
     alvo: 0.209 de positivos

No Orange, monte o mesmo fluxo para os dois arquivos:

    File -> Data Sampler (70/30, estratificado) -> Naive Bayes -> Test & Score
                                               -> Logistic Regression
                                               -> Tree
            Test & Score -> Confusion Matrix
                         -> ROC Analysis

Use o MESMO conjunto de teste e as MESMAS configurações nos dois. A única
diferença entre os fluxos deve ser o arquivo de entrada.
```

