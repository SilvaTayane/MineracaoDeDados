#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETAPA 4 — TABELA-BASE DE ANÁLISE (ABT)

A tabela-base traz o alvo e os atributos preditivos calculados apenas com
informações disponíveis até a data de corte, além de uma versão com vazamento
intencional para comparação e ensino.
"""

import argparse

import pandas as pd
from sqlalchemy import text

from config import DATA_CORTE, DATA_FIM_ALVO, eng_dw
from qualidade.assercoes import Suite


SQL_ALVO = f"""
WITH base AS (
    SELECT DISTINCT c.cliente_sk
    FROM dw.dim_cliente c
    JOIN dw.fato_pedido p ON p.cliente_sk = c.cliente_sk
    WHERE p.data_pedido_sk <= DATE '{DATA_CORTE}'
),
compras_na_janela AS (
    SELECT DISTINCT p.cliente_sk
    FROM dw.fato_pedido p
    JOIN dw.dim_status s ON s.status_sk = p.status_sk
    WHERE p.data_pedido_sk > DATE '{DATA_CORTE}'
      AND p.data_pedido_sk <= DATE '{DATA_FIM_ALVO}'
      AND s.status_conformado <> 'CANCELADO'
)
SELECT b.cliente_sk,
       DATE '{DATA_CORTE}' AS data_corte,
       CASE WHEN j.cliente_sk IS NOT NULL THEN 1 ELSE 0 END AS alvo_recompra_90d
FROM base b
LEFT JOIN compras_na_janela j ON j.cliente_sk = b.cliente_sk
"""


def monta_atributos_corretos(dw):
    pedidos = pd.read_sql_query("SELECT * FROM dw.fato_pedido", dw)
    status = pd.read_sql_query("SELECT * FROM dw.dim_status", dw)
    pedidos = pedidos.merge(status[["status_sk", "status_conformado"]], on="status_sk", how="left")
    pedidos["data_pedido_sk"] = pd.to_datetime(pedidos["data_pedido_sk"], errors="coerce")
    pedidos["data_entrega_sk"] = pd.to_datetime(pedidos["data_entrega_sk"], errors="coerce")
    corte = pd.Timestamp(DATA_CORTE)
    pedidos_corte = pedidos[pedidos["data_pedido_sk"] <= corte].copy()

    if pedidos_corte.empty:
        return pd.DataFrame(columns=["cliente_sk", "recencia_dias", "frequencia_pedidos", "valor_monetario", "ticket_medio", "prazo_medio_entrega", "taxa_cancelamento"])

    g = pedidos_corte.groupby("cliente_sk", dropna=False).agg(
        recencia_dias=("data_pedido_sk", lambda s: (corte - s.max()).days if not s.empty else None),
        frequencia_pedidos=("pedido_sk", "count"),
        valor_monetario=("valor_total", "sum"),
        ticket_medio=("valor_total", "mean"),
        prazo_medio_entrega=("dias_entrega", "mean"),
        taxa_cancelamento=("status_conformado", lambda s: (s == "CANCELADO").mean()),
    ).reset_index()
    g["ticket_medio"] = g["valor_monetario"] / g["frequencia_pedidos"]
    g["prazo_medio_entrega"] = g["prazo_medio_entrega"].fillna(0)
    g["taxa_cancelamento"] = g["taxa_cancelamento"].fillna(0)
    return g


def monta_atributos_com_vazamento(dw):
    pedidos = pd.read_sql_query("SELECT * FROM dw.fato_pedido", dw)
    status = pd.read_sql_query("SELECT * FROM dw.dim_status", dw)
    pedidos = pedidos.merge(status[["status_sk", "status_conformado"]], on="status_sk", how="left")
    pedidos["data_pedido_sk"] = pd.to_datetime(pedidos["data_pedido_sk"], errors="coerce")
    corte = pd.Timestamp(DATA_CORTE)

    g = pedidos.groupby("cliente_sk", dropna=False).agg(
        recencia_dias=("data_pedido_sk", lambda s: (corte - s.max()).days if not s.empty else None),
        frequencia_pedidos=("pedido_sk", "count"),
        valor_monetario=("valor_total", "sum"),
        ticket_medio=("valor_total", "mean"),
        prazo_medio_entrega=("dias_entrega", "mean"),
        taxa_cancelamento=("status_conformado", lambda s: (s == "CANCELADO").mean()),
    ).reset_index()
    g["ticket_medio"] = g["valor_monetario"] / g["frequencia_pedidos"]
    g["prazo_medio_entrega"] = g["prazo_medio_entrega"].fillna(0)
    g["taxa_cancelamento"] = g["taxa_cancelamento"].fillna(0)

    # vazamento intencional: usa dados após a data de corte para recencia e frequência
    vazamento = pedidos[pedidos["data_pedido_sk"] <= pd.Timestamp(DATA_FIM_ALVO)].groupby("cliente_sk", dropna=False).agg(
        recencia_dias_vazado=("data_pedido_sk", lambda s: (pd.Timestamp(DATA_CORTE) - s.max()).days if not s.empty else None),
        frequencia_pedidos_vazado=("pedido_sk", "count"),
    ).reset_index()
    g = g.merge(vazamento, on="cliente_sk", how="left")
    std = g["valor_monetario"].std(ddof=0)
    mean = g["valor_monetario"].mean()
    g["valor_monetario_z"] = (g["valor_monetario"] - mean) / std if std else 0
    return g


def grava(df, dw, sufixo):
    tabela = "recompra_90d" if sufixo == "correta" else "recompra_90d_vazamento"
    with dw.begin() as cx:
        cx.execute(text(f"TRUNCATE TABLE abt.{tabela} RESTART IDENTITY CASCADE"))
    df.to_sql(tabela, dw, schema="abt", if_exists="append", index=False, method="multi", chunksize=5_000)
    print(f"abt.{tabela}: {len(df)} linhas, {df.shape[1]} colunas")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--correta", action="store_true")
    ap.add_argument("--vazamento", action="store_true")
    args = ap.parse_args()
    if not (args.correta or args.vazamento):
        ap.error("escolha --correta ou --vazamento")

    dw = eng_dw()
    alvo = pd.read_sql(text(SQL_ALVO), dw)
    print(f"alvo: {len(alvo)} clientes | taxa de recompra = {alvo['alvo_recompra_90d'].mean():.3f}")

    qa = Suite(etapa="04_abt_" + ("correta" if args.correta else "vazamento"))
    qa.entre("taxa do alvo", float(alvo["alvo_recompra_90d"].mean()), 0.02, 0.60,
             "classe extremamente desbalanceada indica erro na janela")
    qa.unico("cliente_sk no alvo", alvo["cliente_sk"])

    atributos = monta_atributos_corretos(dw) if args.correta else monta_atributos_com_vazamento(dw)
    antes = len(alvo)
    abt = alvo.merge(atributos, on="cliente_sk", how="left")
    qa.cardinalidade_preservada("junção alvo x atributos", antes, len(abt))
    grava(abt, dw, "correta" if args.correta else "vazamento")
    qa.registrar(dw)
    qa.imprimir()
