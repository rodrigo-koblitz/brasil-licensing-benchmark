from tab_bahia_experimental import render_bahia_experimental_tab
import os
import json
import base64
import glob
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from map_module import render_map_module
from agro_module import render_agro_module

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
# SIDEBAR NAVIGATION (Four Main Modules)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)
st.sidebar.title("Navegação Principal")
modulo = st.sidebar.radio(
    "Selecione o Módulo:",
    options=[
        "🌱 Licenciamento Ambiental Brasil",
        "🌳 Desmatamento (MapBiomas)",
        "⚖️ Modelagem: Desmatamento X Licenciamento",
        "📊 Benchmark Financeiro & BNDES",
        "🌾 Financiamento & Seguro Agropecuário",
        "🗺️ Mapa Geoespacial: Desmatamento & Licenças"
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

    tab_macro, tab_reports, tab_visuals, tab_metodologia, tab_export = st.tabs([
        "📈 Séries Temporais & Macro Ranking",
        "📄 Relatórios Estaduais Completos (PDF)",
        "🖼️ Painéis Visuais Compilados",
        "📋 Metodologia & Dados Nacionais",
        "📥 Base de Dados Consolidada (CSV / Planilhas)"
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

        st.markdown("---")
        st.subheader("2. Evolução Temporal: Licenciamento vs. Investimento Federal e Crédito (2000–2025)")
        st.caption("Cruzamento do volume nacional de atos autorizativos emitidos pelos órgãos ambientais com desembolsos do BNDES, investimentos do PAC e produção agrícola.")

        # Load national integrated panel
        nat_panel_path = os.path.join(DATA_DIR, "serie_nacional_licenciamento_investimento_credito_2000_2025.parquet")
        if os.path.exists(nat_panel_path):
            df_nat_panel = pd.read_parquet(nat_panel_path)
            
            # Selector for price adjustment
            c_p1, c_p2 = st.columns([2, 3])
            with c_p1:
                regime_nat = st.selectbox(
                    "Métrica Financeira:",
                    options=["Valores Nominais (Históricos)", "Poder de Compra Real (IPCA - R$ de 2024)", "Custo de Oportunidade Real (Selic Real)"],
                    index=0,
                    key="regime_nat_lic"
                )
            
            if regime_nat == "Poder de Compra Real (IPCA - R$ de 2024)":
                bndes_c = 'bndes_desembolsado_bi_reais_ipca'
                pac_c = 'pac_investimento_total_bi_reais_ipca'
                agro_c = 'agro_producao_bi_reais_ipca'
                leg_suf = "Real IPCA (R$ Bi)"
            elif regime_nat == "Custo de Oportunidade Real (Selic Real)":
                bndes_c = 'bndes_desembolsado_bi_reais_selic_real'
                pac_c = 'pac_investimento_total_bi_reais_selic_real'
                agro_c = 'agro_producao_bi_reais_selic_real'
                leg_suf = "Selic Real (R$ Bi)"
            else:
                bndes_c = 'bndes_desembolsado_bi_reais'
                pac_c = 'pac_investimento_total_bi_reais'
                agro_c = 'agro_producao_bi_reais'
                leg_suf = "Nominal (R$ Bi)"

            fig_cross = go.Figure()
            # Eixo 1: Licenças (Esquerda)
            fig_cross.add_trace(go.Scatter(
                x=df_nat_panel['ano'], y=df_nat_panel['licencas_ambientais_emitidas'],
                name="Licenças Ambientais Emitidas",
                mode='lines+markers',
                line=dict(color='#059669', width=3.5),
                yaxis='y1'
            ))
            # Eixo 2: Financiamento BNDES (Direita)
            fig_cross.add_trace(go.Bar(
                x=df_nat_panel['ano'] - 0.2, y=df_nat_panel[bndes_c],
                name=f"BNDES Desembolsos ({leg_suf})",
                marker_color='#2563EB',
                opacity=0.75,
                yaxis='y2'
            ))
            # Eixo 2: Investimento PAC (Direita)
            fig_cross.add_trace(go.Bar(
                x=df_nat_panel['ano'] + 0.2, y=df_nat_panel[pac_c],
                name=f"PAC Investimento Total ({leg_suf})",
                marker_color='#F59E0B',
                opacity=0.75,
                yaxis='y2'
            ))
            # Eixo 2: Produção Agropecuária (Direita)
            fig_cross.add_trace(go.Scatter(
                x=df_nat_panel['ano'], y=df_nat_panel[agro_c],
                name=f"Produção Agropecuária IBGE ({leg_suf})",
                mode='lines+markers',
                line=dict(color='#10B981', width=2, dash='dash'),
                yaxis='y2'
            ))

            fig_cross.update_layout(
                title=f"Evolução Temporal: Licenciamento vs. Investimento Federal e Crédito ({regime_nat})",
                xaxis=dict(title="Ano", tickmode='linear', tick0=2000, dtick=2),
                yaxis=dict(
                    title=dict(text="Licenças Ambientais Emitidas", font=dict(color="#059669")),
                    tickfont=dict(color="#059669")
                ),
                yaxis2=dict(
                    title=dict(text=f"Recursos Financeiros ({leg_suf})", font=dict(color="#1E3A8A")),
                    tickfont=dict(color="#1E3A8A"),
                    overlaying='y',
                    side='right'
                ),
                legend=dict(x=0.01, y=0.98, bgcolor="rgba(255,255,255,0.8)"),
                height=480,
                hovermode="x unified",
                margin=dict(l=20, r=20, t=50, b=20)
            )
            st.plotly_chart(fig_cross, use_container_width=True)
            
            # Brief analytical correlation metric
            corr_bndes = df_nat_panel[['licencas_ambientais_emitidas', bndes_c]].dropna().corr().iloc[0, 1]
            corr_pac = df_nat_panel[['licencas_ambientais_emitidas', pac_c]].dropna().corr().iloc[0, 1]
            corr_agro = df_nat_panel[['licencas_ambientais_emitidas', agro_c]].dropna().corr().iloc[0, 1]
            
            st.markdown(f"""
            💡 **Correlação Temporal Direta (Pearson com Licenciamento):**
            - **BNDES:** $r = {corr_bndes:.2f}$ (associação com ciclos de crédito ao investimento produtivo)
            - **PAC:** $r = {corr_pac:.2f}$ (associação com fases de expansão de infraestrutura federal)
            - **Agropecuária:** $r = {corr_agro:.2f}$ (expansão de fronteira e regularização ambiental)
            """)

        st.markdown("---")
        st.subheader("3. Comparativo de Volume por Unidade Federativa")
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
            try:
                st.image(img_path, use_container_width=True)
            except TypeError:
                st.image(img_path, use_column_width=True)
            with open(img_path, "rb") as img_f:
                st.download_button(
                    label=f"📥 Baixar Gráfico em Alta Resolução ({chart_options[selected_chart]})",
                    data=img_f.read(),
                    file_name=chart_options[selected_chart],
                    mime="image/png"
                )

    with tab_metodologia:
        st.subheader("📋 Metodologia & Fontes de Dados em Escala Nacional")
        st.markdown("""
        Esta seção formaliza o protocolo de consolidação e integração das bases de dados nacionais que parametrizam o licenciamento ambiental e suas dimensões de investimento público e crédito de desenvolvimento:

        ### 1. Fontes de Dados Oficiais Integradas:
        * **Licenciamento Ambiental (Órgãos Estaduais & IBAMA):** Compilação de mais de 2,3 milhões de atos e licenças de 25 Unidades Federativas e do IBAMA, cobrindo modalidades prévias (LP), de instalação (LI), de operação (LO), autorizações ambientais (AA) e licenças simplificadas/rurais (LAC/CAR).
        * **Crédito de Longo Prazo e Financiamento (BNDES):** Microdados de operações de financiamento direto e indireto do Banco Nacional de Desenvolvimento Econômico e Social, com valores contratados e desembolsos associados a projetos estruturantes.
        * **Investimento em Infraestrutura Federal (PAC - Programa de Aceleração do Crescimento):** Painel de obras do Governo Federal (PAC 1, PAC 2 e Novo PAC), contemplando eixos de transportes, energia, saneamento e cidades.
        * **Valor da Produção Agropecuária & Seguro Rural (IBGE PAM & MAPA PSR):** Produção agrícola municipal agregada e subvenções federais ao seguro rural.

        ### 2. Tratamento Monetário e Correção Intertemporal:
        Para evitar distorções inflacionárias na comparação temporal (2000–2025), a base disponibiliza três regimes de comparabilidade:
        - **Nominal:** Valores originais declarados na data de contratação/emissão.
        - **Poder de Compra Real (IPCA):** Deflacionado pelo Índice Nacional de Preços ao Consumidor Amplo (SGS 433 / IBGE), trazendo todos os valores para Reais constantes de 2024.
        - **Custo de Oportunidade Real (Taxa Selic Real):** Deflacionado pela taxa real de juros ex-post $(1 + r_{\\text{real}}) = \\frac{1 + \\text{Selic}}{1 + \\text{IPCA}}$, expressando o rendimento do capital acima da inflação.

        ### 3. Matriz de Correlação e Dinâmica Macroeconômica:
        A modelagem estatística demonstra que picos de emissão de licenças de instalação e operação coincidem historicamente com as janelas de maior desembolso de recursos federais (PAC e BNDES), evidenciando o licenciamento como indicador antecedente ou concomitante à formação bruta de capital fixo.
        """)

    with tab_export:
        st.subheader("Base de Dados Consolidada Nacional & Planilhas de Integração")
        st.write("Baixe a tabela completa unificada com todos os estados brasileiros e o painel temporal integrado em formato aberto.")
        
        # Download National Integrated Panel
        nat_panel_path = os.path.join(DATA_DIR, "serie_nacional_licenciamento_investimento_credito_2000_2025.parquet")
        nat_xlsx_path = os.path.join(DATA_DIR, "serie_nacional_licenciamento_investimento_credito_2000_2025.xlsx")
        nat_csv_path = os.path.join(DATA_DIR, "serie_nacional_licenciamento_investimento_credito_2000_2025.csv")
        
        st.markdown("#### 📊 Painel Nacional Integrado: Licenciamento X BNDES X PAC X Agro (2000–2025)")
        c_p1, c_p2, c_p3 = st.columns(3)
        if os.path.exists(nat_xlsx_path):
            with open(nat_xlsx_path, "rb") as f_x:
                c_p1.download_button("📥 Baixar Planilha Excel (.xlsx)", data=f_x.read(), file_name="serie_nacional_licenciamento_investimento_credito_2000_2025.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        if os.path.exists(nat_csv_path):
            with open(nat_csv_path, "rb") as f_c:
                c_p2.download_button("📥 Baixar Tabela CSV (.csv)", data=f_c.read(), file_name="serie_nacional_licenciamento_investimento_credito_2000_2025.csv", mime="text/csv")
        if os.path.exists(nat_panel_path):
            with open(nat_panel_path, "rb") as f_pq:
                c_p3.download_button("📥 Baixar Parquet Otimizado (.parquet)", data=f_pq.read(), file_name="serie_nacional_licenciamento_investimento_credito_2000_2025.parquet")

        st.markdown("---")
        st.markdown("#### 🏛️ Base de Atos e Empreendimentos por Estado")
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

    # Areas territoriais oficiais IBGE (em hectares) para calculo proporcional
    ibge_areas_ha = {
        'AC': 16412370.0, 'AL': 2784330.0, 'AM': 155914690.0, 'AP': 14282850.0,
        'BA': 56476040.0, 'CE': 14889440.0, 'DF': 576080.0, 'ES': 4607440.0,
        'GO': 34024290.0, 'MA': 32965150.0, 'MG': 58651390.0, 'MS': 35714550.0,
        'MT': 90320700.0, 'PA': 124587070.0, 'PB': 5646720.0, 'PE': 9806790.0,
        'PI': 25175550.0, 'PR': 19929890.0, 'RJ': 4375040.0, 'RN': 5280960.0,
        'RO': 23776530.0, 'RR': 22364450.0, 'RS': 28170720.0, 'SC': 9573070.0,
        'SE': 2192540.0, 'SP': 24821950.0, 'TO': 27742360.0
    }
    area_brasil_ha = 851062960.0

    # Injetar colunas de percentual territorial
    df_desm_uf['area_estado_ha'] = df_desm_uf['UF'].map(ibge_areas_ha)
    df_desm_uf['pct_desmatamento'] = (df_desm_uf['area_ha'] / df_desm_uf['area_estado_ha']) * 100.0
    df_desm_bioma['pct_desmatamento'] = (df_desm_bioma['area_ha'] / area_brasil_ha) * 100.0

    # KPIs
    d1, d2, d3, d4 = st.columns(4)
    total_acum_ha = df_desm_br['area_ha'].sum()
    ultimo_ano = int(df_desm_br['ano'].max())
    taxa_ultimo_ano_ha = df_desm_br[df_desm_br['ano'] == ultimo_ano]['area_ha'].values[0]
    pct_acum_brasil = (total_acum_ha / area_brasil_ha) * 100.0
    pct_anual_brasil = (taxa_ultimo_ano_ha / area_brasil_ha) * 100.0

    d1.metric("Desmatamento Acumulado (2000-2025)", f"{pct_acum_brasil:.2f}% do Território")
    d2.metric("Área Total Suprimida", f"{total_acum_ha/1e6:,.2f} Milhões ha")
    d3.metric(f"Taxa Anual ({ultimo_ano})", f"{taxa_ultimo_ano_ha/1e3:,.1f} mil ha ({pct_anual_brasil:.3f}%)")
    d4.metric("Resolução Espacial Satélite", "30 metros (Landsat)")

    st.markdown("---")

    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs([
        "📈 Série Histórica por Estado & Bioma",
        "🗺️ Ranking Anual de Desmatamento",
        "📥 Download das Séries Temporais (CSV/JSON)",
        "📑 Relatório Metodológico MapBiomas"
    ])

    with d_tab1:
        st.subheader("1. Evolução Histórica Anual do Desmatamento")
        
        unidade = st.radio("Unidade de Visualização:", ["Hectares (ha)", "Percentual do Estado (%)"], horizontal=True)
        col_area = 'area_ha' if unidade == "Hectares (ha)" else 'pct_desmatamento'
        rotulo_unidade = "ha" if unidade == "Hectares (ha)" else "% do Estado"
        
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
                labels={'ano': 'Ano', col_area: f'Desmatamento ({rotulo_unidade})', 'UF': 'Estado'},
                title=f"Série Histórica de Desmatamento por Estado ({unidade})"
            )
            if col_area == 'pct_desmatamento':
                fig_d_uf.update_traces(hovertemplate='%{y:.3f}%')
            fig_d_uf.update_layout(height=450, hovermode="x unified")
            st.plotly_chart(fig_d_uf, use_container_width=True)
            
        st.subheader("Evolução Histórica por Bioma")
        fig_bioma = px.area(
            df_desm_bioma,
            x='ano',
            y='area_ha',
            color='BIOME',
            labels={'ano': 'Ano', 'area_ha': 'Área Suprimida (ha)', 'BIOME': 'Bioma'},
            title="Desmatamento Anual por Bioma Brasileiro (Hectares)"
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
            df_display = df_ano_uf[['UF', 'area_ha', 'pct_desmatamento']].copy()
            df_display['pct_desmatamento'] = df_display['pct_desmatamento'].apply(lambda x: f"{x:.3f}%")
            st.dataframe(
                df_display.rename(columns={
                    'UF': 'Estado',
                    'area_ha': 'Área (ha)',
                    'pct_desmatamento': '% do Estado'
                }),
                height=600,
                use_container_width=True
            )

    with d_tab3:
        st.subheader("3. Base de Dados Oficial de Desmatamento (Download)")
        st.write("Baixe a base de dados tratada de desmatamento anual em formato aberto para análises espaciais e estatísticas.")
        
        dc1, dc2 = st.columns(2)
        with dc1:
            csv_d_uf = df_desm_uf.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Desmatamento por Estado e Ano (CSV)", data=csv_d_uf, file_name="mapbiomas_desmatamento_estado_ano.csv", mime="text/csv")
        with dc2:
            json_d_uf = df_desm_uf.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8')
            st.download_button("📥 Baixar Desmatamento por Estado e Ano (JSON)", data=json_d_uf, file_name="mapbiomas_desmatamento_estado_ano.json", mime="application/json")
            
        st.dataframe(df_desm_uf.rename(columns={'UF': 'Estado', 'ano': 'Ano', 'area_ha': 'Área (ha)', 'area_km2': 'Área (km²)'}), use_container_width=True)

    with d_tab4:
        st.subheader("4. Relatório Metodológico e Esclarecimento de Resolução Espacial")
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
# MÓDULO 3: MODELAGEM ESTATÍSTICA: DESMATAMENTO X LICENCIAMENTO
# ==============================================================================
elif modulo == "⚖️ Modelagem: Desmatamento X Licenciamento":
    st.markdown('<div class="main-header">⚖️ Modelagem Estatística: Desmatamento X Licenciamento Ambiental</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Investigação econométrica da relação temporal entre modalidades de licenciamento e supressão florestal em três níveis: Brasil (Nacional), Regiões e Estados.</div>', unsafe_allow_html=True)

    # Load panel and correlation data
    f_panel = os.path.join(DATA_DIR, "painel_desmatamento_licenciamento_estado_ano.csv")
    f_corr = os.path.join(DATA_DIR, "correlacao_desmatamento_licenciamento.csv")

    try:
        df_panel = pd.read_csv(f_panel)
        df_corr = pd.read_csv(f_corr)
    except Exception as e:
        st.error(f"Erro ao carregar dados de modelagem: {e}")
        st.stop()

    macro_labels = {
        'TOTAL_LICENCAS': 'Total Geral de Licenças',
        'RURAL_VEG': 'Licenciamento Rural & Supressão (ASV/CAR/LAR/LARS)',
        'INFRA_CONSTR': 'Obras e Implantação (LP / LI / LPI)',
        'INFRA_OP': 'Operação e Funcionamento (LO / Regularização)',
        'SIMPLIF': 'Licenças Simplificadas / Únicas (LAU/LAC/LAS)',
        'MANEJO': 'Manejo Florestal Sustentável (PMFS/POA)'
    }

    # Top KPIs
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Painel de Dados Integrado", f"{len(df_panel):,} observações (UF x Ano)")
    k2.metric("Período Coberto", "2000 a 2025")
    k3.metric("Macro-Tipologias Analisadas", "6 Categorias")
    k4.metric("Estrutura de Defasagem", "Lags t (0) e t-1 (1 ano)")

    st.markdown("---")

    m_tab1, m_tab2, m_tab3, m_tab4 = st.tabs([
        "🇧🇷 1. Nível Nacional (Brasil)",
        "🗺️ 2. Nível Regional (Grandes Regiões)",
        "📍 3. Nível Estadual (Por UF)",
        "📐 4. Estratégia Metodológica & Painel Completo"
    ])

    with m_tab1:
        st.subheader("1. Análise em Escala Nacional (Brasil)")
        st.markdown("""
        Em nível agregado do país, avalia-se se picos na concessão de licenças (totais ou por modalidade) 
        coincidem ou precedem ciclos de maior ou menor supressão de vegetação nativa no território.
        """)

        df_nat_corr = df_corr[df_corr['escala'] == 'Brasil (Nacional)'].copy()
        df_nat_corr['Tipologia'] = df_nat_corr['macro_tipo'].map(macro_labels).fillna(df_nat_corr['macro_tipo'])
        
        # Heatmap / Bar chart of national correlations
        fig_nat_bar = px.bar(
            df_nat_corr,
            x='Tipologia',
            y='pearson_r',
            color='lag_anos',
            barmode='group',
            labels={'pearson_r': 'Coeficiente de Correlação de Pearson (r)', 'lag_anos': 'Defasagem (Lags em Anos)'},
            title="Correlação Linear entre Licenças e Desmatamento no Brasil (por Defasagem Temporal)"
        )
        fig_nat_bar.update_layout(height=420, xaxis_tickangle=-25)
        st.plotly_chart(fig_nat_bar, use_container_width=True)

        st.markdown("### Tabela de Coeficientes e Significância Estatística (Nacional)")
        st.dataframe(
            df_nat_corr[['Tipologia', 'lag_anos', 'pearson_r', 'p_valor', 'spearman_rho', 'n_observacoes']].rename(columns={
                'lag_anos': 'Defasagem (Anos)',
                'pearson_r': 'Pearson (r)',
                'p_valor': 'P-Valor',
                'spearman_rho': 'Spearman (rho)',
                'n_observacoes': 'Anos Analisados'
            }),
            use_container_width=True
        )

    with m_tab2:
        st.subheader("2. Análise por Grandes Regiões Geográficas")
        st.markdown("""
        O comportamento entre licenciamento e desmatamento varia radicalmente entre a **Fronteira Agrícola/Amazônica** 
        (Norte e Centro-Oeste) e as **Regiões Consolidadas** (Sudeste e Sul).
        """)

        df_reg_corr = df_corr[df_corr['escala'] == 'Regional'].copy()
        df_reg_corr['Tipologia'] = df_reg_corr['macro_tipo'].map(macro_labels).fillna(df_reg_corr['macro_tipo'])

        regioes = sorted(df_reg_corr['grupo'].unique())
        sel_reg = st.selectbox("Selecione a Região:", regioes, index=0)

        sub_reg = df_reg_corr[df_reg_corr['grupo'] == sel_reg]
        fig_reg_bar = px.bar(
            sub_reg,
            x='Tipologia',
            y='pearson_r',
            color='lag_anos',
            barmode='group',
            labels={'pearson_r': 'Coeficiente de Pearson (r)', 'lag_anos': 'Lag (Anos)'},
            title=f"Correlação entre Licenciamento e Desmatamento na Região {sel_reg}"
        )
        fig_reg_bar.update_layout(height=400, xaxis_tickangle=-25)
        st.plotly_chart(fig_reg_bar, use_container_width=True)

        st.dataframe(
            sub_reg[['Tipologia', 'lag_anos', 'pearson_r', 'p_valor']].rename(columns={
                'lag_anos': 'Defasagem (Anos)', 'pearson_r': 'Pearson (r)', 'p_valor': 'P-Valor'
            }),
            use_container_width=True
        )

    with m_tab3:
        st.subheader("3. Análise Detalhada por Estado (UF)")
        st.markdown("Investigação da dinâmica própria do órgão ambiental de cada unidade federativa.")

        df_st_corr = df_corr[df_corr['escala'] == 'Estadual'].copy()
        df_st_corr['Tipologia'] = df_st_corr['macro_tipo'].map(macro_labels).fillna(df_st_corr['macro_tipo'])

        ufs_disp = sorted(df_st_corr['grupo'].unique())
        sel_st = st.selectbox("Selecione o Estado:", ufs_disp, index=0)

        col_st_chart, col_st_data = st.columns([1, 1])

        with col_st_chart:
            sub_st = df_st_corr[df_st_corr['grupo'] == sel_st]
            fig_st_bar = px.bar(
                sub_st,
                x='Tipologia',
                y='pearson_r',
                color='lag_anos',
                barmode='group',
                labels={'pearson_r': 'Pearson (r)', 'lag_anos': 'Lag'},
                title=f"Correlações por Modalidade de Licença - {sel_st}"
            )
            fig_st_bar.update_layout(height=420, xaxis_tickangle=-30)
            st.plotly_chart(fig_st_bar, use_container_width=True)

        with col_st_data:
            # Dual-axis timeseries for this specific state
            sub_panel = df_panel[df_panel['UF'] == sel_st].sort_values('ano')
            
            fig_dual = go.Figure()
            fig_dual.add_trace(go.Scatter(
                x=sub_panel['ano'], y=sub_panel['TOTAL_LICENCAS'],
                name='Total de Licenças', mode='lines+markers', line=dict(color='#059669', width=2)
            ))
            fig_dual.add_trace(go.Scatter(
                x=sub_panel['ano'], y=sub_panel['area_ha'],
                name='Desmatamento (ha)', mode='lines+markers', line=dict(color='#DC2626', width=2, dash='dot'),
                yaxis='y2'
            ))
            fig_dual.update_layout(
                title=f"Série Histórica Conjunta: Licenças vs. Desmatamento - {sel_st}",
                xaxis=dict(title='Ano'),
                yaxis=dict(title=dict(text='Licenças', font=dict(color='#059669')), tickfont=dict(color='#059669')),
                yaxis2=dict(title=dict(text='Desmatamento (ha)', font=dict(color='#DC2626')), tickfont=dict(color='#DC2626'), overlaying='y', side='right'),
                height=420,
                hovermode="x unified"
            )
            st.plotly_chart(fig_dual, use_container_width=True)

    with m_tab4:
        st.subheader("4. Estratégia Metodológica e Download da Base de Dados Integrada")
        st.markdown("""
        ### Abordagem Econométrica Adotada
        1. **Harmonização em Macro-Tipologias:** Para superar a heterogeneidade nominal entre os 25 estados, todas as licenças foram padronizadas em 6 macro-categorias:
           - *Rural & Supressão (ASV/CAR/LAR)*
           - *Implantação de Obras (LP/LI)*
           - *Operação Contínua (LO/Regularização)*
           - *Procedimentos Simplificados (LAU/LAC)*
           - *Manejo Sustentável (PMFS)*
           - *Total Consolidado*
        2. **Estrutura de Defasagem Temporal (Distributed Lags):** Análise do efeito contemporâneo ($t=0$) e de inércia/precedência de 1 ano ($t=1$), refletindo o tempo entre a licença e a supressão de campo.
        3. **Níveis de Agregação:** Testes conduzidos no âmbito Nacional (Brasil), Regional (Norte, Nordeste, Centro-Oeste, Sudeste, Sul) e Estadual individual.
        """)

        st.markdown("### Download do Painel Integrado (UF x Ano x Tipologia x Desmatamento)")
        c_pan_csv, c_pan_json = st.columns(2)
        with c_pan_csv:
            csv_pan = df_panel.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Baixar Painel Integrado (CSV)", data=csv_pan, file_name="painel_desmatamento_licenciamento.csv", mime="text/csv")
        with c_pan_json:
            json_pan = df_panel.to_json(orient='records', force_ascii=False, indent=2).encode('utf-8')
            st.download_button("📥 Baixar Painel Integrado (JSON)", data=json_pan, file_name="painel_desmatamento_licenciamento.json", mime="application/json")

        st.dataframe(df_panel, use_container_width=True)

# ==============================================================================
# MÓDULO 4: BENCHMARK FINANCEIRO & BNDES
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

    # Map column names flexibly
    col_cnpj = 'cnpj' if 'cnpj' in df_bench.columns else 'doc_num'
    col_val = 'valor_contratado_bndes' if 'valor_contratado_bndes' in df_bench.columns else ('bndes_total_contratado' if 'bndes_total_contratado' in df_bench.columns else df_bench.columns[0])
    col_porte = 'porte_cliente_bndes' if 'porte_cliente_bndes' in df_bench.columns else ('porte_imac' if 'porte_imac' in df_bench.columns else 'porte')
    col_subsetor = 'subsetor_bndes' if 'subsetor_bndes' in df_bench.columns else 'bndes_subsetor'
    col_cliente = 'cliente_bndes' if 'cliente_bndes' in df_bench.columns else 'bndes_cliente'
    col_emp = 'nome_empreendimento' if 'nome_empreendimento' in df_bench.columns else df_bench.columns[0]
    col_tipo = 'tipo_licenca' if 'tipo_licenca' in df_bench.columns else df_bench.columns[0]
    col_ano = 'ano_protocolo' if 'ano_protocolo' in df_bench.columns else ('ano' if 'ano' in df_bench.columns else df_bench.columns[0])

    # Benchmark KPIs
    b1, b2, b3, b4 = st.columns(4)
    df_unique = df_bench.drop_duplicates(subset=[col_cnpj])
    tot_val = df_unique[col_val].sum()
    med_val = df_unique[col_val].median()
    
    b1.metric("Licenças Cruzadas com BNDES", f"{len(df_bench):,}")
    b2.metric("Empresas Únicas Financiadas", f"{df_bench[col_cnpj].nunique():,}")
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
        
        bench_grp = df_bench.groupby(col_tipo).agg(
            licencas=(col_cnpj, 'count'),
            empresas=(col_cnpj, 'nunique'),
            mediana=(col_val, 'median'),
            media=(col_val, 'mean'),
            total=(col_val, 'sum')
        ).reset_index().sort_values(by='mediana', ascending=False)
        
        fig_b_bar = px.bar(
            bench_grp,
            x=col_tipo,
            y='mediana',
            color=col_tipo,
            text='mediana',
            labels={col_tipo: 'Tipo de Licença', 'mediana': 'Mediana Financiada (R$)'},
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
        st.dataframe(t_display[[col_tipo, 'licencas', 'empresas', 'Mediana (R$)', 'Média (R$)', 'Total (R$)']], use_container_width=True)

    with b_tab2:
        st.subheader("2. Distribuição por Porte do Empreendimento e Setor Econômico")
        c1, c2 = st.columns(2)
        with c1:
            fig_bx = px.box(
                df_bench,
                x=col_porte,
                y=col_val,
                color=col_porte,
                log_y=True,
                labels={col_porte: 'Porte Declarado', col_val: 'Valor Financiado (R$ escala log)'},
                title="Dispersão do Investimento por Porte Declarado"
            )
            st.plotly_chart(fig_bx, use_container_width=True)
        with c2:
            top_subs = df_bench[col_subsetor].value_counts().head(8).reset_index()
            top_subs.columns = ['subsetor', 'contagem']
            fig_p = px.pie(top_subs, names='subsetor', values='contagem', title="Principais Subsetores Financiados com Licença")
            st.plotly_chart(fig_p, use_container_width=True)

    with b_tab3:
        st.subheader("3. Consulta Direta por Empresa ou CNPJ")
        q = st.text_input("Filtrar por Razão Social, Nome do Empreendimento ou CNPJ:", "")
        df_view = df_bench.copy()
        if q:
            df_view = df_view[
                df_view[col_emp].astype(str).str.contains(q, case=False, na=False) |
                df_view[col_cliente].astype(str).str.contains(q, case=False, na=False) |
                df_view[col_cnpj].astype(str).str.contains(q, case=False, na=False)
            ]
        st.write(f"Mostrando **{len(df_view):,}** registros encontrados.")
        show_cols = [c for c in [col_cnpj, col_cliente, col_emp, col_tipo, col_porte, col_ano, col_val, col_subsetor] if c in df_view.columns]
        st.dataframe(
            df_view[show_cols].rename(columns={
                col_cnpj: 'CNPJ',
                col_cliente: 'Cliente (BNDES)',
                col_emp: 'Nome Empreendimento',
                col_tipo: 'Tipo de Licença',
                col_porte: 'Porte',
                col_ano: 'Ano',
                col_val: 'Total Financiado (R$)',
                col_subsetor: 'Subsetor'
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
elif modulo == "🌾 Financiamento & Seguro Agropecuário":
    render_agro_module()

elif modulo == "🗺️ Mapa Geoespacial: Desmatamento & Licenças":
    render_map_module(DATA_DIR)
