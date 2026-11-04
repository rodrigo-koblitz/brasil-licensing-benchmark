import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Panorama Geral Nacional - Brasil",
    page_icon="🇧🇷",
    layout="wide"
)

st.markdown("""
<style>
    .page-title { font-size: 2.2rem; font-weight: 700; color: #047857; margin-bottom: 0.5rem; }
    .page-sub { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">🇧🇷 Panorama Consolidado Nacional: Todos os Estados</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Análise macro comparativa do esforço de licenciamento ambiental, empreendimentos e séries temporais de 25 estados brasileiros e do IBAMA.</div>', unsafe_allow_html=True)

# Load data
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_csv = os.path.join(base_dir, "data", "brasil_estados_consolidado.csv")
data_json = os.path.join(base_dir, "data", "serie_temporal_nacional.json")

try:
    df_estados = pd.read_csv(data_csv)
    with open(data_json, 'r', encoding='utf-8') as f:
        ts_data = json.load(f)
except Exception as e:
    st.error(f"Erro ao carregar dados consolidados: {e}")
    st.stop()

# Macro KPIs
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
total_lic_nac = df_estados['total_licencas'].sum()
total_emp_nac = df_estados['total_empreendimentos'].dropna().sum()
total_ufs = len(df_estados)

with kpi1:
    st.metric("Total Nacional de Atos/Licenças", f"{total_lic_nac:,.0f}".replace(",", "."))
with kpi2:
    st.metric("Empreendimentos Processados", f"{total_emp_nac:,.0f}".replace(",", "."))
with kpi3:
    st.metric("Unidades Federativas & IBAMA", f"{total_ufs}")
with kpi4:
    estado_lider = df_estados.iloc[0]['sigla']
    st.metric("Estado com Maior Volume", f"{estado_lider} ({df_estados.iloc[0]['total_licencas']:,.0f})")

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["📊 Comparativo entre Estados", "📈 Evolução Temporal Nacional", "📥 Dados Consolidados (Download)"])

with tab1:
    st.subheader("1. Ranking e Volume de Licenciamento por Estado")
    
    col_chart, col_rank = st.columns([2, 1])
    
    with col_chart:
        fig_bar = px.bar(
            df_estados.sort_values(by='total_licencas', ascending=True),
            x='total_licencas',
            y='sigla',
            orientation='h',
            text='total_licencas',
            color='total_licencas',
            color_continuous_scale='Greens',
            labels={'total_licencas': 'Total de Licenças', 'sigla': 'Estado / UF'},
            title="Total de Licenças Emitidas por UF"
        )
        fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_bar.update_layout(height=650, coloraxis_showscale=False)
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_rank:
        st.markdown("### Top 10 Estados em Volume")
        st.dataframe(
            df_estados[['sigla', 'estado', 'total_licencas', 'total_empreendimentos']].head(10).rename(columns={
                'sigla': 'UF',
                'estado': 'Estado',
                'total_licencas': 'Licenças',
                'total_empreendimentos': 'Empreendimentos'
            }),
            use_container_width=True,
            height=600
        )

with tab2:
    st.subheader("2. Evolução Temporal Histórica do Licenciamento (2000 a 2026)")
    
    # Timeseries data preparation
    years = ts_data['years']
    nat_lic = ts_data['national_total_licenses_by_year']
    nat_emp = ts_data['national_total_enterprises_by_year']
    
    df_ts = pd.DataFrame({
        'Ano': years,
        'Licenças Emitidas': nat_lic,
        'Empreendimentos Ativos': nat_emp
    })
    
    # Plot line chart
    fig_ts = go.Figure()
    fig_ts.add_trace(go.Scatter(
        x=df_ts['Ano'], y=df_ts['Licenças Emitidas'],
        mode='lines+markers', name='Total de Licenças',
        line=dict(color='#047857', width=3)
    ))
    fig_ts.add_trace(go.Scatter(
        x=df_ts['Ano'], y=df_ts['Empreendimentos Ativos'],
        mode='lines+markers', name='Empreendimentos Únicos',
        line=dict(color='#3B82F6', width=2, dash='dot')
    ))
    fig_ts.update_layout(
        title="Histórico Anual de Licenças e Empreendimentos no Brasil",
        xaxis_title="Ano",
        yaxis_title="Volume",
        hovermode="x unified",
        height=450
    )
    st.plotly_chart(fig_ts, use_container_width=True)

with tab3:
    st.subheader("3. Tabela Consolidada & Download dos Dados")
    st.write("Baixe a base de dados consolidada em formato CSV ou JSON para utilizar em suas análises locais, notebooks ou relatórios institucionais.")
    
    col_csv, col_json = st.columns(2)
    with col_csv:
        csv_bytes = df_estados.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Base Consolidada (CSV)",
            data=csv_bytes,
            file_name="brasil_estados_licenciamento_consolidado.csv",
            mime="text/csv"
        )
    with col_json:
        json_bytes = df_estados.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8')
        st.download_button(
            label="📥 Baixar Base Consolidada (JSON)",
            data=json_bytes,
            file_name="brasil_estados_licenciamento_consolidado.json",
            mime="application/json"
        )
        
    st.markdown("### Visualização Completa da Tabela Nacional")
    st.dataframe(
        df_estados.rename(columns={
            'sigla': 'UF',
            'estado': 'Nome do Estado',
            'total_licencas': 'Total Licenças',
            'total_empreendimentos': 'Empreendimentos',
            'ano_inicio': 'Ano Início',
            'ano_fim': 'Ano Fim',
            'total_tipologias': 'Tipologias Distintas',
            'principais_licencas': 'Principais Modalidades de Licenças'
        }),
        use_container_width=True
    )
