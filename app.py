import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# --- CONFIGURAÇÃO DA API FLASK ---
api_url_detalhado = st.secrets["API_URL_DETALHADO"]  # Ex: "http://167.250.29.60:5000/detalhado"
api_url_kpis = st.secrets["API_URL_KPIS"]            # Ex: "http://167.250.29.60:5000/kpis_mensais"

# --- BUSCANDO OS DADOS DA API ---
try:
    # Requisição dos dados detalhados
    resp_detalhado = requests.get(api_url_detalhado)
    resp_detalhado.raise_for_status()
    df_detalhado = pd.DataFrame(resp_detalhado.json())

    # Requisição dos KPIs mensais
    resp_kpis = requests.get(api_url_kpis)
    resp_kpis.raise_for_status()
    df_kpis_mensais = pd.DataFrame(resp_kpis.json())

except requests.exceptions.RequestException as e:
    st.error(f"Erro ao conectar com a API: {e}")
    st.stop()

# --- PROCESSAMENTO ---
df_kpis_mensais["Variação_VLR_%"] = df_kpis_mensais["VLR"].pct_change() * 100
df_kpis_mensais["Variação_CLIENTES_%"] = df_kpis_mensais["QTD_CLIENTES"].pct_change() * 100

# --- DASHBOARD PRINCIPAL ---
st.title("📦 Dashboard de Vendas - E-COMMERCE")

# Mantendo abas originais + novas abas
abas = st.tabs([
    "📊 Visão Geral",
    "📈 Análise Avançada",
    "🏭 Desempenho por Marca",
    "⚡ Indicadores de Eficiência",
    "📅 Análise de Sazonalidade",
    "🎯 Análise de Campanhas",
    "🔮 Previsão de Vendas"
])

# ===========================================================
# 📊 ABA 1 - VISÃO GERAL
# ===========================================================
with abas[0]:
    with st.sidebar:
        st.header("Resumo Total dos KPIs")
        st.write(f"Pedidos: {int(df_kpis_mensais['QTD_PEDIDOS'].sum()):,}")
        st.write(f"Clientes: {int(df_kpis_mensais['QTD_CLIENTES'].sum()):,}")
        st.write(f"Valor Líquido: R$ {df_kpis_mensais['VLR'].sum():,.2f}")
        st.write(f"Ticket Médio: R$ {df_kpis_mensais['TICKET_MEDIO_CLIENTE'].mean():,.2f}")
        st.markdown("---")
        st.subheader("Valor Total de Venda por Mês")
        fig_total = px.bar(
            df_kpis_mensais, x='MES_ANO', y='VLR',
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

    # Top/Bottom 3 marcas
    def top_3_marcas(df):
        df_top = df.groupby(['MES_ANO','MARCA'], as_index=False)['VLR'].sum()
        return df_top.sort_values(['MES_ANO','VLR'], ascending=[True,False]).groupby('MES_ANO').head(3)

    def bottom_3_marcas(df):
        df_bottom = df.groupby(['MES_ANO','MARCA'], as_index=False)['VLR'].sum()
        return df_bottom.sort_values(['MES_ANO','VLR'], ascending=True).groupby('MES_ANO').head(3)

    df_top = top_3_marcas(df_detalhado)
    df_bottom = bottom_3_marcas(df_detalhado)

    st.subheader("🏆 Top 3 Marcas que Mais Venderam por Mês")
    fig_top = px.bar(
        df_top, x="MES_ANO", y="VLR", color="MARCA", barmode="group",
        text=df_top['VLR'].map(lambda x: f"R$ {x:,.2f}")
    )
    fig_top.update_traces(textposition='outside')
    st.plotly_chart(fig_top)

    st.subheader("📉 3 Marcas que Menos Venderam por Mês")
    fig_bottom = px.bar(
        df_bottom, x="MES_ANO", y="VLR", color="MARCA", barmode="group",
        text=df_bottom['VLR'].map(lambda x: f"R$ {x:,.2f}")
    )
    fig_bottom.update_traces(textposition='outside')
    st.plotly_chart(fig_bottom)

    # Crescimento Mensal
    st.subheader("📈 Crescimento Mensal (%)")
    st.dataframe(
        df_kpis_mensais[["MES_ANO","Variação_VLR_%","Variação_CLIENTES_%"]]
        .style.format({"Variação_VLR_%":"{:.2f}%","Variação_CLIENTES_%":"{:.2f}%"})
        .applymap(lambda v:'color: green' if v>0 else 'color: red',
                  subset=["Variação_VLR_%","Variação_CLIENTES_%"])
    )

# ===========================================================
# 📈 ABA 2 - ANÁLISE AVANÇADA
# ===========================================================
with abas[1]:
    st.header("📈 Análise Avançada")
    st.subheader("Correlação entre Valor de Venda e Número de Clientes")
    fig_corr = px.scatter(
        df_kpis_mensais, x="QTD_CLIENTES", y="VLR",
        trendline="ols", text="MES_ANO"
    )
    st.plotly_chart(fig_corr, use_container_width=True)

    st.subheader("Distribuição do Ticket Médio por Marca")
    fig_box = px.box(df_detalhado, x="MARCA", y="VLR",
                     color="MARCA", points="all")
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("Resumo Consolidado por Mês")
    st.dataframe(df_kpis_mensais[[
        "MES_ANO","VLR","QTD_CLIENTES","TICKET_MEDIO_CLIENTE",
        "Variação_VLR_%","Variação_CLIENTES_%"
    ]].style.format({
        "VLR":"R$ {:,.2f}",
        "TICKET_MEDIO_CLIENTE":"R$ {:,.2f}",
        "Variação_VLR_%":"{:.2f}%",
        "Variação_CLIENTES_%":"{:.2f}%"
    }))

# ===========================================================
# 🔹 NOVAS ABAS ADICIONAIS
# ===========================================================
# 🏭 Desempenho por Marca
with abas[2]:
    st.header("🏭 Desempenho por Marca")
    st.write("Gráficos e KPIs detalhados por marca aqui")
    df_marca = df_detalhado.groupby("MARCA",as_index=False)["VLR"].sum()
    fig = px.bar(df_marca,x="MARCA",y="VLR",text=df_marca["VLR"].map(lambda x:f"R$ {x:,.2f}"))
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig,use_container_width=True)

# ⚡ Indicadores de Eficiência
with abas[3]:
    st.header("⚡ Indicadores de Eficiência")
    st.write("KPIs de eficiência operacional e vendas")
    st.dataframe(df_kpis_mensais[["MES_ANO","QTD_PEDIDOS","QTD_CLIENTES","VLR"]])

# 📅 Análise de Sazonalidade
with abas[4]:
    st.header("📅 Análise de Sazonalidade")
    st.write("Visualização de padrões sazonais por mês")
    fig = px.line(df_kpis_mensais,x="MES_ANO",y="VLR",markers=True)
    st.plotly_chart(fig,use_container_width=True)

# 🎯 Análise de Campanhas
with abas[5]:
    st.header("🎯 Análise de Campanhas")
    st.write("KPIs de campanhas promocionais")
    df_campaign = df_detalhado.groupby("MARCA",as_index=False)["VLR"].mean()
    fig = px.bar(df_campaign,x="MARCA",y="VLR",text=df_campaign["VLR"].map(lambda x:f"R$ {x:,.2f}"))
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig,use_container_width=True)

# 🔮 Previsão de Vendas
with abas[6]:
    st.header("🔮 Previsão de Vendas")
    st.write("Exemplo de previsão baseada em séries temporais")
    st.line_chart(df_kpis_mensais.set_index("MES_ANO")["VLR"])