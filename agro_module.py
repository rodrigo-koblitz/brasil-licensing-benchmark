"""
Agricultural Module for Streamlit App
Integrates:
- IBGE PAM: Valor da Produção Agrícola Municipal e Estadual (2000-2024)
- MAPA PSR: Subvenção e Garantias do Seguro Rural (2006-2025)
"""

import os
try:
    import duckdb
except ImportError:
    duckdb = None
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

APP_DIR = os.path.dirname(os.path.abspath(__file__))
APP_DATA_DIR = os.path.join(APP_DIR, "data")
DATA_AGRO_DIR = r"G:\Meu Drive\UFMG\data_agro"

# Prioritize local app/data for Streamlit Cloud deployment, fallback to G: drive
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
    st.markdown('<div class="sub-header">Análise integrada do Valor da Produção Agrícola (IBGE - PAM) e da Subvenção ao Seguro Rural (MAPA - PSR) em escala estadual e municipal (2000–2025).</div>', unsafe_allow_html=True)

    df_state = load_agro_state_data()

    if df_state.empty:
        st.warning("Dados agropecuários ainda não foram processados ou arquivo não encontrado.")
        return

    # Top KPI Metrics Cards (Latest Available Year: 2024)
    df_2024 = df_state[df_state['ano'] == 2024]
    val_prod_total = df_2024['valor_producao_bi_reais'].sum()
    subv_total = df_2024['subvencao_federal_mi_reais'].sum()
    cap_seg_total = df_2024['capital_segurado_mi_reais'].sum() / 1e3
    apolices_total = df_2024['qtde_apolices_seguradas'].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric(
            label="🌾 Valor da Produção (2024)",
            value=f"R$ {val_prod_total:.1f} Bi",
            help="Valor da Produção Agrícola total medido pelo IBGE PAM em 2024"
        )
    with col2:
        st.metric(
            label="🛡️ Subvenção Federal PSR (2024)",
            value=f"R$ {subv_total:.1f} Mi",
            help="Recursos federais pagos pelo MAPA para subvencionar apólices de seguro rural"
        )
    with col3:
        st.metric(
            label="💰 Capital Segurado (2024)",
            value=f"R$ {cap_seg_total:.1f} Bi",
            help="Total do patrimônio agrícola protegido sob apólices com apoio federal"
        )
    with col4:
        st.metric(
            label="📋 Apólices Atendidas (2024)",
            value=f"{int(apolices_total):,}".replace(",", "."),
            help="Contratos de seguro rural subsidiados em 2024"
        )

    st.markdown("---")

    # Tabs for in-depth exploration
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Panorama Nacional & Regional",
        "🗺️ Comparativo entre Estados (UF)",
        "🔍 Detalhamento por Estado",
        "🏙️ Top Municípios Agrícolas"
    ])

    # -------------------------------------------------------------
    # TAB 1: PANORAMA NACIONAL & REGIONAL
    # -------------------------------------------------------------
    with tab1:
        st.subheader("Evolução Histórica da Agropecuária Nacional (2000–2024)")
        
        c_left, c_right = st.columns(2)
        
        with c_left:
            # National time-series IBGE PAM
            df_nat_pam = df_state[df_state['ano'] <= 2024].groupby('ano', as_index=False)['valor_producao_bi_reais'].sum()
            fig_nat = px.area(
                df_nat_pam, x='ano', y='valor_producao_bi_reais',
                title="Valor da Produção Agrícola Nacional (R$ Bilhões)",
                color_discrete_sequence=['#2e7d32'],
                labels={'ano': 'Ano', 'valor_producao_bi_reais': 'R$ Bilhões'}
            )
            fig_nat.update_layout(hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_nat, use_container_width=True)

        with c_right:
            # Regional distribution stacked
            df_reg = df_state[df_state['ano'] <= 2024].groupby(['ano', 'regiao'], as_index=False)['valor_producao_bi_reais'].sum()
            fig_reg = px.bar(
                df_reg, x='ano', y='valor_producao_bi_reais', color='regiao',
                title="Composição por Região Geográfica (R$ Bilhões)",
                color_discrete_map={
                    'Centro-Oeste': '#ff9800',
                    'Sul': '#2196f3',
                    'Sudeste': '#4caf50',
                    'Nordeste': '#e91e63',
                    'Norte': '#9c27b0'
                },
                labels={'ano': 'Ano', 'valor_producao_bi_reais': 'R$ Bilhões', 'regiao': 'Região'}
            )
            fig_reg.update_layout(barmode='stack', hovermode="x unified", margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_reg, use_container_width=True)

        st.markdown("### Apoio ao Seguro Rural Federal (MAPA - PSR)")
        df_nat_psr = df_state[(df_state['ano'] >= 2006) & (df_state['ano'] <= 2024)].groupby('ano', as_index=False).agg({
            'subvencao_federal_mi_reais': 'sum',
            'capital_segurado_mi_reais': 'sum'
        })
        
        fig_dual = go.Figure()
        fig_dual.add_trace(go.Bar(
            x=df_nat_psr['ano'],
            y=df_nat_psr['subvencao_federal_mi_reais'],
            name="Subvenção Federal (R$ Mi)",
            marker_color='#1976d2',
            yaxis='y1'
        ))
        fig_dual.add_trace(go.Scatter(
            x=df_nat_psr['ano'],
            y=df_nat_psr['capital_segurado_mi_reais'] / 1e3,
            name="Capital Protegido (R$ Bi)",
            mode='lines+markers',
            line=dict(color='#d32f2f', width=3),
            yaxis='y2'
        ))
        fig_dual.update_layout(
            title="Evolução do Apoio Financeiro ao Seguro Rural: Subvenção vs. Cobertura",
            yaxis=dict(title="Subvenção Federal (R$ Milhões)", titlefont=dict(color="#1976d2"), tickfont=dict(color="#1976d2")),
            yaxis2=dict(title="Capital Segurado (R$ Bilhões)", titlefont=dict(color="#d32f2f"), tickfont=dict(color="#d32f2f"), overlaying='y', side='right'),
            legend=dict(x=0.01, y=0.98),
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_dual, use_container_width=True)

    # -------------------------------------------------------------
    # TAB 2: COMPARATIVO ENTRE ESTADOS (UF)
    # -------------------------------------------------------------
    with tab2:
        st.subheader("Ranking e Distribuição Estadual")
        selected_year = st.slider("Selecione o Ano de Análise:", min_value=2000, max_value=2024, value=2024)

        df_yr = df_state[df_state['ano'] == selected_year].sort_values('valor_producao_bi_reais', ascending=False)

        col_a, col_b = st.columns([3, 2])
        with col_a:
            fig_bar = px.bar(
                df_yr.head(15),
                x='valor_producao_bi_reais',
                y='uf_nome',
                orientation='h',
                color='regiao',
                title=f"Top 15 Estados em Valor da Produção ({selected_year})",
                labels={'valor_producao_bi_reais': 'R$ Bilhões', 'uf_nome': 'Estado'},
                category_orders={'uf_nome': df_yr.head(15)['uf_nome'].tolist()[::-1]}
            )
            fig_bar.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_b:
            st.markdown(f"**Tabela Consolidada ({selected_year})**")
            cols_show = ['sigla_uf', 'uf_nome', 'regiao', 'valor_producao_bi_reais']
            if selected_year >= 2006:
                cols_show += ['subvencao_federal_mi_reais', 'capital_segurado_mi_reais']
            
            st.dataframe(
                df_yr[cols_show].rename(columns={
                    'sigla_uf': 'UF',
                    'uf_nome': 'Estado',
                    'regiao': 'Região',
                    'valor_producao_bi_reais': 'Produção (R$ Bi)',
                    'subvencao_federal_mi_reais': 'Subvenção (R$ Mi)',
                    'capital_segurado_mi_reais': 'Garantia (R$ Mi)'
                }),
                height=420,
                use_container_width=True
            )

        # Cross analysis scatter (if year >= 2006)
        if selected_year >= 2006:
            st.markdown(f"### Relação: Valor da Produção vs. Cobertura de Seguro ({selected_year})")
            fig_scat = px.scatter(
                df_yr[df_yr['valor_producao_bi_reais'] > 0.5],
                x='valor_producao_bi_reais',
                y='subvencao_federal_mi_reais',
                size='capital_segurado_mi_reais',
                color='regiao',
                text='sigla_uf',
                title="Produção Agrícola (Eixo X) vs. Subvenção ao Seguro Rural (Eixo Y)",
                labels={
                    'valor_producao_bi_reais': 'Valor da Produção (R$ Bilhões)',
                    'subvencao_federal_mi_reais': 'Subvenção Federal (R$ Milhões)',
                    'capital_segurado_mi_reais': 'Capital Segurado (R$ Mi)'
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
                x='ano', y='valor_producao_bi_reais',
                markers=True,
                title=f"Valor da Produção Agrícola - {selected_uf} (R$ Bi)",
                color_discrete_sequence=['#2e7d32']
            )
            fig_uf_pam.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_uf_pam, use_container_width=True)

        with c_u2:
            fig_uf_psr = px.bar(
                df_single_uf[(df_single_uf['ano'] >= 2006) & (df_single_uf['ano'] <= 2024)],
                x='ano', y='subvencao_federal_mi_reais',
                title=f"Subvenção ao Seguro Rural - {selected_uf} (R$ Mi)",
                color_discrete_sequence=['#1565c0']
            )
            fig_uf_psr.update_layout(margin=dict(l=20, r=20, t=40, b=20))
            st.plotly_chart(fig_uf_psr, use_container_width=True)

        # State Data Table
        st.dataframe(
            df_single_uf[['ano', 'valor_producao_bi_reais', 'subvencao_federal_mi_reais', 'capital_segurado_mi_reais', 'qtde_apolices_seguradas']].rename(columns={
                'ano': 'Ano',
                'valor_producao_bi_reais': 'Produção IBGE (R$ Bi)',
                'subvencao_federal_mi_reais': 'Subvenção MAPA (R$ Mi)',
                'capital_segurado_mi_reais': 'Capital Segurado (R$ Mi)',
                'qtde_apolices_seguradas': 'Apólices Subvencionadas'
            }),
            use_container_width=True
        )

    # -------------------------------------------------------------
    # TAB 4: TOP MUNICÍPIOS AGRÍCOLAS
    # -------------------------------------------------------------
    with tab4:
        st.subheader("Granularidade Municipal: Os Maiores Polos Produtivos do Brasil")
        
        muni_year = st.selectbox("Ano de Referência Municipal:", options=list(range(2024, 1999, -1)), index=0)
        
        if os.path.exists(MUNI_PARQUET):
            if duckdb is not None:
                con = duckdb.connect()
                muni_pq_clean = MUNI_PARQUET.replace(chr(92), '/')
                df_top_mun = con.execute(f"""
                    SELECT 
                        municipio_nome,
                        valor_producao_mil_reais / 1e3 AS valor_producao_mi_reais
                    FROM '{muni_pq_clean}'
                    WHERE ano = {muni_year}
                    ORDER BY valor_producao_mil_reais DESC
                    LIMIT 20
                """).df()
                con.close()
            else:
                df_m_all = pd.read_parquet(MUNI_PARQUET, columns=['municipio_nome', 'valor_producao_mil_reais', 'ano'])
                df_sub = df_m_all[df_m_all['ano'] == muni_year].sort_values(by='valor_producao_mil_reais', ascending=False).head(20)
                df_top_mun = pd.DataFrame({
                    'municipio_nome': df_sub['municipio_nome'],
                    'valor_producao_mi_reais': df_sub['valor_producao_mil_reais'] / 1e3
                })

            fig_top_mun = px.bar(
                df_top_mun,
                x='valor_producao_mi_reais',
                y='municipio_nome',
                orientation='h',
                title=f"Top 20 Municípios em Valor da Produção ({muni_year})",
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
                    'valor_producao_mi_reais': 'Valor da Produção (R$ Milhões)'
                }),
                use_container_width=True
            )
        else:
            st.info("Arquivo de microdados municipais não encontrado.")
