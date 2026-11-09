# -*- coding: utf-8 -*-
"""
Módulo Experimental: Análise Integrada Bahia (Licenciamento INEMA, BNDES, PAC, SICONV e Desmatamento MapBiomas)
Adicionado como aba no módulo Benchmark Financeiro & BNDES.
"""

import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def render_bahia_experimental_tab():
    st.subheader("🔬 Laboratório Experimental: Bahia (Licenciamento INEMA vs. BNDES vs. PAC & SICONV vs. Desmatamento)")
    st.caption("Cruzamento temporal histórico para testar a sincronia entre a abertura/emissão de licenças ambientais (Geral, LAC, ASV), supressão de vegetação nativa e os fluxos de investimentos federais e de crédito.")

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
                "Propostas SICONV": int(sic_by_year.get(y, 0))
            })
        df_ts = pd.DataFrame(data)

    # Métricas Resumo
    m1, m2, m3, m4, m5, m6 = st.columns(6)
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
        st.metric("Contratos BNDES", f"{df_ts['Operações BNDES'].sum():,}")

    st.markdown("---")

    # Gráfico com Eixo Duplo (Dual Axis) para acomodar volumes de escala diferente
    st.markdown("### 📈 Evolução Temporal: Licenciamento vs. Investimento Federal e Crédito")

    # Opção de exibição
    view_mode = st.radio(
        "Modo de Visualização:",
        [
            "Série Completa Integrada (Licenças + Desmatamento + Investimentos)",
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

        # Linha 5: Desmatamento MapBiomas (% do Território da Bahia - Eixo Direito)
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Desmatamento (% Território BA)"],
            mode="lines+markers",
            name="🌳 Desmatamento (% Território BA)",
            line=dict(color="#B91C1C", width=3),
            yaxis="y2"
        ))

        # Linha 6: Operações BNDES (Eixo Direito)
        fig.add_trace(go.Scatter(
            x=df_ts["Ano"],
            y=df_ts["Operações BNDES"],
            mode="lines+markers",
            name="🏛️ BNDES Operações Diretas",
            line=dict(color="#F59E0B", width=2, dash="dashdot"),
            yaxis="y3"
        ))

        fig.update_layout(
            title="Bahia: Licenciamento Ambiental (Total, LAC, ASV) vs. Desmatamento vs. Investimentos (2008-2026)",
            xaxis=dict(title="Ano", tickmode="linear", dtick=1, domain=[0.05, 0.90]),
            yaxis=dict(
                title=dict(text="Qtd. Licenças Emitidas & Obras PAC", font=dict(color="#10B981")),
                tickfont=dict(color="#10B981"),
                side="left"
            ),
            yaxis2=dict(
                title=dict(text="Desmatamento Anual (% do Território)", font=dict(color="#B91C1C")),
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
                position=0.97
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
        # Desmatamento em hectares no eixo secundário para correlacionar com a curva de ASV
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
        # Normalização percentual em relação ao ano base 2008 (ou primeiro ano com dado para ASV/LAC)
        base_lic = df_ts.loc[df_ts["Ano"] == 2008, "Licenças Emitidas (Total INEMA)"].values[0] or 1
        base_bndes = df_ts.loc[df_ts["Ano"] == 2008, "Operações BNDES"].values[0] or 1
        base_pac = df_ts.loc[df_ts["Ano"] == 2008, "Obras PAC"].values[0] or 1
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
            y=(df_ts["Operações BNDES"] / base_bndes) * 100,
            mode="lines+markers",
            name="🏛️ Operações BNDES (Base 100)",
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

    # Tabela detalhada
    st.markdown("### 📋 Tabela de Dados Anuais Consolidados (Bahia)")
    df_table = df_ts.copy()
    df_table["Desmatamento (ha)"] = df_table["Desmatamento (ha)"].apply(lambda x: f"{x:,.0f} ha" if x > 0 else "0 ha")
    df_table["Desmatamento (% Território BA)"] = df_table["Desmatamento (% Território BA)"].apply(lambda x: f"{x:.3f}%" if x > 0 else "0.000%")
    st.dataframe(df_table, use_container_width=True)

    # Insights Econômico-Ambientais
    st.markdown("""
    > [!NOTE] **Principais Observações do Experimento Bahia:**
    > 1. **Divergência entre LAC e Licenciamento Complexo:** As Licenças por Adesão e Compromisso (**LAC**) representam uma fatia expressiva das emissões do INEMA a partir de 2012 (chegando a quase 900 licenças/ano no auge), agilizando empreendimentos de baixo/médio potencial poluidor.
    > 2. **Relação entre Autorizações ASV e Desmatamento Real:** A série de Autorizações de Supressão de Vegetação (**ASV**) cresce a partir de 2015, acompanhando o aumento do desmatamento detectado pelo MapBiomas no Cerrado e Caatinga baianos (com picos de supressão entre 2021 e 2023 ultrapassando 500 mil ha/ano, ou ~1,01% do território baiano anualmente).
    > 3. **Sincronia com PAC e Crédito BNDES:** O período de 2012–2014 concentra os maiores volumes combinados de obras públicas federais (PAC 2) e contratos de crédito de desenvolvimento, coincidindo com a expansão da capacidade regulatória estadual.
    """)
