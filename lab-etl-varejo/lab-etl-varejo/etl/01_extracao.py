#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETAPA 1 — EXTRAÇÃO

Carrega as quatro fontes para a camada stg sem transformar o significado dos
valores. A única adição é o metadado de procedência.
"""

import json
from datetime import datetime, timezone

import pandas as pd
from sqlalchemy import text

from config import ARQ_AVALIACOES, ARQ_SAC, eng_dw, eng_mysql, eng_origem
from qualidade.assercoes import Suite

AGORA = datetime.now(timezone.utc)
LOTE = 50_000


def grava_stg(df, tabela, engine, primeiro_bloco):
    df = df.copy()
    df["_fonte"] = tabela.split("_")[0]
    df["_extraido_em"] = AGORA
    df.to_sql(tabela, engine, schema="stg",
              if_exists="replace" if primeiro_bloco else "append",
              index=False, method="multi", chunksize=5_000)


def extrai_mysql(qa):
    eng = eng_mysql()
    for tabela in ["CLIENTES", "PRODUTOS", "PEDIDOS", "ITENS_PEDIDO"]:
        sql = f"SELECT * FROM {tabela}"
        chunks = pd.read_sql_query(sql, eng, chunksize=LOTE)
        primeiro = True
        total = 0
        for chunk in chunks:
            nome_tabela = f"legado_{tabela.lower()}"
            grava_stg(chunk, nome_tabela, eng_dw(), primeiro)
            primeiro = False
            total += len(chunk)
        print(f"stg.{nome_tabela}: {total} linhas")


def extrai_postgres(qa):
    eng = eng_origem()
    for tabela, destino in [
        ("customer", "ecom_customer"),
        ("product", "ecom_product"),
        ("orders", "ecom_orders"),
        ("order_item", "ecom_order_item"),
    ]:
        sql = f"SELECT * FROM shop.{tabela}"
        chunks = pd.read_sql_query(sql, eng, chunksize=LOTE)
        primeiro = True
        total = 0
        for chunk in chunks:
            grava_stg(chunk, destino, eng_dw(), primeiro)
            primeiro = False
            total += len(chunk)
        print(f"stg.{destino}: {total} linhas")


def extrai_sac(qa):
    df = pd.read_csv(ARQ_SAC, sep=";", encoding="latin-1", dtype=str,
                     keep_default_na=False)
    df = df.rename(columns=lambda x: x.strip())
    df["_fonte"] = "sac"
    df["_extraido_em"] = AGORA
    df.to_sql("atendimentos_sac", eng_dw(), schema="stg",
              if_exists="replace", index=False, method="multi", chunksize=5000)
    print(f"stg.atendimentos_sac: {len(df)} linhas")
    return df


def extrai_avaliacoes(qa):
    rows = []
    with open(ARQ_AVALIACOES, encoding="utf-8") as f:
        for linha in f:
            linha = linha.strip()
            if not linha:
                continue
            obj = json.loads(linha)
            if not isinstance(obj, dict):
                continue

            flat = dict(obj)
            order = flat.pop("order", None)
            product = flat.pop("product", None)

            if isinstance(order, dict):
                flat["order_ref"] = order.get("ref")
                flat["order_channel"] = order.get("channel")
            else:
                flat["order_ref"] = None
                flat["order_channel"] = None

            if isinstance(product, dict):
                flat["product_sku"] = product.get("sku")
            else:
                flat["product_sku"] = None

            rows.append(flat)

    if rows:
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=[
            "review_id", "order_ref", "order_channel", "product_sku",
            "submitted_at", "rating", "title", "comment",
            "verified_purchase", "helpful_votes"
        ])

    cols_preservadas = [
        "review_id", "order_ref", "order_channel", "product_sku",
        "submitted_at", "rating", "title", "comment",
        "verified_purchase", "helpful_votes"
    ]
    for coluna in cols_preservadas:
        if coluna not in df.columns:
            df[coluna] = None

    df = df[cols_preservadas]
    df["_fonte"] = "avaliacoes"
    df["_extraido_em"] = AGORA
    df.to_sql("avaliacoes_marketplace", eng_dw(), schema="stg",
              if_exists="replace", index=False, method="multi", chunksize=5000)
    print(f"stg.avaliacoes_marketplace: {len(df)} linhas")
    return df


if __name__ == "__main__":
    qa = Suite(etapa="01_extracao")
    extrai_mysql(qa)
    extrai_postgres(qa)
    sac = extrai_sac(qa)
    aval = extrai_avaliacoes(qa)

    legado_qtd = pd.read_sql_query("SELECT COUNT(*) AS n FROM PEDIDOS", eng_mysql()).iloc[0, 0]
    qa.igual("linhas legado.PEDIDOS", pd.read_sql_query("SELECT COUNT(*) AS n FROM stg.legado_pedidos", eng_dw()).iloc[0, 0], legado_qtd,
             "a extração não pode perder linhas do legado")
    qa.sem_nulos("protocolo do SAC", sac["protocolo"], "protocolo é chave do atendimento e não pode ficar nulo")
    qa.unico("review_id", aval["review_id"], "avaliações duplicadas quebram a identidade da revisão")

    qa.registrar(eng_dw())
    qa.imprimir()
