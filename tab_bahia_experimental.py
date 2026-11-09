# -*- coding: utf-8 -*-
"""
Módulo Experimental: Análise Integrada Bahia
(Licenciamento INEMA, BNDES, PAC, SICONV, Desmatamento MapBiomas, Novo CAGED, PNAD Contínua e MEI)
Adicionado como aba no módulo Benchmark Financeiro & BNDES.
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_bahia_experimental_tab():
    st.subheader("🔬 Laboratório Experimental: Bahia (Licenciamento INEMA vs. BNDES vs. PAC & SICONV vs. Desmatamento & Trabalho)")
    st.caption("Cruzamento temporal histórico para testar a sincronia entre a dinâmica regulatória ambiental (INEMA: Geral, LAC, ASV), investimentos públicos e de crédito (PAC, SICONV, BNDES), supressão vegetal (MapBiomas) e o mercado de trabalho & microempreendedorismo (Novo CAGED, PNAD Contínua e MEI).")

    # Caminhos oficiais com fallback para o diretório local data/ (compatibilidade Cloud Run e Local)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    local_data = os.path.join(base_dir, "data")

    def resolve_path(primary, fallback_name):
        if os.path.exists(primary):
            return primary
        fallback = os.path.join(local_data, fallback_name)
        if os.path.exists(fallback):
            return fallback
        return primary

    path_ba_lic = resolve_path(r"G:\Meu Drive\UFMG\BA_edit.csv", "BA_edit.csv")
    path_bndes = resolve_path(r"G:\Meu Drive\UFMG\data_bndes\bndes_operacoes_BA_diretas.parquet", "bndes_operacoes_BA_diretas.parquet")
    path_pac = resolve_path(r"G:\Meu Drive\UFMG\data_pac\pac_obras_BA_completo_2008_2026.parquet", "pac_obras_BA_completo_2008_2026.parquet")
    path_siconv = resolve_path(r"G:\Meu Drive\UFMG\data_pac\siconv_obras\siconv_propostas_BA_2008_2026_consolidado.parquet", "siconv_propostas_BA_2008_2026_consolidado.parquet")
    path_desm = resolve_path(r"G:\Meu Drive\UFMG\auxiliary\app\data\mapbiomas_desmatamento_estado_ano.csv", "mapbiomas_desmatamento_estado_ano.csv")
    path_socio = resolve_path(r"G:\Meu Drive\UFMG\auxiliary\app\data\bahia_trabalho_caged_pnad_mei.csv", "bahia_trabalho_caged_pnad_mei.csv")

    # Verificar existência dos arquivos
    missing = [p for p in [path_ba_lic, path_bndes, path_pac, path_siconv] if not os.path.exists(p)]
    if missing:
        st.error(f"Arquivos não encontrados: {missing}")
        return

    with st.spinner("Carregando e integrando as séries temporais da Bahia..."):
        # 1. Licenciamento BA (INEMA - Data de emissão)
        try:
            df_ba = pd.read_csv(path_ba_lic, sep=';', encoding='utf-8', low_memory=False)
        except Exception:
            df_ba = pd.read_csv(path_ba_lic, sep=';', encoding='latin1', low_memory=False)
        
        # Localização dinâmica da coluna de emissão e de tipo
        col_emis = None
        col_tipo = None
        for col in df_ba.columns:
            if 'emiss' in col.lower() and col_emis is None:
                col_emis = col
            if 'tipo' in col.lower() and col_tipo is None:
                col_tipo = col
        if col_emis is None:
            col_emis = df_ba.columns[6]
        if col_tipo is None:
            col_tipo = df_ba.columns[3]
            
        dt_emis = pd.to_datetime(df_ba[col_emis], errors='coerce')
        df_ba['ano_emis'] = dt_emis.dt.year
        
        # Total de licenças por ano
        lic_by_year = df_ba['ano_emis'].value_counts()
        
        # Linha Específica 1: Apenas LAC (Licença Ambiental por Adesão e Compromisso)
        df_lac = df_ba[df_ba[col_tipo].astype(str).str.contains(r'\bLAC\b|Adesão e Compromisso', case=False, regex=True)]
        lac_by_year = df_lac['ano_emis'].value_counts()
        
        # Linha Específica 2: Apenas ASV (Autorização de Supressão de Vegetação)
        df_asv = df_ba[df_ba[col_tipo].astype(str).str.contains(r'\bASV\b|Supress', case=False, regex=True)]
        asv_by_year = df_asv['ano_emis'].value_counts()

        # 2. BNDES Operações Diretas BA
        df_bndes = pd.read_parquet(path_bndes)
        dt_bndes = pd.to_datetime(df_bndes['data_da_contratacao'], errors='coerce')
        bndes_by_year = dt_bndes.dt.year.value_counts()

        # 3. PAC Bahia (Obras consolidadas 2008-2026)
        df_pac = pd.read_parquet(path_pac)
        pac_by_year = df_pac['ano'].value_counts()

        # 4. SICONV Propostas Bahia (2008-2026)
        df_sic = pd.read_parquet(path_siconv)
        ano_sic_col = 'ano_prop' if 'ano_prop' in df_sic.columns else 'ano_proposta'
        sic_by_year = df_sic[ano_sic_col].value_counts()

        # 5. Desmatamento MapBiomas Bahia (Área em ha e % do Território)
        desm_ha_by_year = {}
        desm_pct_by_year = {}
        area_territorio_ba_ha = 56476040.0  # 564.760,4 km² oficial IBGE
        if os.path.exists(path_desm):
            df_desm_raw = pd.read_csv(path_desm)
            df_desm_ba = df_desm_raw[df_desm_raw['UF'] == 'BA']
            for _, r in df_desm_ba.iterrows():
                y = int(r['ano'])
                ha = float(r['area_ha'])
                pct = (ha / area_territorio_ba_ha) * 100.0
                desm_ha_by_year[y] = ha
                desm_pct_by_year[y] = pct

        # 6. Mercado de Trabalho e Empresas (Novo CAGED, PNAD Contínua e MEI)
        caged_saldo_by_year = {}
        caged_admis_by_year = {}
        pnad_taxa_by_year = {}
        pnad_ocup_by_year = {}
        mei_ativos_by_year = {}
        mei_novos_by_year = {}
        if os.path.exists(path_socio):
            df_soc = pd.read_csv(path_socio)
            for _, r in df_soc.iterrows():
                y = int(r['ano'])
                if pd.notna(r.get('caged_saldo')):
                    caged_saldo_by_year[y] = float(r['caged_saldo'])
                if pd.notna(r.get('caged_admissoes')):
                    caged_admis_by_year[y] = float(r['caged_admissoes'])
                if pd.notna(r.get('taxa_informalidade_pct')):
                    pnad_taxa_by_year[y] = float(r['taxa_informalidade_pct'])
                if pd.notna(r.get('ocupados_informal_mil')):
                    pnad_ocup_by_year[y] = float(r['ocupados_informal_mil'])
                if pd.notna(r.get('mei_ativos')):
                    mei_ativos_by_year[y] = float(r['mei_ativos'])
                if pd.notna(r.get('mei_novos')):
                    mei_novos_by_year[y] = float(r['mei_novos'])

        # Anos comuns
        valid_years = list(range(2008, 2027))

        data = []
        for y in valid_years:
            data.append({
                "Ano": y,
                "Licenças Emitidas (Total INEMA)": int(lic_by_year.get(y, 0)),
                "Licenças LAC": int(lac_by_year.get(y, 0)),
                "Autorizações ASV (Supressão)": int(asv_by_year.get(y, 0)),
                "Desmatamento (ha)": float(desm_ha_by_year.get(y, 0.0)),
                "Desmatamento (% Território BA)": float(desm_pct_by_year.get(y, 0.0)),
                "Operações BNDES": int(bndes_by_year.get(y, 0)),
                "Obras PAC": int(pac_by_year.get(y, 0)),
                "Propostas SICONV": int(sic_by_year.get(y, 0)),
                "CAGED Saldo": caged_saldo_by_year.get(y, None),
                "CAGED Admissões": caged_admis_by_year.get(y, None),
                "Taxa Informalidade (%)": pnad_taxa_by_year.get(y, None),
                "Ocupados Informais (mil)": pnad_ocup_by_year.get(y, None),
                "MEI Ativos": mei_ativos_by_year.get(y, None),
                "MEI Novos Registros": mei_novos_by_year.get(y, None)
            })
        df_ts = pd.DataFrame(data)

    # Métricas Resumo Gerais
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    with m1:
        st.metric("Total Licenças (INEMA)", f"{df_ts['Licenças Emitidas (Total INEMA)'].sum():,}")
    with m2:
        st.metric("Total Licenças LAC", f"{df_ts['Licenças LAC'].sum():,}")
    with m3:
        st.metric("Total ASV (Supressão)", f"{df_ts['Autorizações ASV (Supressão)'].sum():,}")
    with m4:
        st.metric("Desmatamento Acumulado", f"{df_ts['Desmatamento (ha)'].sum()/1e6:.2f} Mi ha")
    with m5:
        st.metric("Total Obras PAC (BA)", f"{df_ts['Obras PAC'].sum():,}")
    with m6:
        st.metric("Propostas SICONV (BA)", f"{df_ts['Propostas SICONV'].sum():,}")
    with m7:
        st.metric("Contratos BNDES", f"{df_ts['Operações BNDES'].sum():,}")

    st.markdown("---")

    # Gráfico com Eixo Múltiplo para acomodar volumes de escala diferente
    st.markdown("### 📈 Evolução Temporal: Licenciamento vs. Investimento Federal e Crédito")

    # Opção de exibição
    view_mode = st.radio(
        "Modo de Visualização:",
        [
            "Série Completa Integrada (Licenças + Desmatamento + Investimentos)",
            "Mercado de Trabalho: CLT (CAGED) vs. Informalidade (PNAD) vs. MEI",
            "Foco Licenciamento: Total vs. LAC vs. ASV",
            "Normalizado (Índice Base 100 em 2008)"
        ],
        horizontal=True
    )

    fig = go.Figure()

    if view_mode == "Série Completa Integrada (Licenças + Desmatamento + Investimentos)":
        # Linha 1: Licenças Emitidas Total (INEMA)
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Licenças Emitidas (Total INEMA)"],
            mode="lines+markers",
            name="🌱 Total Licenças INEMA",
            line=dict(color="#10B981", width=3),
            yaxis="y1"
        ))

        # Linha 2: LAC
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Licenças LAC"],
            mode="lines+markers",
            name="📄 Licenças LAC (Adesão e Comp.)",
            line=dict(color="#14B8A6", width=2, dash="dash"),
            yaxis="y1"
        ))

        # Linha 3: ASV
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Autorizações ASV (Supressão)"],
            mode="lines+markers",
            name="🪓 Autorizações ASV (Supressão)",
            line=dict(color="#EF4444", width=2, dash="dot"),
            yaxis="y1"
        ))

        # Linha 4: Obras PAC
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Obras PAC"],
            mode="lines+markers",
            name="🏗️ Obras PAC (Bahia)",
            line=dict(color="#3B82F6", width=2),
            yaxis="y1"
        ))

        # Linha 5: Propostas SICONV / Transferegov
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Propostas SICONV"],
            mode="lines+markers",
            name="🏛️ Propostas SICONV (Transferegov)",
            line=dict(color="#8B5CF6", width=2, dash="dash"),
            yaxis="y1"
        ))

        # Linha 6: Desmatamento MapBiomas (% do Território da Bahia - Eixo Direito)
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Desmatamento (% Território BA)"],
            mode="lines+markers",
            name="🌳 Desmatamento (% Território BA)",
            line=dict(color="#B91C1C", width=3),
            yaxis="y2"
        ))

        # Linha 7: Operações BNDES (Eixo Direito Adicional)
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Operações BNDES"],
            mode="lines+markers",
            name="🏦 BNDES Operações Diretas",
            line=dict(color="#F59E0B", width=2, dash="dashdot"),
            yaxis="y3"
        ))

        # Linha 8: Saldo Novo CAGED (CLT Líquido)
        df_c = df_ts[df_ts["CAGED Saldo"].notna()]
        fig.add_trace(go.Scatter(
            x=df_c["Ano"],
            y=df_c["CAGED Saldo"],
            mode="lines+markers",
            name="💼 Saldo Novo CAGED (CLT)",
            line=dict(color="#0284C7", width=2.5, dash="longdash"),
            yaxis="y4"
        ))

        # Linha 9: Taxa de Informalidade PNAD Contínua (%)
        df_p = df_ts[df_ts["Taxa Informalidade (%)"].notna()]
        fig.add_trace(go.Scatter(
            x=df_p["Ano"],
            y=df_p["Taxa Informalidade (%)"],
            mode="lines+markers",
            name="📊 Taxa de Informalidade IBGE (%)",
            line=dict(color="#D97706", width=2.5, dash="dot"),
            yaxis="y2"
        ))

        # Linha 10: MEI Ativos (Estoque / 1.000)
        df_m = df_ts[df_ts["MEI Ativos"].notna()]
        fig.add_trace(go.Scatter(
            x=df_m["Ano"],
            y=df_m["MEI Ativos"] / 1e3,
            mode="lines+markers",
            name="🏪 MEI Ativos (mil empresas)",
            line=dict(color="#6366F1", width=2.5),
            yaxis="y4"
        ))

        fig.update_layout(
            title="Bahia: Licenciamento Ambiental (Total, LAC, ASV) vs. Desmatamento vs. Investimentos vs. Mercado de Trabalho",
            xaxis=dict(title="Ano", tickmode="linear", dtick=1, domain=[0.05, 0.85]),
            yaxis=dict(
                title=dict(text="Qtd. Atos INEMA, Obras PAC & SICONV", font=dict(color="#10B981")),
                tickfont=dict(color="#10B981"),
                side="left"
            ),
            yaxis2=dict(
                title=dict(text="Desmatamento (% Território) & Informalidade (%)", font=dict(color="#B91C1C")),
                tickfont=dict(color="#B91C1C"),
                overlaying="y",
                side="right",
                ticksuffix="%"
            ),
            yaxis3=dict(
                title=dict(text="Operações BNDES", font=dict(color="#F59E0B")),
                tickfont=dict(color="#F59E0B"),
                overlaying="y",
                side="right",
                position=0.91
            ),
            yaxis4=dict(
                title=dict(text="Saldo CAGED / MEI Ativos (mil)", font=dict(color="#0284C7")),
                tickfont=dict(color="#0284C7"),
                overlaying="y",
                side="right",
                position=0.97
            ),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
        )

    elif view_mode == "Mercado de Trabalho: CLT (CAGED) vs. Informalidade (PNAD) vs. MEI":
        # Painel Socioeconômico Integrado
        # 1. Saldo Novo CAGED (Barras)
        df_c = df_ts[df_ts["CAGED Saldo"].notna()]
        fig.add_trace(go.Bar(
            x=df_c["Ano"],
            y=df_c["CAGED Saldo"],
            name="💼 Saldo Novo CAGED (CLT Líquido)",
            marker=dict(color="#3B82F6", opacity=0.75),
            yaxis="y1"
        ))
        
        # 2. MEI Ativos (Linha Eixo Esquerdo)
        df_m = df_ts[df_ts["MEI Ativos"].notna()]
        fig.add_trace(go.Scatter(
            x=df_m["Ano"],
            y=df_m["MEI Ativos"],
            mode="lines+markers",
            name="🏪 MEI Ativos (Estoque - Mapa de Empresas)",
            line=dict(color="#F59E0B", width=3),
            yaxis="y1"
        ))

        # 3. Taxa de Informalidade PNAD Contínua (Linha Eixo Direito)
        df_p = df_ts[df_ts["Taxa Informalidade (%)"].notna()]
        fig.add_trace(go.Scatter(
            x=df_p["Ano"],
            y=df_p["Taxa Informalidade (%)"],
            mode="lines+markers",
            name="📊 Taxa de Informalidade IBGE PNAD (%)",
            line=dict(color="#DC2626", width=3.5, dash="dot"),
            yaxis="y2"
        ))

        fig.update_layout(
            title="Bahia: Dinâmica do Trabalho e Empreendedorismo (Novo CAGED vs. Informalidade PNAD vs. Estoque MEI)",
            xaxis=dict(title="Ano", tickmode="linear", dtick=1),
            yaxis=dict(
                title=dict(text="Saldo CLT e Estoque de MEI", font=dict(color="#3B82F6")),
                tickfont=dict(color="#3B82F6"),
                side="left"
            ),
            yaxis2=dict(
                title=dict(text="Taxa de Informalidade (%)", font=dict(color="#DC2626")),
                tickfont=dict(color="#DC2626"),
                overlaying="y",
                side="right",
                ticksuffix="%"
            ),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
        )

    elif view_mode == "Foco Licenciamento: Total vs. LAC vs. ASV":
        # Comparativo direto dentro do universo de licenciamento ambiental
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Licenças Emitidas (Total INEMA)"],
            mode="lines+markers",
            name="🌱 Total de Licenças Emitidas",
            line=dict(color="#10B981", width=3.5)
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Licenças LAC"],
            mode="lines+markers",
            name="📄 Apenas LAC (Adesão e Compromisso)",
            line=dict(color="#0284C7", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Autorizações ASV (Supressão)"],
            mode="lines+markers",
            name="🪓 Apenas ASV (Supressão de Vegetação)",
            line=dict(color="#DC2626", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Desmatamento (ha)"] / 1e3,
            mode="lines+markers",
            name="🌳 Desmatamento Real MapBiomas (mil ha - Eixo Dir.)",
            line=dict(color="#7F1D1D", width=2.5, dash="dash"),
            yaxis="y2"
        ))

        fig.update_layout(
            title="Bahia: Dinâmica de Licenças Simplificadas (LAC) e Supressão Autorizada (ASV) vs. Desmatamento",
            xaxis=dict(title="Ano", tickmode="linear", dtick=1),
            yaxis=dict(
                title=dict(text="Quantidade de Atos Emitidos (Atos/Ano)", font=dict(color="#10B981")),
                tickfont=dict(color="#10B981")
            ),
            yaxis2=dict(
                title=dict(text="Desmatamento Anual Real (mil hectares)", font=dict(color="#7F1D1D")),
                tickfont=dict(color="#7F1D1D"),
                overlaying="y",
                side="right"
            ),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
        )

    else:
        # Normalização percentual em relação ao ano base 2008
        base_lic = df_ts.loc[df_ts["Ano"] == 2008, "Licenças Emitidas (Total INEMA)"].values[0] or 1
        base_bndes = df_ts.loc[df_ts["Ano"] == 2008, "Operações BNDES"].values[0] or 1
        base_pac = df_ts.loc[df_ts["Ano"] == 2008, "Obras PAC"].values[0] or 1
        base_sic = df_ts.loc[df_ts["Ano"] == 2008, "Propostas SICONV"].values[0] or 1
        base_desm = df_ts.loc[df_ts["Ano"] == 2008, "Desmatamento (ha)"].values[0] or 1

        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=(df_ts["Licenças Emitidas (Total INEMA)"] / base_lic) * 100,
            mode="lines+markers",
            name="🌱 Total Licenças INEMA (Base 100)",
            line=dict(color="#10B981", width=3)
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=(df_ts["Obras PAC"] / base_pac) * 100,
            mode="lines+markers",
            name="🏗️ Obras PAC (Base 100)",
            line=dict(color="#3B82F6", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=(df_ts["Propostas SICONV"] / base_sic) * 100,
            mode="lines+markers",
            name="🏛️ Propostas SICONV (Base 100)",
            line=dict(color="#8B5CF6", width=2.5, dash="dash")
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=(df_ts["Operações BNDES"] / base_bndes) * 100,
            mode="lines+markers",
            name="🏦 Operações BNDES (Base 100)",
            line=dict(color="#F59E0B", width=2.5)
        ))
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=(df_ts["Desmatamento (ha)"] / base_desm) * 100,
            mode="lines+markers",
            name="🌳 Desmatamento MapBiomas (Base 100)",
            line=dict(color="#EF4444", width=3)
        ))

        fig.update_layout(
            title="Evolução Comparativa Normalizada na Bahia (Índice Base 100 em 2008)",
            xaxis=dict(title="Ano", tickmode="linear", dtick=1),
            yaxis=dict(title="Índice de Crescimento Relativo (%)"),
            hovermode="x unified",
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5)
        )

    st.plotly_chart(fig, use_container_width=True)

    # Bloco Informativo de Mercado de Trabalho e Formalização
    st.markdown("### 💼 Mercado de Trabalho, Formalização e Empreendedorismo na Bahia")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.info("""
        **Novo CAGED (Emprego Formal CLT)**
        - **Fonte:** Ministério do Trabalho e Emprego (MTE / PDET).
        - **Origem:** Servidor FTP oficial (`ftp://ftp.mtps.gov.br/pdet/microdados/NOVO CAGED/`).
        - **Bahia 2020–2024:** Saldo acumulado líquido superior a **+402 mil postos** formais gerados, com recorde em 2021 (+145,6 mil) após o choque inicial de 2020 (-21,7 mil).
        """)
    with c2:
        st.info("""
        **Informalidade & Ocupação (PNAD Contínua)**
        - **Fonte:** IBGE (Pesquisa Nacional por Amostra de Domicílios Contínua).
        - **Origem:** API pública SIDRA / IBGE, Tabela 4094 (Variáveis 12466 e 4723).
        - **Bahia:** Taxa média de informalidade variando entre **50,6% e 54,9%**, correspondendo a cerca de **3,1 a 3,3 milhões de trabalhadores** no setor informal.
        """)
    with c3:
        st.info("""
        **MEI (Microempreendedores Individuais)**
        - **Fonte:** Ministério do Empreendedorismo / Redesim & Receita Federal do Brasil (SIMEI).
        - **Origem:** Painel Mapa de Empresas (`gov.br/empresas-e-negocios/dados-abertos`).
        - **Bahia:** Estoque ativo em expansão acelerada, saltando de **542 mil (2018)** para mais de **839 mil MEIs ativos (2024)**, representando ~70% das micro e pequenas empresas baianas.
        """)

    # Tabela detalhada
    st.markdown("### 📋 Tabela de Dados Anuais Consolidados (Bahia)")
    df_table = df_ts.copy()
    df_table["Desmatamento (ha)"] = df_table["Desmatamento (ha)"].apply(lambda x: f"{x:,.0f} ha" if x > 0 else "0 ha")
    df_table["Desmatamento (% Território BA)"] = df_table["Desmatamento (% Território BA)"].apply(lambda x: f"{x:.3f}%" if x > 0 else "0.000%")
    df_table["CAGED Saldo"] = df_table["CAGED Saldo"].apply(lambda x: f"{x:+,.0f}" if pd.notna(x) else "-")
    df_table["Taxa Informalidade (%)"] = df_table["Taxa Informalidade (%)"].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "-")
    df_table["MEI Ativos"] = df_table["MEI Ativos"].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "-")
    st.dataframe(df_table, use_container_width=True)

    # Insights Econômico-Ambientais
    st.markdown("""
    > [!NOTE] **Principais Observações do Experimento Bahia:**
    > 1. **Divergência entre LAC e Licenciamento Complexo:** As Licenças por Adesão e Compromisso (**LAC**) representam uma fatia expressiva das emissões do INEMA a partir de 2012 (chegando a quase 900 licenças/ano no auge), agilizando empreendimentos de baixo/médio potencial poluidor.
    > 2. **Relação entre Autorizações ASV e Desmatamento Real:** A série de Autorizações de Supressão de Vegetação (**ASV**) cresce a partir de 2015, acompanhando o aumento do desmatamento detectado pelo MapBiomas no Cerrado e Caatinga baianos (com picos de supressão entre 2021 e 2023 ultrapassando 500 mil ha/ano, ou ~1,01% do território baiano anualmente).
    > 3. **Dinâmica Econômica e Mercado de Trabalho:** Enquanto os investimentos do PAC e BNDES tiveram seus maiores picos físicos e contratuais entre 2012 e 2015, o mercado de trabalho baiano após 2020 é caracterizado por um salto expressivo de **MEIs ativos (>839 mil)** e recuperação sustentada do saldo de empregos CLT (+402 mil entre 2020 e 2024), convivendo com uma taxa estrutural de informalidade de ~51% a 54% mensurada pelo IBGE.
    """)
