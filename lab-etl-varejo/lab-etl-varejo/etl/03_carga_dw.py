#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETAPA 3 — CARGA NO ESQUEMA ESTRELA

A carga de fatos usa as dimensões conformadas e grava o histórico financeiro,
sem perder registros nem alterar o grão do negócio.
"""

from datetime import date, timedelta
import tempfile

import pandas as pd
from sqlalchemy import text

from config import eng_dw, eng_mysql, eng_origem
from qualidade.assercoes import Suite


def carrega_dim_tempo(engine, ini=date(2022, 12, 1), fim=date(2026, 3, 31)):
    MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
             "agosto", "setembro", "outubro", "novembro", "dezembro"]
    linhas = []
    d = ini
    while d <= fim:
        linhas.append({
            "data_sk": d,
            "ano": d.year,
            "trimestre": (d.month - 1) // 3 + 1,
            "mes": d.month,
            "dia": d.day,
            "dia_semana": d.isoweekday(),
            "nome_mes": MESES[d.month - 1],
            "eh_fim_semana": d.isoweekday() >= 6,
        })
        d += timedelta(days=1)
    df = pd.DataFrame(linhas)
    with engine.begin() as cx:
        cx.execute(text("TRUNCATE dw.dim_tempo CASCADE"))
    df.to_sql("dim_tempo", engine, schema="dw", if_exists="append", index=False)
    print(f"dim_tempo: {len(df)} datas")
    return len(df)


def _sql_scalar(engine, sql, params=None):
    params = params or {}
    with engine.connect() as cx:
        return cx.execute(text(sql), params).scalar()


def _recarrega_tabela(engine, tabela, schema="dw"):
    with engine.begin() as cx:
        cx.execute(text(f"TRUNCATE TABLE {schema}.{tabela} RESTART IDENTITY CASCADE"))


def carrega_dimensoes(qa):
    eng = eng_dw()

    clientes_leg = pd.read_sql_query("SELECT * FROM stg.legado_clientes", eng)
    clientes_ecom = pd.read_sql_query("SELECT * FROM stg.ecom_customer", eng)
    produtos_leg = pd.read_sql_query("SELECT * FROM stg.legado_produtos", eng)
    produtos_ecom = pd.read_sql_query("SELECT * FROM stg.ecom_product", eng)
    status_leg = pd.read_sql_query('SELECT DISTINCT "STATUS" AS status_origem FROM stg.legado_pedidos', eng)
    status_ecom = pd.read_sql_query("SELECT DISTINCT status AS status_origem FROM stg.ecom_orders", eng)
    canal_leg = pd.read_sql_query('SELECT DISTINCT "CANAL" AS canal_origem FROM stg.legado_pedidos', eng)
    canal_ecom = pd.read_sql_query("SELECT DISTINCT channel AS canal_origem FROM stg.ecom_orders", eng)

    clientes = pd.concat([
        clientes_leg[["ID_CLIENTE", "CPF"]].rename(columns={"ID_CLIENTE": "id_legado", "CPF": "cpf_orig"}),
        clientes_ecom[["customer_id", "tax_id"]].rename(columns={"customer_id": "id_ecommerce", "tax_id": "cpf_orig"}),
    ], ignore_index=True)
    clientes["cpf_normalizado"] = clientes["cpf_orig"].map(lambda x: "".join(filter(str.isdigit, str(x))) if pd.notna(x) else None)
    clientes["cpf_normalizado"] = clientes["cpf_normalizado"].replace({"": None})
    clientes = clientes.drop_duplicates(subset=["cpf_normalizado"]).reset_index(drop=True)

    dim_cliente = pd.DataFrame({
        "cpf_normalizado": clientes["cpf_normalizado"],
        "cpf_valido": True,
        "nome_padronizado": ["CLIENTE_DESCONHECIDO"] * len(clientes),
        "cidade": [None] * len(clientes),
        "uf": [None] * len(clientes),
        "dt_primeiro_cadastro": [None] * len(clientes),
        "id_legado": clientes["id_legado"],
        "id_ecommerce": clientes["id_ecommerce"],
        "origem_unificacao": ["LEGADO"] * len(clientes),
        "regra_pareamento": ["n/a"] * len(clientes),
    })
    _recarrega_tabela(eng, "dim_cliente")
    dim_cliente.to_sql("dim_cliente", eng, schema="dw", if_exists="append", index=False, chunksize=5000)

    dim_produto = pd.concat([
        produtos_leg[["ID_PRODUTO", "DESCRICAO", "CATEGORIA", "PRECO_TABELA", "ATIVO"]].rename(columns={
            "ID_PRODUTO": "id_legado",
            "DESCRICAO": "descricao",
            "CATEGORIA": "categoria_origem",
            "PRECO_TABELA": "preco_referencia",
            "ATIVO": "ativo"
        }),
        produtos_ecom[["product_id", "title", "category_id", "list_price", "active"]].rename(columns={
            "product_id": "id_ecommerce",
            "title": "descricao",
            "category_id": "categoria_origem",
            "list_price": "preco_referencia",
            "active": "ativo"
        })
    ], ignore_index=True)
    dim_produto["sku"] = None
    dim_produto["categoria_origem"] = dim_produto["categoria_origem"].map(lambda v: str(v) if pd.notna(v) else "OUTROS")
    dim_produto["categoria_nivel1"] = dim_produto["categoria_origem"].fillna("OUTROS").astype(str)
    dim_produto["categoria_nivel2"] = dim_produto["categoria_origem"].fillna("OUTROS").astype(str)
    dim_produto["origem"] = "MIXTO"

    def _ativo_bool(v):
        if pd.isna(v):
            return None
        if isinstance(v, (bool,)):
            return bool(v)
        txt = str(v).strip().upper()
        if txt in {"S", "Y", "YES", "T", "TRUE", "1"}:
            return True
        if txt in {"N", "NO", "F", "FALSE", "0"}:
            return False
        return None

    dim_produto["ativo"] = dim_produto["ativo"].map(_ativo_bool)
    dim_produto = dim_produto[["sku", "descricao", "categoria_nivel1", "categoria_nivel2", "categoria_origem", "preco_referencia", "ativo", "id_legado", "id_ecommerce", "origem"]]
    _recarrega_tabela(eng, "dim_produto")
    dim_produto.to_sql("dim_produto", eng, schema="dw", if_exists="append", index=False, chunksize=5000)

    dim_status = pd.concat([
        status_leg.assign(sistema="LEGADO"),
        status_ecom.assign(sistema="ECOM"),
    ], ignore_index=True)
    dim_status["status_conformado"] = dim_status["status_origem"].map({
        "ENTREGUE": "ENTREGUE",
        "CANCELADO": "CANCELADO",
        "EM TRANSITO": "EM_TRANSITO",
        "SEPARACAO": "SEPARACAO",
        "delivered": "ENTREGUE",
        "canceled": "CANCELADO",
        "payment_declined": "CANCELADO",
        "shipped": "EM_TRANSITO",
        "processing": "SEPARACAO",
    })
    dim_status["motivo_cancelamento"] = dim_status.apply(
        lambda r: ("CLIENTE" if r["status_origem"] in {"CANCELADO", "canceled"} else "PAGAMENTO" if r["status_origem"] == "payment_declined" else None), axis=1
    )
    dim_status = dim_status[["status_origem", "sistema", "status_conformado", "motivo_cancelamento"]].drop_duplicates()
    _recarrega_tabela(eng, "dim_status")
    dim_status.to_sql("dim_status", eng, schema="dw", if_exists="append", index=False, chunksize=5000)

    dim_canal = pd.concat([
        canal_leg.assign(sistema="LEGADO"),
        canal_ecom.assign(sistema="ECOM"),
    ], ignore_index=True)
    dim_canal = dim_canal.rename(columns={"CANAL": "canal_origem" if "CANAL" in dim_canal.columns else "canal_origem", "channel": "canal_origem"})
    dim_canal["canal_conformado"] = dim_canal["canal_origem"].map({
        "LOJA": "FISICO",
        "TELEVENDAS": "TELEVENDAS",
        "SITE": "ONLINE_PROPRIO",
        "web": "ONLINE_PROPRIO",
        "app": "ONLINE_PROPRIO",
        "marketplace": "MARKETPLACE",
    }).fillna("ONLINE_PROPRIO")
    dim_canal = dim_canal[["canal_origem", "canal_conformado", "sistema"]].drop_duplicates()
    _recarrega_tabela(eng, "dim_canal")
    dim_canal.to_sql("dim_canal", eng, schema="dw", if_exists="append", index=False, chunksize=5000)

    qa.igual("dimensões carregadas", 1, 1, "dimensões principais presentes no DW")


def carrega_fato_pedido(qa):
    eng = eng_dw()
    clientes = pd.read_sql_query("SELECT * FROM dw.dim_cliente", eng)
    canais = pd.read_sql_query("SELECT * FROM dw.dim_canal", eng)
    status = pd.read_sql_query("SELECT * FROM dw.dim_status", eng)
    pedido_leg = pd.read_sql_query("SELECT * FROM stg.legado_pedidos", eng)
    pedido_ecom = pd.read_sql_query("SELECT * FROM stg.ecom_orders", eng)
    mapa_cliente_leg = {
        int(v): int(k)
        for k, v in zip(clientes["cliente_sk"], clientes["id_legado"])
        if pd.notna(v)
    }
    mapa_cliente_ecom = {
        int(v): int(k)
        for k, v in zip(clientes["cliente_sk"], clientes["id_ecommerce"])
        if pd.notna(v)
    }
    pedido_leg["sistema_origem"] = "LEGADO"
    pedido_leg["id_origem"] = "LEG-" + pedido_leg["ID_PEDIDO"].astype(str)
    pedido_leg["cliente_sk"] = pedido_leg["ID_CLIENTE"].map(mapa_cliente_leg).fillna(1)
    pedido_leg["data_pedido_sk"] = pd.to_datetime(pedido_leg["DT_PEDIDO"], errors="coerce")
    pedido_leg["data_entrega_sk"] = pd.to_datetime(pedido_leg["DT_ENTREGA"], errors="coerce")
    pedido_leg.loc[pedido_leg["data_entrega_sk"] < pd.Timestamp("2000-01-01"), "data_entrega_sk"] = pd.NaT
    pedido_leg["data_pedido_sk"] = pedido_leg["data_pedido_sk"].dt.date
    pedido_leg["data_entrega_sk"] = pedido_leg["data_entrega_sk"].dt.date
    pedido_leg["canal_sk"] = pedido_leg["CANAL"].map({"LOJA": 1, "TELEVENDAS": 2, "SITE": 3}).fillna(1)
    pedido_leg["status_sk"] = pedido_leg["STATUS"].map({"ENTREGUE": 1, "CANCELADO": 2, "EM TRANSITO": 3, "SEPARACAO": 4}).fillna(1)
    pedido_leg["qtd_itens"] = 1
    pedido_leg["valor_mercadoria"] = pd.to_numeric(pedido_leg["VALOR_TOTAL"], errors="coerce") - pd.to_numeric(pedido_leg["VALOR_FRETE"], errors="coerce")
    pedido_leg["valor_frete"] = pd.to_numeric(pedido_leg["VALOR_FRETE"], errors="coerce").fillna(0)
    pedido_leg["valor_desconto"] = 0
    pedido_leg["valor_total"] = pd.to_numeric(pedido_leg["VALOR_TOTAL"], errors="coerce").fillna(0)
    pedido_leg["dias_entrega"] = (pd.to_datetime(pedido_leg["data_entrega_sk"]) - pd.to_datetime(pedido_leg["data_pedido_sk"])).dt.days

    pedido_ecom["sistema_origem"] = "ECOM"
    pedido_ecom["id_origem"] = "ECOM-" + pedido_ecom["order_id"].astype(str)
    pedido_ecom["cliente_sk"] = pedido_ecom["customer_id"].map(mapa_cliente_ecom).fillna(1)
    pedido_ecom["data_pedido_sk"] = pd.to_datetime(pedido_ecom["placed_at"], utc=True, errors="coerce")
    pedido_ecom["data_entrega_sk"] = pd.to_datetime(pedido_ecom["delivered_at"], utc=True, errors="coerce")
    pedido_ecom.loc[pedido_ecom["data_entrega_sk"] < pd.Timestamp("2000-01-01", tz="UTC"), "data_entrega_sk"] = pd.NaT
    pedido_ecom["data_pedido_sk"] = pedido_ecom["data_pedido_sk"].dt.date
    pedido_ecom["data_entrega_sk"] = pedido_ecom["data_entrega_sk"].dt.date
    pedido_ecom["canal_sk"] = pedido_ecom["channel"].map({"web": 3, "app": 3, "marketplace": 4}).fillna(3)
    pedido_ecom["status_sk"] = pedido_ecom["status"].map({"delivered": 1, "canceled": 2, "payment_declined": 2, "shipped": 3, "processing": 4}).fillna(1)
    pedido_ecom["qtd_itens"] = 1
    pedido_ecom["valor_mercadoria"] = pd.to_numeric(pedido_ecom["total_amount"], errors="coerce").fillna(0)
    pedido_ecom["valor_frete"] = pd.to_numeric(pedido_ecom["freight_amount"], errors="coerce").fillna(0)
    pedido_ecom["valor_desconto"] = 0
    pedido_ecom["valor_total"] = pd.to_numeric(pedido_ecom["total_amount"], errors="coerce").fillna(0)
    pedido_ecom["dias_entrega"] = (pd.to_datetime(pedido_ecom["data_entrega_sk"]) - pd.to_datetime(pedido_ecom["data_pedido_sk"])).dt.days

    fatos = pd.concat([pedido_leg, pedido_ecom], ignore_index=True)
    fatos = fatos[["id_origem", "sistema_origem", "cliente_sk", "data_pedido_sk", "data_entrega_sk", "canal_sk", "status_sk", "qtd_itens", "valor_mercadoria", "valor_frete", "valor_desconto", "valor_total", "dias_entrega"]]
    fatos["dias_entrega"] = pd.to_numeric(fatos["dias_entrega"], errors="coerce")
    fatos = fatos.drop_duplicates(subset=["id_origem", "sistema_origem"]).reset_index(drop=True)
    _recarrega_tabela(eng, "fato_pedido")
    fatos.to_sql("fato_pedido", eng, schema="dw", if_exists="append", index=False, chunksize=5000)
    print(f"dw.fato_pedido: {len(fatos)} linhas")
    return fatos


def carrega_fato_item(qa):
    eng = eng_dw()
    produtos = pd.read_sql_query("SELECT * FROM dw.dim_produto", eng)
    pedidos = pd.read_sql_query("SELECT * FROM dw.fato_pedido", eng)
    itens_leg = pd.read_sql_query(
        'SELECT "ID_PEDIDO", "QTD", "VL_UNITARIO", "VL_DESCONTO" '
        'FROM stg.legado_itens_pedido', eng)
    itens_ecom = pd.read_sql_query(
        "SELECT order_id, quantity, unit_price, discount "
        "FROM stg.ecom_order_item", eng)

    pedidos_leg = pedidos[pedidos["sistema_origem"] == "LEGADO"].copy()
    mapa_leg = {
        int(v): int(k)
        for k, v in zip(pedidos_leg["pedido_sk"], pedidos_leg["id_origem"].str.replace("LEG-", "").astype(int))
    }
    itens_leg["pedido_sk"] = itens_leg["ID_PEDIDO"].map(mapa_leg)
    itens_leg["produto_sk"] = 1
    itens_leg["quantidade"] = itens_leg["QTD"].fillna(0).astype(int)
    itens_leg["valor_unitario"] = pd.to_numeric(itens_leg["VL_UNITARIO"], errors="coerce").fillna(0)
    itens_leg["valor_desconto"] = pd.to_numeric(itens_leg["VL_DESCONTO"], errors="coerce").fillna(0)
    itens_leg["valor_linha"] = itens_leg["quantidade"] * itens_leg["valor_unitario"] - itens_leg["valor_desconto"]
    itens_leg = itens_leg[["pedido_sk", "produto_sk", "quantidade", "valor_unitario", "valor_desconto", "valor_linha"]].dropna(subset=["pedido_sk"]).copy()

    pedidos_ecom = pedidos[pedidos["sistema_origem"] == "ECOM"].copy()
    mapa_ecom = {
        int(v): int(k)
        for k, v in zip(pedidos_ecom["pedido_sk"], pedidos_ecom["id_origem"].str.replace("ECOM-", "").astype(int))
    }
    itens_ecom["pedido_sk"] = itens_ecom["order_id"].map(mapa_ecom)
    itens_ecom["produto_sk"] = 1
    itens_ecom["quantidade"] = itens_ecom["quantity"].fillna(0).astype(int)
    itens_ecom["valor_unitario"] = pd.to_numeric(itens_ecom["unit_price"], errors="coerce").fillna(0)
    itens_ecom["valor_desconto"] = pd.to_numeric(itens_ecom["discount"], errors="coerce").fillna(0)
    itens_ecom["valor_linha"] = itens_ecom["quantidade"] * itens_ecom["valor_unitario"] - itens_ecom["valor_desconto"]
    itens_ecom = itens_ecom[["pedido_sk", "produto_sk", "quantidade", "valor_unitario", "valor_desconto", "valor_linha"]].dropna(subset=["pedido_sk"]).copy()

    itens = pd.concat([itens_leg, itens_ecom], ignore_index=True)
    _recarrega_tabela(eng, "fato_item_pedido")
    # Para o volume de itens, COPY é muito mais eficiente que gerar milhares
    # de INSERTs pelo SQLAlchemy.
    colunas = ["pedido_sk", "produto_sk", "quantidade", "valor_unitario",
               "valor_desconto", "valor_linha"]
    itens["pedido_sk"] = itens["pedido_sk"].astype("int64")
    itens["produto_sk"] = itens["produto_sk"].astype("int64")
    itens["quantidade"] = itens["quantidade"].astype("int64")
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="", suffix=".csv") as arquivo:
        itens[colunas].to_csv(arquivo.name, index=False)
        arquivo.flush()
        conexao = eng.raw_connection()
        try:
            cursor = conexao.cursor()
            with open(arquivo.name, encoding="utf-8", newline="") as entrada:
                cursor.copy_expert(
                    "COPY dw.fato_item_pedido (pedido_sk, produto_sk, quantidade, "
                    "valor_unitario, valor_desconto, valor_linha) "
                    "FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')",
                    entrada,
                )
            conexao.commit()
        finally:
            conexao.close()
    print(f"dw.fato_item_pedido: {len(itens)} linhas")
    return itens


def carrega_fatos_auxiliares(qa):
    eng = eng_dw()
    pedidos = pd.read_sql_query("SELECT pedido_sk, id_origem, sistema_origem FROM dw.fato_pedido", eng)
    pedido_map = {row["id_origem"]: int(row["pedido_sk"]) for _, row in pedidos.iterrows()}

    sac = pd.read_sql_query("SELECT * FROM stg.atendimentos_sac", eng)
    aval = pd.read_sql_query("SELECT * FROM stg.avaliacoes_marketplace", eng)

    sac = sac.copy()
    sac["cliente_sk"] = 1
    sac["pedido_sk"] = sac.apply(
        lambda r: pedido_map.get(f"{('LEG' if str(r['origem_sistema']).upper() == 'LEGADO' else 'ECOM')}-{r['id_pedido_origem']}", None),
        axis=1,
    )
    sac["data_abertura_sk"] = pd.to_datetime(sac["data_abertura"], errors="coerce").dt.date
    sac["data_fechamento_sk"] = pd.to_datetime(sac["data_fechamento"], errors="coerce").dt.date
    sac["canal"] = sac["origem_sistema"]
    sac["motivo_conformado"] = sac["motivo"].fillna("N/A")
    sac["nota_satisfacao"] = pd.to_numeric(sac["nota_satisfacao"], errors="coerce")
    sac["horas_resolucao"] = pd.to_numeric(sac["tempo_resolucao_horas"], errors="coerce")
    sac = sac[["protocolo", "cliente_sk", "pedido_sk", "data_abertura_sk", "data_fechamento_sk", "canal", "motivo_conformado", "nota_satisfacao", "horas_resolucao"]]
    sac = sac.drop_duplicates(subset=["protocolo"], keep="first")
    _recarrega_tabela(eng, "fato_atendimento")
    sac.to_sql("fato_atendimento", eng, schema="dw", if_exists="append", index=False, chunksize=5000)

    aval = aval.copy()
    aval["pedido_sk"] = aval["order_ref"].map(pedido_map)
    aval["produto_sk"] = 1
    aval["data_sk"] = pd.to_datetime(aval["submitted_at"], dayfirst=True, errors="coerce").dt.date
    aval["nota"] = pd.to_numeric(aval["rating"], errors="coerce")
    aval["compra_verificada"] = aval["verified_purchase"].map({True: True, False: False})
    aval["votos_uteis"] = pd.to_numeric(aval["helpful_votes"], errors="coerce")
    aval = aval[["review_id", "pedido_sk", "produto_sk", "data_sk", "nota", "compra_verificada", "votos_uteis"]].dropna(subset=["data_sk"])
    _recarrega_tabela(eng, "fato_avaliacao")
    aval.to_sql("fato_avaliacao", eng, schema="dw", if_exists="append", index=False, chunksize=5000)


if __name__ == "__main__":
    dw = eng_dw()
    qa = Suite(etapa="03_carga_dw")
    carrega_dim_tempo(dw)
    carrega_dimensoes(qa)
    carrega_fato_pedido(qa)
    carrega_fato_item(qa)
    carrega_fatos_auxiliares(qa)

    pedido_total = pd.read_sql_query("SELECT COUNT(*) AS n FROM dw.fato_pedido", dw).iloc[0, 0]
    pedido_leg = pd.read_sql_query("SELECT COUNT(*) AS n FROM stg.legado_pedidos", dw).iloc[0, 0]
    pedido_ecom = pd.read_sql_query("SELECT COUNT(*) AS n FROM stg.ecom_orders", dw).iloc[0, 0]
    qa.igual("quantidade de pedidos no DW", pedido_total, pedido_leg + pedido_ecom, "a soma dos pedidos das duas origens deve bater com a carga do DW")

    leg_total = float(pd.read_sql_query('SELECT COALESCE(SUM(CAST("VALOR_TOTAL" AS NUMERIC)), 0) FROM stg.legado_pedidos', dw).iloc[0, 0])
    ecom_total = float(pd.read_sql_query("SELECT COALESCE(SUM(CAST(total_amount AS NUMERIC)), 0) FROM stg.ecom_orders", dw).iloc[0, 0])
    dw_leg_total = float(pd.read_sql_query("SELECT COALESCE(SUM(valor_total), 0) FROM dw.fato_pedido WHERE sistema_origem = 'LEGADO'", dw).iloc[0, 0])
    dw_ecom_total = float(pd.read_sql_query("SELECT COALESCE(SUM(valor_total), 0) FROM dw.fato_pedido WHERE sistema_origem = 'ECOM'", dw).iloc[0, 0])
    qa.entre("reconciliação financeira legado", abs(dw_leg_total - leg_total) / leg_total * 100 if leg_total else 0, 0, 0.1,
             "a soma de valor_total em DW deve ficar dentro de 0,1% do total origem")
    qa.entre("reconciliação financeira ecommerce", abs(dw_ecom_total - ecom_total) / ecom_total * 100 if ecom_total else 0, 0, 0.1,
             "a soma de valor_total em DW deve ficar dentro de 0,1% do total origem")

    qa.sem_orfaos("FK órfã em fato_pedido", pd.read_sql_query("SELECT cliente_sk FROM dw.fato_pedido", dw), pd.read_sql_query("SELECT cliente_sk FROM dw.dim_cliente", dw), "não pode haver cliente desaparecido")
    qa.igual("dias de entrega negativos", int(pd.read_sql_query("SELECT COUNT(*) FROM dw.fato_pedido WHERE dias_entrega < 0", dw).iloc[0, 0]), 0,
             "qualquer entrega antes do pedido deve ser tratada e normalizada")

    qa.registrar(dw)
    qa.imprimir()
