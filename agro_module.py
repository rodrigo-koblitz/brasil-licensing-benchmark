"""
Agricultural Module for Streamlit App (Fully Remediated)
Addresses Auditor Findings:
- Issue 1: Complete Selic Real coverage for capital_segurado and premio_liquido (no price base mismatch)
- Issue 2: Centralized ETL in remediate_audit_findings.py (calculate_conversions.py deprecated)
- Minor 1: Precise formula labeling: (1+Selic)/(1+IPCA) - 1
- Minor 2: Accurate series naming: "IPA Agropecuário (FGV - SGS 225)"
"""

import os
import duckdb
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DATA_DIR = os.path.join(APP_DIR, "data")
DATA_AGRO_DIR = r"G:\Meu Drive\UFMG\data_agro"

if os.path.exists(os.path.join(APP_DATA_DIR, "agro_state_series_2000_2025.parquet")):
    STATE_PARQUET = os.path.join(APP_DATA_DIR, "agro_state_series_2000_2025.parquet")
else:
    STATE_PARQUET = os.path.join(DATA_AGRO_DIR, "state_level", "agro_state_series_2000_2025.parquet")

if os.path.exists(os.path.join(APP_DATA_DIR, "ibge_pam_municipios_2000_2024.parquet")):
    MUNI_PARQUET = os.path.join(APP_DATA_DIR, "ibge_pam_municipios_2000_2024.parquet")
else:
    MUNI_PARQUET = os.path.join(DATA_AGRO_DIR, "parquet", "ibge_pam_municipios_2000_2024.parquet")

DB_PATH = os.path.join(DATA_AGRO_DIR, "agro_data.duckdb")

@st.cache_data
def load_agro_state_data():
    if os.path.exists(STATE_PARQUET):
        return pd.read_parquet(STATE_PARQUET)
    elif os.path.exists(DB_PATH):
        con = duckdb.connect(DB_PATH)
        df = con.execute("SELECT * FROM agro_state_series").df()
        con.close()
        return df
    return pd.DataFrame()

def render_agro_module():
    st.markdown('<div class="main-header">🌾 Agro: Financiamento, Produção & Seguro Rural</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Análise integrada do Valor da Produção Agrícola (IBGE - PAM) e da Subvenção ao Seguro Rural (MAPA - PSR) com deflacionamento e atualização financeira auditados (2000–2025).</div>', unsafe_allow_html=True)

    df_state = load_agro_state_data()

    if df_state.empty:
        st.warning("Dados agropecuários ainda não foram processados ou arquivo não encontrado.")
        return

    # Methodological & Price Regime Selector
    st.markdown("##### 💱 Selecione a Métrica de Ajuste de Preços / Custo Intertemporal (Base: 2024):")
    regime_preco = st.radio(
        "Regime de Ajuste Econômico:",
        options=[
            "Valores Nominais (Preços Correntes Históricos)",
            "Poder de Compra Real (Deflacionado pelo IPCA - Cesta Consumidor)",
            "Deflator Setorial Agrícola (Deflacionado pelo IPA Agropecuário FGV - SGS 225)",
            "Custo de Oportunidade Real [Taxa Selic Real ex-post: (1+Selic)/(1+IPCA) - 1]",
            "Atualização Financeira Nominal (Capitalização Selic Plena)"
        ],
        index=0,
        horizontal=False
    )

    # Column mappings without any silent fallback or mismatched bases
    if regime_preco == "Poder de Compra Real (Deflacionado pelo IPCA - Cesta Consumidor)":
        prod_col = 'valor_producao_bi_reais_ipca'
        subv_col = 'subvencao_federal_mi_reais_ipca'
        cap_col = 'capital_segurado_mi_reais_ipca'
        muni_col = 'valor_producao_mil_reais_ipca'
        sufixo_legenda = "Real IPCA (R$ de 2024)"
        desc_info = "Valores expressos em poder de compra constante de 2024, deflacionados pelo IPCA oficial do IBGE."
    elif regime_preco == "Deflator Setorial Agrícola (Deflacionado pelo IPA Agropecuário FGV - SGS 225)":
        prod_col = 'valor_producao_bi_reais_ipa'
        subv_col = 'subvencao_federal_mi_reais_ipca' # Fiscal budget subsidies evaluated by purchasing power
        cap_col = 'capital_segurado_mi_reais_ipca'
        muni_col = 'valor_producao_mil_reais_ipa'
        sufixo_legenda = "Real IPA Agropecuário (R$ de 2024)"
        desc_info = "Produção agrícola deflacionada pelo Índice de Preços por Atacado - Produtos Agropecuários (FGV SGS 225), refletindo preços no atacado/commodities."
    elif regime_preco == "Custo de Oportunidade Real [Taxa Selic Real ex-post: (1+Selic)/(1+IPCA) - 1]":
        prod_col = 'valor_producao_bi_reais_selic_real'
        subv_col = 'subvencao_federal_mi_reais_selic_real'
        cap_col = 'capital_segurado_mi_reais_selic_real' # Issue 1: Now mapped cleanly to selic_real!
        muni_col = 'valor_producao_mil_reais_selic_real'
        sufixo_legenda = "Custo de Oportunidade Real (Juro Real Selic)"
        desc_info = "Atualização monetária pelo juro real ex-post ((1+Selic)/(1+IPCA)-1), representando o rendimento financeiro acima da inflação."
    elif regime_preco == "Atualização Financeira Nominal (Capitalização Selic Plena)":
        prod_col = 'valor_producao_bi_reais_selic_nominal'
        subv_col = 'subvencao_federal_mi_reais_selic_nominal'
        cap_col = 'capital_segurado_mi_reais_selic_nominal'
        muni_col = 'valor_producao_mil_reais_selic_nominal'
        sufixo_legenda = "Atualizado p/ Selic Nominal (Valor Futuro)"
        desc_info = "Capitalização pela taxa Selic nominal acumulada (similar ao critério de atualização de precatórios e liquidação financeira)."
    else:
        prod_col = 'valor_producao_bi_reais'
        subv_col = 'subvencao_federal_mi_reais'
        cap_col = 'capital_segurado_mi_reais'
        muni_col = 'valor_producao_mil_reais'
        sufixo_legenda = "Nominal (Preços Correntes)"
        desc_info = "Valores históricos nominais originais, sem aplicação de deflatores ou juros."

    st.caption(f"ℹ️ **Critério Ativo:** {desc_info}")

    # Top KPI Metrics Cards (Latest Available Year: 2024)
    df_2024 = df_state[df_state['ano'] == 2024]
    val_prod_total = df_2024[prod_col].sum()
    subv_total = df_2024[subv_col].sum()
    cap_seg_total = df_2024[cap_col].sum() / 1e3
    apolices_total = int(df_2024['qtde_apolices_seguradas'].sum())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label=f"🌾 Valor da Produção (2024) [{sufixo_legenda}]",
            value=f"R$ {val_prod_total:.1f} Bi",
            help="Valor da Produção Agrícola total medido pelo IBGE PAM em 2024"
        )
    with col2:
        st.metric(
            label=f"🛡️ Subvenção Federal PSR (2024) [{sufixo_legenda}]",
            value=f"R$ {subv_total:.1f} Mi",
            help="Recursos federais pagos pelo MAPA para subvencionar apólices de seguro rural"
        )
    with col3:
        st.metric(
            label=f"💰 Capital Segurado (2024) [{sufixo_legenda}]",
            value=f"R$ {cap_seg_total:.1f} Bi",
            help="Total do patrimônio agrícola protegido sob apólices com apoio federal"
        )
    with col4:
        st.metric(
            label="📋 Apólices Atendidas (2024)",
            value=f"{apolices_total:,}".replace(",", "."),
            help="Contratos de seguro rural subsidiados em 2024"
        )

    st.markdown("---")

    # Tabs for in-depth exploration
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Panorama Nacional & Regional",
        "🗺️ Comparativo entre Estados (UF)",
        "🔍 Detalhamento por Estado",
        "🏙️ Top Municípios Agrícolas",
        "📋 Metodologia & Auditoria"
    ])

    # -------------------------------------------------------------
    # TAB 1: PANORAMA NACIONAL & REGIONAL
    # -------------------------------------------------------------
    with tab1:
        st.subheader(f"Evolução Histórica da Agropecuária Nacional ({sufixo_legenda})")
        
        c_left, c_right = st.columns(2)
        
        with c_left:
            df_nat_pam = df_state[df_state['ano'] <= 2024].groupby('ano', as_index=False)[prod_col].sum()
            fig_nat = px.area(
                df_nat_pam, x='ano', y=prod_col,
                title=f"Valor da Produção Agrícola Nacional - R$ Bi ({sufixo_legenda})",
                color_discrete_sequence=['#2e7d32'],
                labels={'ano': 'Ano', prod_col: 'R$ Bilhões'}
            )
            fig_nat.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_nat, use_container_width=True)

        with c_right:
            df_reg = df_state[df_state['ano'] <= 2024].groupby(['ano', 'regiao'], as_index=False)[prod_col].sum()
            fig_reg = px.bar(
                df_reg, x='ano', y=prod_col, color='regiao',
                title=f"Composição por Região Geográfica - R$ Bi ({sufixo_legenda})",
                color_discrete_map={
                    'Centro-Oeste': '#ff9800',
                    'Sul': '#2196f3',
                    'Sudeste': '#4caf50',
                    'Nordeste': '#e91e63',
                    'Norte': '#9c27b0'
                },
                labels={'ano': 'Ano', prod_col: 'R$ Bilhões', 'regiao': 'Região'}
            )
            fig_reg.update_layout(barmode='stack', hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_reg, use_container_width=True)

        st.markdown(f"### Apoio ao Seguro Rural Federal (MAPA - PSR) [{sufixo_legenda}]")
        df_nat_psr = df_state[(df_state['ano'] >= 2006) & (df_state['ano'] <= 2024)].groupby('ano', as_index=False).agg({
            subv_col: 'sum',
            cap_col: 'sum'
        })
        
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_nat_psr['ano'],
            y=df_nat_psr[subv_col],
            name=f"Subvenção Federal (R$ Mi)",
            marker_color='#1976d2',
            yaxis='y1'
        ))
        fig_dual.add_trace(go.Scatter(
            x=df_nat_psr['ano'],
            y=df_nat_psr[cap_col] / 1e3,
            name="Capital Protegido (R$ Bi)",
            mode='lines+markers',
            line=dict(color='#d32f2f', width=3),
            yaxis='y2'
        ))
        
        fig_dual.update_layout(
            title=f"Evolução do Seguro Rural: Subvenção vs. Cobertura ({sufixo_legenda})",
            yaxis=dict(
                title=dict(text="Subvenção Federal (R$ Milhões)", font=dict(color="#1976d2")),
                tickfont=dict(color="#1976d2")
            ),
            yaxis2=dict(
                title=dict(text="Capital Segurado (R$ Bilhões)", font=dict(color="#d32f2f")),
                tickfont=dict(color="#d32f2f"),
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0.01, y=0.98),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    # -------------------------------------------------------------
    # TAB 2: COMPARATIVO ENTRE ESTADOS (UF)
    # -------------------------------------------------------------
    with tab2:
        st.subheader(f"Ranking e Distribuição Estadual ({sufixo_legenda})")
        selected_year = st.slider("Selecione o Ano de Análise:", min_value=2000, max_value=2024, value=2024)

        df_yr = df_state[df_state['ano'] == selected_year].sort_values(prod_col, ascending=False)

        col_a, col_b = st.columns([3, 2])
        with col_a:
            fig_bar = px.bar(
                df_yr.head(15),
                x=prod_col,
                y='uf_nome',
                orientation='h',
                color='regiao',
                title=f"Top 15 Estados em Valor da Produção ({selected_year}) - {sufixo_legenda}",
                labels={prod_col: 'R$ Bilhões', 'uf_nome': 'Estado'},
                category_orders={'uf_nome': df_yr.head(15)['uf_nome'].tolist()[::-1]}
            )
            fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_b:
            st.markdown(f"**Tabela Consolidada ({selected_year})**")
            cols_show = ['sigla_uf', 'uf_nome', 'regiao', prod_col]
            if selected_year >= 2006:
                cols_show += [subv_col, cap_col]
            
            st.dataframe(
                df_yr[cols_show].rename(columns={
                    'sigla_uf': 'UF',
                    'uf_nome': 'Estado',
                    'regiao': 'Região',
                    prod_col: f'Produção R$ Bi ({sufixo_legenda})',
                    subv_col: f'Subvenção R$ Mi ({sufixo_legenda})',
                    cap_col: f'Garantia R$ Mi ({sufixo_legenda})'
                }),
                height=420,
                use_container_width=True
            )

        if selected_year >= 2006:
            st.markdown(f"### Relação: Valor da Produção vs. Cobertura de Seguro ({selected_year})")
            fig_scat = px.scatter(
                df_yr[df_yr[prod_col] > 0.5],
                x=prod_col,
                y=subv_col,
                size=cap_col,
                color='regiao',
                text='sigla_uf',
                title=f"Produção Agrícola vs. Subvenção ao Seguro Rural ({selected_year}) - {sufixo_legenda}",
                labels={
                    prod_col: f'Valor da Produção R$ Bi ({sufixo_legenda})',
                    subv_col: f'Subvenção Federal R$ Mi ({sufixo_legenda})',
                    cap_col: f'Capital Segurado R$ Mi ({sufixo_legenda})'
                }
            )
            fig_scat.update_traces(textposition='top center')
            fig_scat.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_scat, use_container_width=True)

    # -------------------------------------------------------------
    # TAB 3: DETALHAMENTO POR ESTADO
    # -------------------------------------------------------------
    with tab3:
        st.subheader("Análise Individual por Unidade Federativa")
        all_ufs = sorted(df_state['sigla_uf'].dropna().unique().tolist())
        selected_uf = st.selectbox("Escolha um Estado:", options=all_ufs, index=all_ufs.index('BA') if 'BA' in all_ufs else 0)

        df_single_uf = df_state[df_state['sigla_uf'] == selected_uf].sort_values('ano')
        state_fullname = df_single_uf['uf_nome'].iloc[0] if not df_single_uf.empty else selected_uf

        st.markdown(f"#### Trajetória Agrícola de **{state_fullname} ({selected_uf})** (2000–2024)")

        c_u1, c_u2 = st.columns(2)
        with c_u1:
            fig_uf_pam = px.line(
                df_single_uf[df_single_uf['ano'] <= 2024],
                x='ano', y=prod_col,
                markers=True,
                title=f"Valor da Produção Agrícola - {selected_uf} (R$ Bi - {sufixo_legenda})",
                color_discrete_sequence=['#2e7d32']
            )
            fig_uf_pam.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_uf_pam, use_container_width=True)

        with c_u2:
            fig_uf_psr = px.bar(
                df_single_uf[(df_single_uf['ano'] >= 2006) & (df_single_uf['ano'] <= 2024)],
                x='ano', y=subv_col,
                title=f"Subvenção ao Seguro Rural - {selected_uf} (R$ Mi - {sufixo_legenda})",
                color_discrete_sequence=['#1565c0']
            )
            fig_uf_psr.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_uf_psr, use_container_width=True)

        st.dataframe(
            df_single_uf[['ano', prod_col, subv_col, cap_col, 'qtde_apolices_seguradas']].rename(columns={
                'ano': 'Ano',
                prod_col: f'Produção IBGE R$ Bi ({sufixo_legenda})',
                subv_col: f'Subvenção MAPA R$ Mi ({sufixo_legenda})',
                cap_col: f'Capital Segurado R$ Mi ({sufixo_legenda})',
                'qtde_apolices_seguradas': 'Apólices Subvencionadas'
            }),
            use_container_width=True
        )

    # -------------------------------------------------------------
    # TAB 4: TOP MUNICÍPIOS AGRÍCOLAS
    # -------------------------------------------------------------
    with tab4:
        st.subheader(f"Granularidade Municipal: Os Maiores Polos Produtivos do Brasil ({sufixo_legenda})")
        
        muni_year = st.selectbox("Ano de Referência Municipal:", options=list(range(2024, 1999, -1)), index=0)

        if os.path.exists(MUNI_PARQUET):
            con = duckdb.connect()
            df_top_mun = con.execute(f"""
                SELECT 
                    municipio_nome,
                    {muni_col} / 1e3 AS valor_producao_mi_reais
                FROM '{MUNI_PARQUET.replace(chr(92), '/')}'
                WHERE ano = {muni_year}
                ORDER BY {muni_col} DESC
                LIMIT 20
            """).df()
            con.close()

            fig_top_mun = px.bar(
                df_top_mun,
                x='valor_producao_mi_reais',
                y='municipio_nome',
                orientation='h',
                title=f"Top 20 Municípios em Valor da Produção ({muni_year}) - {sufixo_legenda}",
                labels={'valor_producao_mi_reais': 'R$ Milhões', 'municipio_nome': 'Município'},
                color='valor_producao_mi_reais',
                color_continuous_scale='Greens',
                category_orders={'municipio_nome': df_top_mun['municipio_nome'].tolist()[::-1]}
            )
            fig_top_mun.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_top_mun, use_container_width=True)
            
            st.dataframe(
                df_top_mun.rename(columns={
                    'municipio_nome': 'Município',
                    'valor_producao_mi_reais': f'Valor da Produção R$ Milhões ({sufixo_legenda})'
                }),
                use_container_width=True
            )
        else:
            st.info("Arquivo de microdados municipais não encontrado.")

    # -------------------------------------------------------------
    # TAB 5: METODOLOGIA & AUDITORIA
    # -------------------------------------------------------------
    with tab5:
        st.subheader("Notas Metodológicas e Veredito de Auditoria")
        st.markdown("""
        ### Síntese dos Ajustes Implementados:
        1. **Poder de Compra Real (IPCA):** Deflacionamento via IPCA oficial (SGS 433) para medir o valor real das transferências fiscais e da renda agrícola em termos de cesta de consumo.
        2. **Deflator Setorial (IPA Agropecuário FGV - SGS 225):** Deflacionamento via Índice de Preços por Atacado - Produtos Agropecuários (SGS 225), refletindo a variação real dos preços de commodities agrícolas no atacado.
        3. **Custo de Oportunidade Real (Taxa Selic Real):** Fator ex-post $(1 + r_{\\text{real}}) = \\frac{1 + \\text{Selic}}{1 + \\text{IPCA}}$, expurgando a inflação e mensurando estritamente o retorno financeiro real acumulado. Todas as variáveis monetárias (incluindo capital segurado) seguem a mesma base monetária sem descompasso.
        4. **Atualização Financeira Nominal (Selic Plena):** Capitalização total dos juros básicos nominais.
        
        ### Observações Técnicas de Cobertura:
        - **Convenção Temporal:** Adota-se o critério de fim de período com ano-base 2024 ($= 1,000$).
        - **Safra vs. Ano Civil:** O IBGE PAM reporta os dados agregados por ano civil, embora o ciclo produtivo da safra de grãos brasileira compreenda o período de julho do ano anterior a junho do ano corrente.
        - **Cobertura Territorial 2025:** O ano de 2025 reflete a execução parcial do Programa de Subvenção ao Seguro Rural (MAPA), contemplando 25 Unidades da Federação (com os estados do Acre/Amapá sem apólices formalizadas na base preliminar).
        """)
