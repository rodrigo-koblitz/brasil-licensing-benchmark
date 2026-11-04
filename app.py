import os
import json
import base64
import glob
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Plataforma Nacional de Licenciamento Ambiental - Brasil",
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
# SIDEBAR NAVIGATION (Two Main Modules)
# ==========================================
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)
st.sidebar.title("Navegação Principal")
modulo = st.sidebar.radio(
    "Selecione o Módulo:",
    options=[
        "🌱 Licenciamento Ambiental Brasil",
        "📊 Benchmark Financeiro & BNDES"
    ],
    index=0
)

# State mapping helper
state_names = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "IBAMA": "Âmbito Federal (IBAMA)",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo"
}

# ==============================================================================
# MÓDULO 1: LICENCIAMENTO AMBIENTAL BRASIL
# ==============================================================================
if modulo == "🌱 Licenciamento Ambiental Brasil":
    st.markdown('<div class="main-header">🌱 Panorama e Processamento de Licenciamento Ambiental no Brasil</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Acompanhamento consolidado do esforço de licenciamento ambiental, evolução temporal e acervo documental oficial de 25 estados brasileiros e do IBAMA.</div>', unsafe_allow_html=True)

    # Load national dataset
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

    # Tabs inside Licenciamento Brasil
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
            
            # Embedded PDF Viewer
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
# MÓDULO 2: BENCHMARK FINANCEIRO & BNDES
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

    b_tab1, b_tab2, b_tab3 = st.tabs([
        "📊 Mediana e Média por Tipo de Licença",
        "🏢 Distribuição por Porte e Subsetor",
        "🔎 Explorador de Empresas & CNPJ"
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
