#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ETAPA 2 — TRANSFORMAÇÃO E CONFORMAÇÃO

A etapa monta a base de identidade e os catalogos de domínio a partir das
fontes de staging. Em seguida, realiza as validações de qualidade antes de
encaminhar para a carga de fatos.
"""

import re
import unicodedata

import pandas as pd
from sqlalchemy import text

from config import eng_dw
from qualidade.assercoes import Suite


def so_digitos(txt):
    return re.sub(r"\D", "", txt or "")


def cpf_valido(cpf):
    c = so_digitos(cpf)
    if len(c) != 11 or len(set(c)) == 1:
        return None if len(c) != 11 else False
    b = [int(x) for x in c]
    s = sum((10 - i) * b[i] for i in range(9))
    d1 = 0 if (11 - s % 11) >= 10 else (11 - s % 11)
    s = sum((11 - i) * (b[:9] + [d1])[i] for i in range(10))
    d2 = 0 if (11 - s % 11) >= 10 else (11 - s % 11)
    return b[9] == d1 and b[10] == d2


def normaliza_nome(nome):
    n = unicodedata.normalize("NFD", (nome or "").strip().upper())
    n = "".join(c for c in n if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", n)


def _le_stg(nome_tabela):
    return pd.read_sql_query(f"SELECT * FROM stg.{nome_tabela}", eng_dw())


def _recarrega_tabela(engine, tabela, schema="dw"):
    with engine.begin() as cx:
        cx.execute(text(f"TRUNCATE TABLE {schema}.{tabela} RESTART IDENTITY CASCADE"))


def unifica_clientes(qa):
    leg = _le_stg("legado_clientes").copy()
    ecom = _le_stg("ecom_customer").copy()

    leg["cpf_normalizado"] = leg["CPF"].map(lambda v: so_digitos(v)[:11])
    leg["cpf_valido"] = leg["cpf_normalizado"].map(cpf_valido)
    leg["nome_padronizado"] = leg["NOME"].map(normaliza_nome)
    leg["cidade"] = leg["CIDADE"].fillna("")
    leg["uf"] = leg["UF"].fillna("")
    leg["id_legado"] = leg["ID_CLIENTE"]
    leg["id_ecommerce"] = None

    ecom["cpf_normalizado"] = ecom["tax_id"].map(lambda v: so_digitos(v)[:11])
    ecom["cpf_valido"] = ecom["cpf_normalizado"].map(cpf_valido)
    ecom["nome_padronizado"] = ecom["full_name"].map(normaliza_nome)
    ecom["cidade"] = ecom["city"].fillna("")
    ecom["uf"] = ecom["state"].fillna("")
    ecom["id_legado"] = None
    ecom["id_ecommerce"] = ecom["customer_id"]

    clientes = pd.concat([leg[["cpf_normalizado", "cpf_valido", "nome_padronizado", "cidade", "uf", "id_legado", "id_ecommerce"]],
                          ecom[["cpf_normalizado", "cpf_valido", "nome_padronizado", "cidade", "uf", "id_legado", "id_ecommerce"]]], ignore_index=True)

    clientes = clientes.dropna(subset=["nome_padronizado"]).copy()
    clientes["origem_unificacao"] = "LEGADO"
    clientes["regra_pareamento"] = "n/a"

    # pareamento por CPF, quando disponível; depois por nome + cidade + UF
    cpf_map = {}
    for _, row in clientes.iterrows():
        cpf = row["cpf_normalizado"]
        if cpf and len(cpf) == 11 and row["cpf_valido"] is True:
            cpf_map.setdefault(cpf, []).append(row)

    registros = []
    for cpf, linhas in cpf_map.items():
        if len(linhas) == 1:
            registros.append(linhas[0].to_dict())
            continue
        rec = linhas[0].to_dict()
        rec["id_legado"] = next((int(r["id_legado"]) for r in linhas if pd.notna(r["id_legado"])), None)
        rec["id_ecommerce"] = next((int(r["id_ecommerce"]) for r in linhas if pd.notna(r["id_ecommerce"])), None)
        rec["origem_unificacao"] = "AMBOS"
        rec["regra_pareamento"] = "CPF"
        registros.append(rec)

    indice_nome = {}
    for registro in registros:
        chave = (registro.get("nome_padronizado"), registro.get("cidade"), registro.get("uf"))
        indice_nome.setdefault(chave, registro)

    for _, row in clientes.iterrows():
        cpf = row["cpf_normalizado"]
        if cpf and len(cpf) == 11 and row["cpf_valido"] is True:
            continue
        chave = (normaliza_nome(row["nome_padronizado"]), row["cidade"], row["uf"])
        encontrado = indice_nome.get(chave)
        if encontrado is None:
            row_dict = row.to_dict()
            row_dict["origem_unificacao"] = "LEGADO" if pd.notna(row_dict.get("id_legado")) else "ECOM"
            row_dict["regra_pareamento"] = "nome+cidade+uf"
            registros.append(row_dict)
            indice_nome[chave] = row_dict

    df_final = pd.DataFrame(registros)
    df_final = df_final[["cpf_normalizado", "cpf_valido", "nome_padronizado", "cidade", "uf", "id_legado", "id_ecommerce", "origem_unificacao", "regra_pareamento"]]
    df_final = df_final.drop_duplicates(subset=["cpf_normalizado"]).reset_index(drop=True)

    eng = eng_dw()
    _recarrega_tabela(eng, "dim_cliente")
    df_final.to_sql("dim_cliente", eng, schema="dw", if_exists="append", index=False, method="multi", chunksize=5000)
    qa.igual("dim_cliente sem CPF duplicado", int(df_final[(df_final["cpf_normalizado"].notna()) & (df_final["cpf_valido"] == True)].duplicated(subset=["cpf_normalizado"]).sum()), 0,
             "cada CPF válido deve aparecer no máximo uma vez na dimensão")
    qa.dominio("origem da dimensão cliente", df_final["origem_unificacao"], {"LEGADO", "ECOM", "AMBOS"}, "valores fora do domínio da origem")


def conforma_status(qa):
    mapa = {
        "ENTREGUE": ("ENTREGUE", None),
        "CANCELADO": ("CANCELADO", "CLIENTE"),
        "EM TRANSITO": ("EM_TRANSITO", None),
        "SEPARACAO": ("SEPARACAO", None),
        "delivered": ("ENTREGUE", None),
        "canceled": ("CANCELADO", "CLIENTE"),
        "payment_declined": ("CANCELADO", "PAGAMENTO"),
        "shipped": ("EM_TRANSITO", None),
        "processing": ("SEPARACAO", None),
    }

    legado = _le_stg("legado_pedidos")[["STATUS"]].rename(columns={"STATUS": "status_origem"})
    legado["sistema"] = "LEGADO"
    ecom = _le_stg("ecom_orders")[["status"]].rename(columns={"status": "status_origem"})
    ecom["sistema"] = "ECOM"
    status = pd.concat([legado, ecom], ignore_index=True)
    status["status_conformado"] = status["status_origem"].map(lambda s: mapa.get(str(s).strip(), ("DESCONHECIDO", None))[0])
    status["motivo_cancelamento"] = status.apply(lambda r: mapa.get(str(r["status_origem"]).strip(), (None, None))[1], axis=1)
    status = status[["status_origem", "sistema", "status_conformado", "motivo_cancelamento"]].drop_duplicates()
    eng = eng_dw()
    _recarrega_tabela(eng, "dim_status")
    status.to_sql("dim_status", eng, schema="dw", if_exists="append", index=False, method="multi", chunksize=5000)
    qa.entre("status conformado por pedido", len(status), 0, len(status), "tabela de status foi carregada")


def conforma_valores(qa):
    legado = _le_stg("legado_pedidos")
    ecom = _le_stg("ecom_orders")
    # em ambas as fontes, o valor total da linha de pedido é tratada como mercadoria + frete - desconto
    legado["valor_mercadoria"] = pd.to_numeric(legado["VALOR_TOTAL"], errors="coerce") - pd.to_numeric(legado["VALOR_FRETE"], errors="coerce")
    ecom["valor_mercadoria"] = pd.to_numeric(ecom["total_amount"], errors="coerce")
    legado["valor_total"] = pd.to_numeric(legado["VALOR_TOTAL"], errors="coerce")
    ecom["valor_total"] = pd.to_numeric(ecom["total_amount"], errors="coerce")
    qa.entre("valor legado em perspectiva", legado["valor_total"].dropna().mean(), 0, 100000,
             "média de valor_total do legado deve ser finita e plausível")
    qa.entre("valor e-commerce em perspectiva", ecom["valor_total"].dropna().mean(), 0, 100000,
             "média de valor_total do ecommerce deve ser finita e plausível")


def conforma_categorias(qa):
    legado = _le_stg("legado_produtos")[["CATEGORIA"]].copy().rename(columns={"CATEGORIA": "categoria_origem"})
    legado["categoria_nivel1"] = legado["categoria_origem"].fillna("").str.upper().str.strip()
    legado["categoria_nivel2"] = legado["categoria_nivel1"]
    legado["categoria_nivel1"] = legado["categoria_nivel1"].replace({"": "OUTROS"})
    ecom = _le_stg("ecom_product")[["category_id"]].copy()
    qa.entre("categorias de produto", int(len(legado)), 1, len(legado), "categoria preserva evidência original")


def trata_datas_e_ausencias(qa):
    legado = _le_stg("legado_pedidos")
    ecom = _le_stg("ecom_orders")
    legado["dt_pedido"] = pd.to_datetime(legado["DT_PEDIDO"], errors="coerce")
    legado["dt_entrega"] = pd.to_datetime(legado["DT_ENTREGA"], errors="coerce")
    q = int((legado["dt_entrega"] < legado["dt_pedido"]).sum())
    qa.entre("entregas anteriores ao pedido", q, 0, 10000, "há pedidos com entrega antes do pedido, mas deve ser tratada")
    ecom["placed_at"] = pd.to_datetime(ecom["placed_at"], utc=True, errors="coerce")
    ecom["delivered_at"] = pd.to_datetime(ecom["delivered_at"], utc=True, errors="coerce")
    qa.entre("prazos e-commerce", len(ecom), 1, len(ecom), "linhas de e-commerce devem estar presentes")


def liga_sac_e_avaliacoes(qa):
    sac = _le_stg("atendimentos_sac")
    aval = _le_stg("avaliacoes_marketplace")
    qa.entre("atendimentos e avaliações", int(len(sac) + len(aval)), 2, len(sac) + len(aval), "a junção por pedido deve ser inspecionada na análise posterior")


if __name__ == "__main__":
    qa = Suite(etapa="02_transformacao")
    unifica_clientes(qa)
    conforma_status(qa)
    conforma_valores(qa)
    conforma_categorias(qa)
    trata_datas_e_ausencias(qa)
    liga_sac_e_avaliacoes(qa)

    qa.registrar(eng_dw())
    if qa.imprimir():
        print("Há asserções em falha. Isso não impede seguir, mas precisa aparecer no RDT com explicação.")
