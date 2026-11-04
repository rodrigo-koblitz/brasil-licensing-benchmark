import os
import json
import base64
import glob
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Plataforma Integrada: Licenciamento Ambiental, Desmatamento & Benchmark - Brasil",
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
# SIDEBAR NAVIGATION (Three Main Modules)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)
st.sidebar.title("Navegação Principal")
modulo = st.sidebar.radio(
    "Selecione o Módulo:",
    options=[
        "🌱 Licenciamento Ambiental Brasil",
        "🌳 Desmatamento (MapBiomas)",
        "📊 Benchmark Financeiro & BNDES"
    ],
    index=0
)

# State mapping helper
state_names = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "AP": "Amapá", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "IBAMA": "Âmbito Federal (IBAMA)",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte", "RO": "Rondônia", "RR": "Roraima",
    "RS": "Rio Grande do Sul", "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo", "TO": "Tocantins"
}

# ==============================================================================
# MÓDULO 1: LICENCIAMENTO AMBIENTAL BRASIL
# ==============================================================================
if modulo == "🌱 Licenciamento Ambiental Brasil":
    st.markdown('<div class="main-header">🌱 Panorama e Processamento de Licenciamento Ambiental no Brasil</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Acompanhamento consolidado do esforço de licenciamento ambiental, evolução temporal e acervo documental oficial de 25 estados brasileiros e do IBAMA.</div>', unsafe_allow_html=True)

    csv_file = os.path.join(DATA_DIR, "brasil_estados_consolidado.csv")
    ts_file = os.path.join(DATA_DIR, "serie_temporal_nacional.json")

    try:
        df_estados = pd.read_csv(csv_file)
        with open(ts_file, 'r', encoding='utf-8') as f:
            ts_data = json.load(f)
    except Exception as e:
        st.error(f"Erro ao carregar dados consolidados: {e}")
        st.stop()

    # Macro Metrics
    m1, m2, m3, m4 = st.columns(4)
    tot_lic = df_estados['total_licencas'].sum()
    tot_emp = df_estados['total_empreendimentos'].dropna().sum()
    m1.metric("Total de Atos / Licenças", f"{tot_lic:,.0f}".replace(",", "."))
    m2.metric("Empreendimentos Registrados", f"{tot_emp:,.0f}".replace(",", "."))
    m3.metric("Órgãos / UFs Analisados", f"{len(df_estados)}")
    m4.metric("Estado Líder em Volume", f"{df_estados.iloc[0]['sigla']} ({df_estados.iloc[0]['total_licencas']:,.0f})")

    st.markdown("---")

    tab_macro, tab_reports, tab_visuals, tab_export = st.tabs([
        "📈 Séries Temporais & Macro Ranking",
        "📄 Relatórios Estaduais Completos (PDF)",
        "🖼️ Painéis Visuais Compilados",
        "📥 Base de Dados Consolidada (CSV / JSON)"
    ])

    with tab_macro:
        st.subheader("1. Evolução Histórica Nacional (2000 – 2026)")
        years = [str(y) for y in ts_data['years']]
        nat_lic_dict = ts_data['national_total_licenses_by_year']
        nat_emp_dict = ts_data['national_total_enterprises_by_year']
        
        lic_vals = [nat_lic_dict.get(y, 0) for y in years]
        emp_vals = [nat_emp_dict.get(y, 0) for y in years]
        
        df_ts = pd.DataFrame({
            'Ano': [int(y) for y in years],
            'Licenças Emitidas': lic_vals,
            'Empreendimentos Ativos': emp_vals
        })
        
        fig_ts = go.Figure()
        fig_ts.add_trace(go.Scatter(
            x=df_ts['Ano'], y=df_ts['Licenças Emitidas'],
            mode='lines+markers', name='Total de Licenças Emitidas',
            line=dict(color='#059669', width=3)
        ))
        fig_ts.add_trace(go.Scatter(
            x=df_ts['Ano'], y=df_ts['Empreendimentos Ativos'],
            mode='lines+markers', name='Empreendimentos Ativos',
            line=dict(color='#2563EB', width=2, dash='dot')
        ))
        fig_ts.update_layout(
            title="Série Histórica Anual: Licenças vs. Empreendimentos (Brasil)",
            xaxis_title="Ano",
            yaxis_title="Volume",
            hovermode="x unified",
            height=430
        )
        st.plotly_chart(fig_ts, use_container_width=True)

        st.subheader("2. Comparativo de Volume por Unidade Federativa")
        col_g1, col_g2 = st.columns([2, 1])
        with col_g1:
            fig_bar = px.bar(
                df_estados.sort_values(by='total_licencas', ascending=True),
                x='total_licencas',
                y='sigla',
                orientation='h',
                text='total_licencas',
                color='total_licencas',
                color_continuous_scale='Greens',
                labels={'total_licencas': 'Licenças', 'sigla': 'Estado'},
                title="Ranking de Licenças Emitidas por UF"
            )
            fig_bar.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_bar.update_layout(height=600, coloraxis_showscale=False)
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_g2:
            st.markdown("### Ranking Detalhado")
            st.dataframe(
                df_estados[['sigla', 'estado', 'total_licencas', 'total_empreendimentos']].rename(columns={
                    'sigla': 'UF', 'estado': 'Estado', 'total_licencas': 'Licenças', 'total_empreendimentos': 'Empreendimentos'
                }),
                height=560,
                use_container_width=True
            )

    with tab_reports:
        st.subheader("Leitor e Repositório dos Relatórios Técnicos por Estado")
        st.caption("Documentos oficiais detalhados com tipologias, potencial poluidor, base normativa e esforço temporal.")
        
        pdf_files = sorted(glob.glob(os.path.join(PDF_DIR, "*_analysis.pdf")))
        if not pdf_files:
            st.warning("Relatórios PDF não encontrados no servidor.")
        else:
            file_dict = {}
            for p in pdf_files:
                code = os.path.basename(p).replace("_analysis.pdf", "")
                label = f"{code} - {state_names.get(code, code)}"
                file_dict[label] = (code, p)
                
            col_sel, col_btn = st.columns([2, 1])
            with col_sel:
                selected_label = st.selectbox(
                    "Selecione o Estado / Órgão:",
                    options=list(file_dict.keys()),
                    index=0
                )
            
            sel_code, sel_path = file_dict[selected_label]
            with open(sel_path, "rb") as f:
                pdf_bytes = f.read()
                
            with col_btn:
                st.write(f"Tamanho: {len(pdf_bytes)/1024:,.1f} KB")
                st.download_button(
                    label=f"📥 Baixar Relatório {sel_code} (PDF)",
                    data=pdf_bytes,
                    file_name=f"{sel_code}_analysis.pdf",
                    mime="application/pdf"
                )
            
            base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_embed = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="850" type="application/pdf" style="border: 1px solid #CBD5E1; border-radius: 8px;"></iframe>'
            st.markdown(pdf_embed, unsafe_allow_html=True)

    with tab_visuals:
        st.subheader("Painéis Gráficos Nacionais Compilados")
        chart_options = {
            "Painel Geral do Brasil (Overall of Overall)": "overall_of_overall.png",
            "Empreendimentos e Estados por Ano (Time Series)": "all_enterprises_and_states_by_year.png",
            "Empilhamento Anual de Empreendimentos por Estado": "all_states_enterprises_stacked_by_year.png",
            "Dashboard Regional Consolidado": "all_enterprises_by_region_dashboard.png",
            "Empreendimentos por Grande Região Geográfica": "all_enterprises_by_region_stacked_by_year.png"
        }
        
        selected_chart = st.selectbox("Selecione o Gráfico para Ampliar:", list(chart_options.keys()))
        img_path = os.path.join(STATIC_DIR, chart_options[selected_chart])
        if os.path.exists(img_path):
            st.image(img_path, use_container_width=True)
            with open(img_path, "rb") as img_f:
                st.download_button(
                    label=f"📥 Baixar Gráfico em Alta Resolução ({chart_options[selected_chart]})",
                    data=img_f.read(),
                    file_name=chart_options[selected_chart],
                    mime="image/png"
                )

    with tab_export:
        st.subheader("Base de Dados Consolidada Nacional")
        st.write("Baixe a tabela completa unificada com todos os estados brasileiros em formato aberto para análise.")
        
        c_csv, c_json = st.columns(2)
        with c_csv:
            csv_data = df_estados.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Base Consolidada (CSV)", data=csv_data, file_name="brasil_estados_licenciamento.csv", mime="text/csv")
        with c_json:
            json_data = df_estados.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8')
            st.download_button("📥 Baixar Base Consolidada (JSON)", data=json_data, file_name="brasil_estados_licenciamento.json", mime="application/json")
            
        st.dataframe(df_estados.rename(columns={
            'sigla': 'UF', 'estado': 'Estado', 'total_licencas': 'Total Licenças',
            'total_empreendimentos': 'Empreendimentos', 'ano_inicio': 'Ano Inicial',
            'ano_fim': 'Ano Final', 'total_tipologias': 'Tipologias Distintas',
            'principais_licencas': 'Principais Licenças Registradas'
        }), use_container_width=True)

# ==============================================================================
# MÓDULO 2: DESMATAMENTO (MAPBIOMAS)
# ==============================================================================
elif modulo == "🌳 Desmatamento (MapBiomas)":
    st.markdown('<div class="main-header">🌳 Desmatamento & Supressão de Vegetação Nativa (MapBiomas)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Monitoramento e estatísticas oficiais de desmatamento anual no Brasil por Estado e Bioma (Série Histórica MapBiomas Coleção 11 – Resolução Espacial 30m / Landsat).</div>', unsafe_allow_html=True)

    # Load Deforestation Datasets
    f_uf = os.path.join(DATA_DIR, "mapbiomas_desmatamento_estado_ano.csv")
    f_bioma = os.path.join(DATA_DIR, "mapbiomas_desmatamento_bioma_ano.csv")
    f_br = os.path.join(DATA_DIR, "mapbiomas_desmatamento_brasil_ano.csv")

    try:
        df_desm_uf = pd.read_csv(f_uf)
        df_desm_bioma = pd.read_csv(f_bioma)
        df_desm_br = pd.read_csv(f_br)
    except Exception as e:
        st.error(f"Erro ao carregar dados de desmatamento: {e}")
        st.stop()

    # KPIs (Year 2024 / Total Cumulative 2000-2025)
    d1, d2, d3, d4 = st.columns(4)
    total_acum_ha = df_desm_br['area_ha'].sum()
    total_acum_km2 = df_desm_br['area_km2'].sum()
    ultimo_ano = int(df_desm_br['ano'].max())
    taxa_ultimo_ano_ha = df_desm_br[df_desm_br['ano'] == ultimo_ano]['area_ha'].values[0]

    d1.metric("Desmatamento Acumulado (2000-2025)", f"{total_acum_km2:,.0f} km²")
    d2.metric("Área Total Suprimida", f"{total_acum_ha/1e6:,.2f} Milhões ha")
    d3.metric(f"Taxa Anual ({ultimo_ano})", f"{taxa_ultimo_ano_ha/1e3:,.1f} mil ha")
    d4.metric("Resolução Espacial Satélite", "30 metros (Landsat)")

    st.markdown("---")

    d_tab1, d_tab2, d_tab3, d_tab4, d_tab5 = st.tabs([
        "📈 Série Histórica por Estado & Bioma",
        "🗺️ Ranking Anual de Desmatamento",
        "⚖️ Cruzamento Licenciamento vs. Desmatamento",
        "📥 Download das Séries Temporais (CSV/JSON)",
        "📑 Relatório Metodológico MapBiomas"
    ])

    with d_tab1:
        st.subheader("1. Evolução Histórica Anual do Desmatamento")
        
        # Metric Selector
        unidade = st.radio("Unidade de Visualização:", ["Hectares (ha)", "Quilômetros Quadrados (km²)"], horizontal=True)
        col_area = 'area_ha' if unidade == "Hectares (ha)" else 'area_km2'
        
        # State Filter
        ufs_disponiveis = sorted(df_desm_uf['UF'].unique())
        selected_ufs = st.multiselect(
            "Selecione os Estados para comparar a curva de desmatamento:",
            options=ufs_disponiveis,
            default=['PA', 'MT', 'MA', 'RO', 'BA']
        )
        
        if selected_ufs:
            sub_uf = df_desm_uf[df_desm_uf['UF'].isin(selected_ufs)]
            fig_d_uf = px.line(
                sub_uf,
                x='ano',
                y=col_area,
                color='UF',
                markers=True,
                labels={'ano': 'Ano', col_area: f'Área Suprimida ({unidade})', 'UF': 'Estado'},
                title=f"Série Histórica de Desmatamento por Estado ({unidade})"
            )
            fig_d_uf.update_layout(height=450, hovermode="x unified")
            st.plotly_chart(fig_d_uf, use_container_width=True)
            
        st.subheader("Evolução Histórica por Bioma")
        fig_bioma = px.area(
            df_desm_bioma,
            x='ano',
            y=col_area,
            color='BIOME',
            labels={'ano': 'Ano', col_area: f'Área Suprimida ({unidade})', 'BIOME': 'Bioma'},
            title=f"Desmatamento Anual por Bioma Brasileiro ({unidade})"
        )
        fig_bioma.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig_bioma, use_container_width=True)

    with d_tab2:
        st.subheader("2. Ranking e Concentração do Desmatamento por Estado")
        
        ano_selecionado = st.slider("Selecione o Ano para Ranking:", min_value=2000, max_value=ultimo_ano, value=2024, step=1)
        df_ano_uf = df_desm_uf[df_desm_uf['ano'] == ano_selecionado].sort_values(by='area_ha', ascending=False)
        
        col_rank_chart, col_rank_table = st.columns([2, 1])
        with col_rank_chart:
            fig_rank_bar = px.bar(
                df_ano_uf.sort_values(by='area_ha', ascending=True),
                x='area_ha',
                y='UF',
                orientation='h',
                text='area_ha',
                color='area_ha',
                color_continuous_scale='Reds',
                labels={'area_ha': 'Área Desmatada (ha)', 'UF': 'Estado'},
                title=f"Ranking de Desmatamento por UF no Ano {ano_selecionado} (Hectares)"
            )
            fig_rank_bar.update_traces(texttemplate='%{text:,.0f} ha', textposition='outside')
            fig_rank_bar.update_layout(height=650, coloraxis_showscale=False)
            st.plotly_chart(fig_rank_bar, use_container_width=True)
            
        with col_rank_table:
            st.markdown(f"### Tabela do Ano {ano_selecionado}")
            st.dataframe(
                df_ano_uf[['UF', 'area_ha', 'area_km2']].rename(columns={
                    'UF': 'Estado',
                    'area_ha': 'Área (ha)',
                    'area_km2': 'Área (km²)'
                }),
                height=600,
                use_container_width=True
            )

    with d_tab3:
        st.subheader("3. Cruzamento: Licenciamento Ambiental vs. Curva de Desmatamento")
        st.caption("Compara a dinâmica temporal entre o número de licenças emitidas pelos órgãos ambientais e o desmatamento registrado no mesmo estado.")
        
        ts_lic_file = os.path.join(DATA_DIR, "serie_temporal_nacional.json")
        with open(ts_lic_file, 'r', encoding='utf-8') as f:
            lic_ts_data = json.load(f)
            
        state_choices = sorted([s for s in lic_ts_data['states'] if s in df_desm_uf['UF'].unique()])
        sel_cross_state = st.selectbox("Selecione o Estado para Cruzamento:", state_choices, index=0)
        
        # Prepare merged timeseries
        lic_years = [str(y) for y in lic_ts_data['years']]
        state_lics = lic_ts_data['state_year_licenses'].get(sel_cross_state, {})
        lic_curve = [state_lics.get(y, 0) for y in lic_years]
        
        df_lic_st = pd.DataFrame({'ano': [int(y) for y in lic_years], 'licencas': lic_curve})
        df_desm_st = df_desm_uf[df_desm_uf['UF'] == sel_cross_state][['ano', 'area_ha', 'area_km2']]
        
        df_cross = pd.merge(df_lic_st, df_desm_st, on='ano', how='inner')
        
        # Dual axis line chart
        fig_cross = go.Figure()
        fig_cross.add_trace(go.Scatter(
            x=df_cross['ano'], y=df_cross['licencas'],
            name='Licenças Emitidas',
            mode='lines+markers',
            line=dict(color='#059669', width=3),
            yaxis='y1'
        ))
        fig_cross.add_trace(go.Scatter(
            x=df_cross['ano'], y=df_cross['area_ha'],
            name='Desmatamento MapBiomas (ha)',
            mode='lines+markers',
            line=dict(color='#DC2626', width=3, dash='dot'),
            yaxis='y2'
        ))
        fig_cross.update_layout(
            title=f"Cruzamento Temporal: Licenças Emitidas vs. Desmatamento - {sel_cross_state} ({state_names.get(sel_cross_state, sel_cross_state)})",
            xaxis=dict(title='Ano'),
            yaxis=dict(title='Volume de Licenças Emitidas', titlefont=dict(color='#059669'), tickfont=dict(color='#059669')),
            yaxis2=dict(title='Área Desmatada (ha)', titlefont=dict(color='#DC2626'), tickfont=dict(color='#DC2626'), overlaying='y', side='right'),
            hovermode="x unified",
            height=480
        )
        st.plotly_chart(fig_cross, use_container_width=True)

    with d_tab4:
        st.subheader("4. Base de Dados Oficial de Desmatamento (Download)")
        st.write("Baixe a base de dados tratada de desmatamento anual em formato aberto para análises espaciais e estatísticas.")
        
        dc1, dc2 = st.columns(2)
        with dc1:
            csv_d_uf = df_desm_uf.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Desmatamento por Estado e Ano (CSV)", data=csv_d_uf, file_name="mapbiomas_desmatamento_estado_ano.csv", mime="text/csv")
        with dc2:
            json_d_uf = df_desm_uf.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8')
            st.download_button("📥 Baixar Desmatamento por Estado e Ano (JSON)", data=json_d_uf, file_name="mapbiomas_desmatamento_estado_ano.json", mime="application/json")
            
        st.dataframe(df_desm_uf.rename(columns={'UF': 'Estado', 'ano': 'Ano', 'area_ha': 'Área (ha)', 'area_km2': 'Área (km²)'}), use_container_width=True)

    with d_tab5:
        st.subheader("5. Relatório Metodológico e Esclarecimento de Resolução Espacial")
        st.markdown("""
        ### Fonte e Curadoria dos Dados
        - **Iniciativa:** Rede MapBiomas Brasil (Coleção 11 - Módulo Desmatamento / Perda de Vegetação Nativa).
        - **Sensor / Satélite:** Constelação **Landsat** (Landsat 5, 7, 8 e 9 - NASA/USGS) com processamento pixel a pixel em nuvem no **Google Earth Engine (GEE)**.
        - **Resolução Espacial Padronizada:** **30 metros** $\times$ **30 metros** ($900\,m^2$ por pixel no solo).
        - **Série Histórica Contínua:** Mapeada anualmente de **1985 até o presente**.
        
        ### Diferenciação Crítica de Resoluções no Ecossistema MapBiomas:
        1. **MapBiomas Desmatamento Anual (30 metros - Adotado Aqui):**
           - Permite séries históricas homogêneas desde 1985 e consolidadas de 2000 em diante.
           - Mantém a mesma resolução de 30m em todos os anos, sem quebras metodológicas ou alterações de escala.
        2. **MapBiomas Alerta (3 metros - PlanetScope):**
           - Voltado para alertas rápidos semanais e laudos de fiscalização territorial imediata.
           - Não possui série histórica longa, estando disponível apenas a partir de **2019**.
        """)

# ==============================================================================
# MÓDULO 3: BENCHMARK FINANCEIRO & BNDES
# ==============================================================================
elif modulo == "📊 Benchmark Financeiro & BNDES":
    st.markdown('<div class="main-header">📊 Benchmark Financeiro de Licenciamento & Investimento BNDES</div>', unsafe_allow_html=True)
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

    b_tab1, b_tab2, b_tab3, b_tab4 = st.tabs([
        "📊 Mediana e Média por Tipo de Licença",
        "🏢 Distribuição por Porte e Subsetor",
        "🔎 Explorador de Empresas & CNPJ",
        "🗺️ Viabilidade de Estimativa Financeira por Estado & Tipo"
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
