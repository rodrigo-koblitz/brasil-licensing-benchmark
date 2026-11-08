import os
import json
import base64
import glob
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from tab_bahia_experimental import render_bahia_experimental_tab
from map_module import render_map_module

st.set_page_config(
    page_title="Plataforma Integrada: Licenciamento Ambiental, Desmatamento & Modelagem Estatística - Brasil",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #0F172A; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #475569; margin-bottom: 1.5rem; }
    .card { background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; }
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
PDF_DIR = os.path.join(BASE_DIR, "reports_pdf")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# ==========================================

# SIDEBAR FINANCEIRO
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)
st.sidebar.title("Módulo Financeiro e BNDES")
state_names = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "IBAMA": "Âmbito Federal (IBAMA)",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins"
}

if True:
    st.markdown('<div class="sub-header">Mapeamento empírico da relação de capital, contratos de financiamento e escala de empreendimentos por modalidade de licença.</div>', unsafe_allow_html=True)

    bench_json = os.path.join(BASE_DIR, "acre_bndes_benchmark.json")
    try:
        df_bench = pd.read_json(bench_json)
    except Exception as e:
        st.error(f"Erro ao carregar benchmark financeiro: {e}")
        st.stop()

    # Benchmark KPIs
    b1, b2, b3, b4 = st.columns(4)
    tot_val = df_bench.drop_duplicates(subset=['doc_num'])['bndes_total_contratado'].sum()
    med_val = df_bench.drop_duplicates(subset=['doc_num'])['bndes_total_contratado'].median()
    
    b1.metric("Licenças Cruzadas com BNDES", f"{len(df_bench):,}")
    b2.metric("Empresas Únicas Financiadas", f"{df_bench['doc_num'].nunique():,}")
    b3.metric("Volume Financiado (BNDES)", f"R$ {tot_val/1e9:.2f} Bilhões")
    b4.metric("Mediana Financiada / Empresa", f"R$ {med_val/1e6:.2f} Mi")

    st.markdown("---")

    b_tab1, b_tab2, b_tab3, b_tab4, b_tab5 = st.tabs([
        "📊 Mediana e Média por Tipo de Licença",
        "🏢 Distribuição por Porte e Subsetor",
        "🔎 Explorador de Empresas & CNPJ",
        "🗺️ Viabilidade de Estimativa Financeira por Estado & Tipo",
        "🔬 Experimento Bahia: Licenciamento vs BNDES vs PAC"
    ])

    with b_tab1:
        st.subheader("1. Mediana do Investimento por Modalidade de Licença")
        st.caption("A mediana é o indicador mais robusto para representar o valor financeiro típico associado a cada tipo de licença.")
        
        bench_grp = df_bench.groupby('tipo_licenca').agg(
            licencas=('doc_num', 'count'),
            empresas=('doc_num', 'nunique'),
            mediana=('bndes_total_contratado', 'median'),
            media=('bndes_total_contratado', 'mean'),
            total=('bndes_total_contratado', 'sum')
        ).reset_index().sort_values(by='mediana', ascending=False)
        
        fig_b_bar = px.bar(
            bench_grp,
            x='tipo_licenca',
            y='mediana',
            color='tipo_licenca',
            text='mediana',
            labels={'tipo_licenca': 'Tipo de Licença', 'mediana': 'Mediana Financiada (R$)'},
            title="Mediana de Valor Financiado por Tipo de Licença (R$)"
        )
        fig_b_bar.update_traces(texttemplate='R$ %{text:,.0f}', textposition='outside')
        fig_b_bar.update_layout(showlegend=False, xaxis_tickangle=-30, height=450)
        st.plotly_chart(fig_b_bar, use_container_width=True)
        
        st.markdown("### Tabela Detalhada de Benchmark")
        t_display = bench_grp.copy()
        t_display['Mediana (R$)'] = t_display['mediana'].apply(lambda x: f"R$ {x:,.2f}")
        t_display['Média (R$)'] = t_display['media'].apply(lambda x: f"R$ {x:,.2f}")
        t_display['Total (R$)'] = t_display['total'].apply(lambda x: f"R$ {x:,.2f}")
        st.dataframe(t_display[['tipo_licenca', 'licencas', 'empresas', 'Mediana (R$)', 'Média (R$)', 'Total (R$)']], use_container_width=True)

    with b_tab2:
        st.subheader("2. Distribuição por Porte do Empreendimento e Setor Econômico")
        c1, c2 = st.columns(2)
        with c1:
            fig_bx = px.box(
                df_bench,
                x='porte',
                y='bndes_total_contratado',
                color='porte',
                log_y=True,
                labels={'porte': 'Porte Declarado', 'bndes_total_contratado': 'Valor Financiado (R$ escala log)'},
                title="Dispersão do Investimento por Porte Declarado"
            )
            st.plotly_chart(fig_bx, use_container_width=True)
        with c2:
            top_subs = df_bench['bndes_subsetor'].value_counts().head(8).reset_index()
            top_subs.columns = ['subsetor', 'contagem']
            fig_p = px.pie(top_subs, names='subsetor', values='contagem', title="Principais Subsetores Financiados com Licença")
            st.plotly_chart(fig_p, use_container_width=True)

    with b_tab3:
        st.subheader("3. Consulta Direta por Empresa ou CNPJ")
        q = st.text_input("Filtrar por Razão Social, Nome do Empreendimento ou CNPJ:", "")
        df_view = df_bench.copy()
        if q:
            df_view = df_view[
                df_view['nome_empreendimento'].astype(str).str.contains(q, case=False, na=False) |
                df_view['bndes_cliente'].astype(str).str.contains(q, case=False, na=False) |
                df_view['doc_num'].astype(str).str.contains(q, case=False, na=False)
            ]
        st.write(f"Mostrando **{len(df_view):,}** registros encontrados.")
        st.dataframe(
            df_view[[
                'doc_num', 'bndes_cliente', 'nome_empreendimento', 'tipo_licenca',
                'porte', 'ano', 'bndes_total_contratado', 'bndes_subsetor'
            ]].rename(columns={
                'doc_num': 'CNPJ',
                'bndes_cliente': 'Cliente (BNDES)',
                'nome_empreendimento': 'Nome Empreendimento',
                'tipo_licenca': 'Tipo de Licença',
                'porte': 'Porte',
                'ano': 'Ano',
                'bndes_total_contratado': 'Total Financiado (R$)',
                'bndes_subsetor': 'Subsetor'
            }),
            use_container_width=True
        )

    with b_tab4:
        st.subheader("4. Matriz de Viabilidade para Estimativa Financeira: Estados & Modalidades de Licença")
        st.markdown("""
        Esta seção detalha **em quais estados e para quais tipos de licença** é metodologicamente viável utilizar dados financeiros 
        (seja via **custo administrativo/taxa de análise estadual** ou via **escala de investimento/CAPEX pelo BNDES**) para estimar a dimensão econômica do licenciamento.
        """)
        
        f_estados_path = os.path.join(DATA_DIR, "viabilidade_financeira_estados.json")
        f_licencas_path = os.path.join(DATA_DIR, "viabilidade_financeira_licencas.json")
        
        try:
            with open(f_estados_path, 'r', encoding='utf-8') as f1, open(f_licencas_path, 'r', encoding='utf-8') as f2:
                viab_estados = json.load(f1)
                viab_licencas = json.load(f2)
            df_v_est = pd.DataFrame(viab_estados)
            df_v_lic = pd.DataFrame(viab_licencas)
        except Exception as e:
            st.error(f"Erro ao carregar dados de viabilidade: {e}")
            st.stop()
            
        st.markdown("### A. Viabilidade de Estimativa por Estado e Órgão Regulador")
        st.caption("Classificação baseada na qualidade de CNPJs no banco de dados, presença do porte (P, M, G) e clareza da tabela normativa de taxas e custos.")
        
        st.dataframe(
            df_v_est.rename(columns={
                'uf': 'UF',
                'estado': 'Estado / Âmbito',
                'orgao': 'Órgão Ambiental',
                'viabilidade_financeira': 'Grau de Viabilidade',
                'nivel_precisao': 'Métrica Normativa',
                'metodo_indicado': 'Metodologia de Estimativa Recomendada',
                'cobertura_dados': 'Qualidade do Cadastro',
                'licencas_prioritarias': 'Modalidades com Alta Resolução'
            }),
            use_container_width=True
        )
        
        st.markdown("---")
        st.markdown("### B. Viabilidade de Estimativa por Modalidade de Licenciamento")
        st.caption("Quais tipos de licença possuem correlação direta com o orçamento e investimentos da empresa.")
        
        st.dataframe(
            df_v_lic.rename(columns={
                'tipo_licenca': 'Modalidade de Licença',
                'grau_viabilidade': 'Acurácia Financeira Estimável',
                'relacao_financeira': 'Dimensão Econômica Representada',
                'fonte_estimativa': 'Base de Dados de Referência',
                'aplicabilidade': 'Aplicação Prática no Brasil'
            }),
            use_container_width=True
        )
        
        st.info("""
        💡 **Síntese Metodológica:**
        - **Para Licenças Trifásicas (LP, LI, LO):** Os estados com sistemas analíticos maduros (**SP/CETESB, MG/COPAM, RJ/INEA, PR/IAT, RS/FEPAM e IBAMA**) permitem estimar tanto a **taxa administrativa de análise** (via fórmulas matemáticas paramétricas publicadas) quanto o **volume total de investimento das empresas** (via cruzamento por CNPJ com o BNDES).
        - **Para Licenças Simplificadas e Rurais (LAU, LAC, LARS, CAR):** A estimativa é parametrizada com alta precisão através do porte do imóvel (módulos fiscais) ou faixa de faturamento presumido das PMEs.
        """)


    with b_tab5:
        render_bahia_experimental_tab()


# ==============================================================================
# MÓDULO 5: MAPA GEOESPACIAL (LEAFLET / FOLIUM)
# ==============================================================================
