import os
import json
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Licenciamento Ambiental Brasil & BNDES Benchmark",
    page_icon="🌿",
    layout="wide"
)

# Custom Styling
st.markdown("""
<style>
    .main-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .sub-title { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .metric-card { background: #F8FAFC; border-radius: 8px; padding: 1rem; border-left: 4px solid #3B82F6; }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(base_dir, "acre_bndes_benchmark.json")
    summary_path = os.path.join(base_dir, "benchmark_summary.json")
    
    df = pd.read_json(data_path)
    summary = pd.read_json(summary_path)
    return df, summary

try:
    df, summary = load_data()
except Exception as e:
    st.error(f"Erro ao carregar os dados de benchmark: {e}")
    st.stop()

st.markdown('<div class="main-title">🌿 Brasil: Licenciamento Ambiental & Benchmark Financeiro BNDES</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Cruzamento do acervo de licenças ambientais com operações de crédito e investimento do BNDES para mensurar escala financeira por tipo de licença e porte.</div>', unsafe_allow_html=True)

# Top KPIs
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total de Licenças Cruzadas", f"{len(df):,}")
with col2:
    st.metric("Empresas Únicas Financiadas", f"{df['doc_num'].nunique():,}")
with col3:
    total_val = df.drop_duplicates(subset=['doc_num'])['bndes_total_contratado'].sum()
    st.metric("Total Financiado (BNDES)", f"R$ {total_val/1e9:.2f} Bilhões")
with col4:
    mediana_val = df.drop_duplicates(subset=['doc_num'])['bndes_total_contratado'].median()
    st.metric("Mediana de Financiamento / Empresa", f"R$ {mediana_val/1e6:.2f} Mi")

st.markdown("---")

# Sidebar Filters
st.sidebar.header("🔍 Filtros de Análise")
licencas_disponiveis = sorted(df['tipo_licenca'].dropna().unique())
selected_licencas = st.sidebar.multiselect(
    "Modalidade da Licença",
    options=licencas_disponiveis,
    default=licencas_disponiveis[:4] if len(licencas_disponiveis) >= 4 else licencas_disponiveis
)

portes_disponiveis = sorted(df['porte'].dropna().unique())
selected_portes = st.sidebar.multiselect(
    "Porte do Empreendimento (IMAC)",
    options=portes_disponiveis,
    default=portes_disponiveis
)

# Apply filters
filtered_df = df[
    (df['tipo_licenca'].isin(selected_licencas)) &
    (df['porte'].isin(selected_portes))
]

# Tabs
tab1, tab2, tab3 = st.tabs(["📊 Benchmark por Tipo de Licença", "🏢 Análise por Porte & Setor", "🔎 Explorador de Empresas"])

with tab1:
    st.subheader("1. Valores Médios e Medianos Contratados no BNDES por Tipo de Licença")
    st.caption("A mediana reflete com mais precisão a realidade do empreendimento típico, expurgando megaprojetos de infraestrutura.")
    
    bench_group = filtered_df.groupby('tipo_licenca').agg(
        qtd_licencas=('doc_num', 'count'),
        empresas_unicas=('doc_num', 'nunique'),
        mediana_brl=('bndes_total_contratado', 'median'),
        media_brl=('bndes_total_contratado', 'mean'),
        total_brl=('bndes_total_contratado', 'sum')
    ).reset_index().sort_values(by='mediana_brl', ascending=False)
    
    # Chart
    fig_bar = px.bar(
        bench_group,
        x='tipo_licenca',
        y='mediana_brl',
        color='tipo_licenca',
        text='mediana_brl',
        labels={'tipo_licenca': 'Tipo de Licença', 'mediana_brl': 'Mediana Financiada (R$)'},
        title="Mediana de Valor Financiado por Tipo de Licença (R$)"
    )
    fig_bar.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
    fig_bar.update_layout(showlegend=False, xaxis_tickangle=-30, height=450)
    st.plotly_chart(fig_bar, use_container_width=True)
    
    st.markdown("### Tabela Detalhada de Benchmark Financeiro")
    bench_display = bench_group.copy()
    bench_display['Mediana (R$)'] = bench_display['mediana_brl'].apply(lambda x: f"R$ {x:,.2f}")
    bench_display['Média (R$)'] = bench_display['media_brl'].apply(lambda x: f"R$ {x:,.2f}")
    bench_display['Total Contratado (R$)'] = bench_display['total_brl'].apply(lambda x: f"R$ {x:,.2f}")
    st.dataframe(
        bench_display[['tipo_licenca', 'qtd_licencas', 'empresas_unicas', 'Mediana (R$)', 'Média (R$)', 'Total Contratado (R$)']],
        use_container_width=True
    )

with tab2:
    st.subheader("2. Comparação por Porte Declarado no IMAC vs. Setor BNDES")
    col_a, col_b = st.columns(2)
    
    with col_a:
        fig_porte = px.box(
            filtered_df,
            x='porte',
            y='bndes_total_contratado',
            color='porte',
            log_y=True,
            labels={'porte': 'Porte do Empreendimento', 'bndes_total_contratado': 'Total Financiado (R$ log scale)'},
            title="Distribuição do Investimento por Porte Declarado"
        )
        st.plotly_chart(fig_porte, use_container_width=True)
        
    with col_b:
        top_setores = filtered_df['bndes_subsetor'].value_counts().head(8).reset_index()
        top_setores.columns = ['subsetor', 'contagem']
        fig_pie = px.pie(
            top_setores,
            names='subsetor',
            values='contagem',
            title="Principais Subsetores Financiados com Licença no Acre"
        )
        st.plotly_chart(fig_pie, use_container_width=True)

with tab3:
    st.subheader("3. Consulta Direta de Empresas, Licenças e Valores")
    search = st.text_input("Filtrar por Nome da Empresa ou CNPJ:", "")
    
    table_df = filtered_df.copy()
    if search:
        table_df = table_df[
            table_df['nome_empreendimento'].astype(str).str.contains(search, case=False, na=False) |
            table_df['bndes_cliente'].astype(str).str.contains(search, case=False, na=False) |
            table_df['doc_num'].astype(str).str.contains(search, case=False, na=False)
        ]
        
    display_cols = [
        'doc_num', 'bndes_cliente', 'nome_empreendimento', 'tipo_licenca',
        'porte', 'ano', 'bndes_total_contratado', 'bndes_subsetor'
    ]
    st.write(f"Mostrando **{len(table_df):,}** registros encontrados.")
    st.dataframe(
        table_df[display_cols].rename(columns={
            'doc_num': 'CNPJ',
            'bndes_cliente': 'Cliente (BNDES)',
            'nome_empreendimento': 'Nome do Empreendimento (IMAC)',
            'tipo_licenca': 'Tipo de Licença',
            'porte': 'Porte',
            'ano': 'Ano Emissão',
            'bndes_total_contratado': 'Valor Financiado BNDES (R$)',
            'bndes_subsetor': 'Subsetor'
        }),
        use_container_width=True
    )

# Trigger CI/CD Cloud Build deploy
