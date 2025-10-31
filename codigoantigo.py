import streamlit as st
import cx_Oracle
import pandas as pd
import plotly.express as px
import os

# Ajuste do PATH para Oracle Instant Client
os.environ["PATH"] = r"C:\oracle\instantclient_19_28;" + os.environ["PATH"]

# Configurações iniciais
usuario = "CLT167027RAVEL"
senha = "bdtre09841FCOPR?!"
dsn = cx_Oracle.makedsn("201.157.243.3", 1521, service_name="CHE0V5_167027_C")

# Consulta detalhada por marca e mês
query_detalhada = """
SELECT
    NVL(M.MARCA, '* SEM MARCA *') AS MARCA,
    TO_CHAR(V.DTAVDA, 'YYYY-MM') AS MES_ANO,
    COUNT(DISTINCT V.NRODOCTO) AS QTD_PEDIDOS,
    COUNT(DISTINCT V.SEQPESSOA) AS QTD_CLIENTES,
    SUM((V.VLRITEM - V.VLRDEVOLITEM
        + NVL(V.VLREMBDESCRESSARCST,0)
        - NVL(V.VLREMBDESCRESSARCSTDEVOL,0))) AS VLR,
    SUM((V.VLRITEM - V.VLRDEVOLITEM
        + NVL(V.VLREMBDESCRESSARCST,0)
        - NVL(V.VLREMBDESCRESSARCSTDEVOL,0)))
        / NULLIF(COUNT(DISTINCT V.SEQPESSOA),0) AS TICKET_MEDIO_CLIENTE,
    SUM(V.QTDITEM - V.QTDDEVOLITEM) AS QTD_VENDIDA
FROM CONSINCO.MAXV_ABCDISTRIBBASE V
JOIN CONSINCO.MAP_PRODUTO P ON V.SEQPRODUTO = P.SEQPRODUTO
JOIN CONSINCO.MAP_FAMDIVISAO FD ON FD.NRODIVISAO = V.NRODIVISAO AND FD.SEQFAMILIA = P.SEQFAMILIA
JOIN CONSINCO.MAP_FAMILIA F ON F.SEQFAMILIA = FD.SEQFAMILIA
LEFT JOIN CONSINCO.MAP_MARCA M ON NVL(F.SEQMARCA,0) = M.SEQMARCA
WHERE V.DTAVDA >= ADD_MONTHS(TRUNC(SYSDATE,'MM'), -6)
  AND V.NROEMPRESA = 1
  AND V.NROSEGMENTO = 3
  AND V.CODGERALOPER NOT IN (
    216, 251, 801, 809, 815, 820, 822,
    823, 955, 802, 811, 805, 206, 850, 922)
GROUP BY NVL(M.MARCA, '* SEM MARCA *'), TO_CHAR(V.DTAVDA, 'YYYY-MM')
ORDER BY MES_ANO, VLR DESC
"""

# Consulta KPIs totais mensais
query_kpis_mensais = """
SELECT
    TO_CHAR(V.DTAVDA, 'YYYY-MM') AS MES_ANO,
    COUNT(DISTINCT V.NRODOCTO) AS QTD_PEDIDOS,
    COUNT(DISTINCT V.SEQPESSOA) AS QTD_CLIENTES,
    SUM((V.VLRITEM - V.VLRDEVOLITEM
        + NVL(V.VLREMBDESCRESSARCST,0)
        - NVL(V.VLREMBDESCRESSARCSTDEVOL,0))) AS VLR,
    SUM((V.VLRITEM - V.VLRDEVOLITEM
        + NVL(V.VLREMBDESCRESSARCST,0)
        - NVL(V.VLREMBDESCRESSARCSTDEVOL,0)))
        / NULLIF(COUNT(DISTINCT V.SEQPESSOA),0) AS TICKET_MEDIO_CLIENTE
FROM CONSINCO.MAXV_ABCDISTRIBBASE V
WHERE V.DTAVDA >= ADD_MONTHS(TRUNC(SYSDATE,'MM'), -6)
  AND V.NROEMPRESA = 1
  AND V.NROSEGMENTO = 3
  AND V.CODGERALOPER NOT IN (
    216, 251, 801, 809, 815, 820, 822,
    823, 955, 802, 811, 805, 206, 850, 922)
GROUP BY TO_CHAR(V.DTAVDA, 'YYYY-MM')
ORDER BY MES_ANO
"""

try:
    conn = cx_Oracle.connect(usuario, senha, dsn)
    df_detalhado = pd.read_sql(query_detalhada, conn)
    df_kpis_mensais = pd.read_sql(query_kpis_mensais, conn)
    conn.close()
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

st.title("Dashboard de Vendas - E-COMMERCE")

# ---- Sidebar: resumo total KPIs, gráfico de vendas por mês e KPIs mensais ----
with st.sidebar:
    st.header("Resumo Total dos KPIs")
    st.write(f"Pedidos: {int(df_kpis_mensais['QTD_PEDIDOS'].sum()):,}")
    st.write(f"Clientes: {int(df_kpis_mensais['QTD_CLIENTES'].sum()):,}")
    st.write(f"Valor Líquido: R$ {df_kpis_mensais['VLR'].sum():,.2f}")
    st.write(f"Ticket Médio: R$ {df_kpis_mensais['TICKET_MEDIO_CLIENTE'].mean():,.2f}")
    st.markdown("---")

    st.subheader("Valor Total de Venda por Mês")
    fig_total = px.bar(
        df_kpis_mensais,
        x='MES_ANO',
        y='VLR',
        text=df_kpis_mensais['VLR'].map(lambda x: f"R$ {x:,.2f}")
    )
    fig_total.update_traces(textposition='outside')
    st.plotly_chart(fig_total, use_container_width=True)

    st.subheader("KPIs Mensais")
    for _, row in df_kpis_mensais.iterrows():
        st.markdown(f"**{row['MES_ANO']}**")
        st.write(f"Pedidos: {int(row['QTD_PEDIDOS']):,}")
        st.write(f"Clientes: {int(row['QTD_CLIENTES']):,}")
        st.write(f"Valor Líquido: R$ {row['VLR']:,.2f}")
        st.write(f"Ticket Médio: R$ {row['TICKET_MEDIO_CLIENTE']:,.2f}")
        st.markdown("---")

# ---- Centro: gráficos top/bottom 3 marcas ----
col_center = st.container()

def top_3_marcas(df):
    df_top = df.groupby(['MES_ANO', 'MARCA'], as_index=False)['VLR'].sum()
    return df_top.sort_values(['MES_ANO', 'VLR'], ascending=[True, False]).groupby('MES_ANO').head(3)

def bottom_3_marcas(df):
    df_bottom = df.groupby(['MES_ANO', 'MARCA'], as_index=False)['VLR'].sum()
    return df_bottom.sort_values(['MES_ANO', 'VLR'], ascending=True).groupby('MES_ANO').head(3)

df_top = top_3_marcas(df_detalhado)
df_bottom = bottom_3_marcas(df_detalhado)

col_center.subheader("3 Marcas que Mais Venderam por Mês")
fig_top = px.bar(
    df_top,
    x="MES_ANO",
    y="VLR",
    color="MARCA",
    barmode="group",
    text=df_top['VLR'].map(lambda x: f"R$ {x:,.2f}")
)
fig_top.update_traces(textposition='outside')
col_center.plotly_chart(fig_top)

col_center.subheader("3 Marcas que Menos Venderam por Mês")
fig_bottom = px.bar(
    df_bottom,
    x="MES_ANO",
    y="VLR",
    color="MARCA",
    barmode="group",
    text=df_bottom['VLR'].map(lambda x: f"R$ {x:,.2f}")
)
fig_bottom.update_traces(textposition='outside')
col_center.plotly_chart(fig_bottom)