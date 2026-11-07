import os
import json
import glob
import streamlit as st
import pandas as pd
import folium
from folium import plugins

# Helper dictionary for State coordinates (Centroids)
STATE_COORDINATES = {
    'AC': [-9.0238, -70.812], 'AL': [-9.5713, -36.782], 'AM': [-3.4168, -65.8561],
    'AP': [1.41, -51.77], 'BA': [-12.9714, -38.5014], 'CE': [-5.4984, -39.3206],
    'DF': [-15.7998, -47.8645], 'ES': [-19.1834, -40.3089], 'GO': [-15.827, -49.8362],
    'MA': [-5.42, -45.44], 'MG': [-18.5122, -44.555], 'MS': [-20.7722, -54.7852],
    'MT': [-12.6819, -56.9211], 'PA': [-3.793, -52.482], 'PB': [-7.24, -36.78],
    'PE': [-8.8137, -36.9541], 'PI': [-7.7183, -42.7289], 'PR': [-25.2521, -52.0215],
    'RJ': [-22.9068, -43.1729], 'RN': [-5.7945, -36.56], 'RO': [-11.5057, -63.5806],
    'RR': [2.7376, -62.0751], 'RS': [-30.0346, -51.2177], 'SC': [-27.2423, -50.2189],
    'SE': [-10.5741, -37.3857], 'SP': [-23.5505, -46.6333], 'TO': [-10.1753, -48.2982],
    'IBAMA': [-15.7797, -47.9297]
}

STATE_NAMES = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AM': 'Amazonas', 'AP': 'Amapá', 'BA': 'Bahia',
    'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
    'MA': 'Maranhão', 'MG': 'Minas Gerais', 'MS': 'Mato Grosso do Sul', 'MT': 'Mato Grosso',
    'PA': 'Pará', 'PB': 'Paraíba', 'PE': 'Pernambuco', 'PI': 'Piauí', 'PR': 'Paraná',
    'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RO': 'Rondônia', 'RR': 'Roraima',
    'RS': 'Rio Grande do Sul', 'SC': 'Santa Catarina', 'SE': 'Sergipe', 'SP': 'São Paulo',
    'TO': 'Tocantins', 'IBAMA': 'IBAMA (Âmbito Federal)'
}

def find_state_edit_files(data_dir):
    """Dynamically discover any [XX]_edit.csv in data_dir or root project dir."""
    found = {}
    search_dirs = [data_dir, os.path.dirname(data_dir), os.path.dirname(os.path.dirname(data_dir))]
    for d in search_dirs:
        if not os.path.exists(d): continue
        for f in glob.glob(os.path.join(d, "*_edit.csv")):
            fname = os.path.basename(f)
            uf = fname.split("_")[0].upper()
            if len(uf) == 2 and uf not in found:
                found[uf] = f
    return found

def render_map_module(data_dir):
    st.markdown('<div class="main-header">🗺️ Mapa Interativo: Desmatamento e Licenciamento Ambiental (Leaflet)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Visualização geoespacial integrada com suporte a visualização pontual dos empreendimentos ([UF]_edit.csv) e macrovisão estadual/nacional.</div>', unsafe_allow_html=True)

    # 1. Discover available [UF]_edit.csv files
    edit_files = find_state_edit_files(data_dir)
    available_edit_ufs = sorted(list(edit_files.keys()))

    # Global Mode Selector
    opcoes_modo = [
        "📍 Empreendimentos Individuais no Mapa (Latitude/Longitude dos arquivos [UF]_edit.csv)",
        "🇧🇷 Macrovisão Nacional & Estadual (Choropleth de Polígonos e Desmatamento MapBiomas)"
    ]
    modo_mapa = st.radio(
        "Selecione o Tipo de Mapa:",
        options=opcoes_modo,
        index=0,
        horizontal=True
    )

    # ==============================================================================
    # MODO A: EMPREENDIMENTOS INDIVIDUAIS COM LATITUDE/LONGITUDE ([UF]_edit.csv)
    # ==============================================================================
    if "Empreendimentos Individuais" in modo_mapa:
        st.markdown("### 📍 Empreendimentos Georreferenciados (Pontos e Clusters Reais)")
        
        if not available_edit_ufs:
            st.warning("Nenhum arquivo [UF]_edit.csv encontrado no diretório de dados.")
            return

        col_c1, col_c2, col_c3, col_c4 = st.columns([1, 1, 1, 1])
        with col_c1:
            uf_sel = st.selectbox("Selecione a Unidade Federativa (UF):", available_edit_ufs, index=0)
        
        file_path = edit_files[uf_sel]
        
        # Load state edit csv
        try:
            df_edit = pd.read_csv(file_path, sep=";", encoding="latin1", low_memory=False)
        except Exception:
            df_edit = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
            
        df_edit['Latitude'] = pd.to_numeric(df_edit['Latitude'], errors='coerce')
        df_edit['Longitude'] = pd.to_numeric(df_edit['Longitude'], errors='coerce')
        valid_points = df_edit.dropna(subset=['Latitude', 'Longitude']).copy()

        # Extract Year column
        col_emiss = [c for c in valid_points.columns if 'emiss' in c.lower()]
        if col_emiss:
            valid_points['ano_ato'] = valid_points[col_emiss[0]].astype(str).str.extract(r'^(19\d\d|20\d\d)')[0].fillna('Não informado')
        else:
            valid_points['ano_ato'] = 'Não informado'

        anos_disponiveis = ["Todos"] + sorted([str(a) for a in valid_points['ano_ato'].unique() if str(a) != 'Não informado'])

        with col_c2:
            ano_filtro = st.selectbox("Ano de Emissão do Ato:", anos_disponiveis, index=0)

        with col_c3:
            precisoes = ["Todas"] + sorted([str(p) for p in valid_points['geo_precision_level'].dropna().unique()])
            sel_prec = st.selectbox("Nível de Precisão:", precisoes, index=0)
            
        with col_c4:
            tipos = ["Todas as Tipologias"] + sorted([str(t) for t in valid_points['Tipo da licença'].dropna().unique() if str(t).strip()])
            sel_tipo = st.selectbox("Tipologia de Licença:", tipos, index=0)

        # Apply Filters
        df_filtered = valid_points.copy()
        if ano_filtro != "Todos":
            df_filtered = df_filtered[df_filtered['ano_ato'] == ano_filtro]
        if sel_prec != "Todas":
            df_filtered = df_filtered[df_filtered['geo_precision_level'] == sel_prec]
        if sel_tipo != "Todas as Tipologias":
            df_filtered = df_filtered[df_filtered['Tipo da licença'] == sel_tipo]

        # Top Metric Cards
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Empreendimentos Filtrados", f"{len(df_filtered):,}")
        col_m2.metric("Total no Estado", f"{len(valid_points):,}")
        col_m3.metric("Localizações Distintas", f"{len(df_filtered[['Latitude', 'Longitude']].drop_duplicates()):,}")
        col_m4.metric("UF Selecionada", f"{uf_sel} - {STATE_NAMES.get(uf_sel, '')}")

        # Map Center
        center = STATE_COORDINATES.get(uf_sel, [-12.9714, -38.5014])
        m_state = folium.Map(location=center, zoom_start=7, tiles="CartoDB positron")

        folium.TileLayer('OpenStreetMap', name='OpenStreetMap (Ruas)').add_to(m_state)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Satellite',
            name='Satélite (Esri World Imagery)'
        ).add_to(m_state)

        # FastMarkerCluster with all coordinates
        coords_list = df_filtered[['Latitude', 'Longitude']].values.tolist()
        plugins.FastMarkerCluster(
            data=coords_list,
            name=f"Clusters de Empreendimentos ({len(coords_list):,} atos)"
        ).add_to(m_state)

        folium.LayerControl(collapsed=False).add_to(m_state)

        # Render Map
        map_html = m_state._repr_html_()
        st.components.v1.html(map_html, height=640, scrolling=False)

        # Data Table Below Map
        st.markdown("#### 📋 Base de Dados dos Empreendimentos Georreferenciados")
        cols_to_show = [
            c for c in [
                df_edit.columns[0], 'Tipo da licença', 'Nome do empreendimento',
                'Nome do empreendedor', 'Município do empreendimento', 'CEP do empreendimento',
                'Latitude', 'Longitude', 'geo_precision_level', 'geo_source'
            ] if c in df_edit.columns
        ]
        st.dataframe(df_filtered[cols_to_show].head(1000), use_container_width=True)
        return

    # ==============================================================================
    # MODO B: MACROVISÃO NACIONAL (Choropleth de Polígonos)
    # ==============================================================================
    lic_file = os.path.join(data_dir, "licencas_estado_ano_macrotipos.csv")
    desm_file = os.path.join(data_dir, "mapbiomas_desmatamento_estado_ano.csv")
    geojson_file = os.path.join(data_dir, "br_states.geojson")

    if not os.path.exists(lic_file) or not os.path.exists(desm_file):
        st.error("Arquivos de dados macroeconômicos não encontrados.")
        return

    df_lic = pd.read_csv(lic_file)
    df_desm = pd.read_csv(desm_file)

    anos_lic = sorted(df_lic['ano'].dropna().unique().astype(int).tolist())
    anos_desm = sorted(df_desm['ano'].dropna().unique().astype(int).tolist())
    anos_comuns = sorted(list(set(anos_lic).intersection(set(anos_desm))))

    st.markdown("### ⚙️ Painel de Controle de Camadas e Filtros Espaciais")
    col_f1, col_f2, col_f3 = st.columns([1, 1, 2])

    with col_f1:
        # Permitir selecionar 'Todos os Anos (Acumulado Histórico)' ou um ano específico
        opcoes_ano = ["Todos os Anos (Acumulado Histórico)"] + [str(a) for a in reversed(anos_comuns)]
        ano_macro_sel = st.selectbox("Selecione o Ano de Análise:", opcoes_ano, index=0)
    
    with col_f2:
        # Opções de tema incluindo 'Sem Camada Coroplética' para ver apenas o mapa limpo
        opcoes_tema = [
            "Desmatamento Anual (Hectares)",
            "Licenças Totais Emitidas",
            "Licenças Rurais e Supressão (ASV/CAR/LAR)",
            "Licenças de Obras e Implantação (LP/LI)",
            "Licenças de Operação Contínua (LO)",
            "Nenhuma (Apenas Mapa Base e Marcadores)"
        ]
        tema_mapa = st.selectbox("Camada de Fundo (Choropleth Polígonos):", opcoes_tema, index=0)

    with col_f3:
        all_ufs = sorted(list(set(df_lic['UF'].unique().tolist()).union(set(df_desm['UF'].unique().tolist()))))
        ufs_sel = st.multiselect(
            "Unidades Federativas & Órgãos Ativos no Mapa:",
            options=all_ufs,
            default=all_ufs
        )

    # Filter Data by Year or Accumulate
    if ano_macro_sel == "Todos os Anos (Acumulado Histórico)":
        df_lic_agg = df_lic.groupby('UF')[['TOTAL_LICENCAS', 'INFRA_CONSTR', 'INFRA_OP', 'RURAL_VEG']].sum().reset_index()
        df_desm_agg = df_desm.groupby('UF')[['area_ha', 'area_km2']].sum().reset_index()
        df_map = pd.merge(df_lic_agg, df_desm_agg, on='UF', how='outer').fillna(0)
        label_ano = "Histórico Acumulado (2000-2025)"
    else:
        ano_int = int(ano_macro_sel)
        df_lic_agg = df_lic[df_lic['ano'] == ano_int].copy()
        df_desm_agg = df_desm[df_desm['ano'] == ano_int][['UF', 'area_ha', 'area_km2']].copy()
        df_map = pd.merge(df_lic_agg, df_desm_agg, on='UF', how='outer').fillna(0)
        label_ano = f"Ano {ano_int}"

    df_map['DESMATAMENTO_HA'] = df_map['area_ha']
    df_map['DESMATAMENTO_KM2'] = df_map['area_km2']
    df_map['Nome'] = df_map['UF'].map(STATE_NAMES).fillna(df_map['UF'])
    df_map['lat'] = df_map['UF'].map(lambda u: STATE_COORDINATES.get(u, [None, None])[0])
    df_map['lon'] = df_map['UF'].map(lambda u: STATE_COORDINATES.get(u, [None, None])[1])
    df_map = df_map[df_map['UF'].isin(ufs_sel)]

    # Metrics Summary Cards
    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
    col_t1.metric(f"Total de Licenças ({label_ano})", f"{df_map['TOTAL_LICENCAS'].sum():,.0f}")
    col_t2.metric(f"Desmatamento ({label_ano})", f"{df_map['DESMATAMENTO_HA'].sum():,.0f} ha")
    ibama_count = df_map[df_map['UF']=='IBAMA']['TOTAL_LICENCAS'].sum() if 'IBAMA' in df_map['UF'].values else 0
    col_t3.metric("Atos IBAMA Federal", f"{ibama_count:,.0f}")
    col_t4.metric("Estados Selecionados", f"{len(df_map)} UFs")

    # Initialize Base Leaflet Map
    m = folium.Map(location=[-14.235, -51.9253], zoom_start=4, tiles="CartoDB positron")
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap (Ruas)').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Satellite',
        name='Satélite (Esri World Imagery)'
    ).add_to(m)

    # Choropleth polygon layer
    if tema_mapa != "Nenhuma (Apenas Mapa Base e Marcadores)" and os.path.exists(geojson_file):
        metric_cols = {
            "Licenças Totais Emitidas": "TOTAL_LICENCAS",
            "Desmatamento Anual (Hectares)": "DESMATAMENTO_HA",
            "Licenças Rurais e Supressão (ASV/CAR/LAR)": "RURAL_VEG",
            "Licenças de Obras e Implantação (LP/LI)": "INFRA_CONSTR",
            "Licenças de Operação Contínua (LO)": "INFRA_OP"
        }
        target_metric = metric_cols[tema_mapa]
        with open(geojson_file, 'r', encoding='utf-8') as gf:
            br_geo = json.load(gf)

        fill_color_scheme = 'YlOrRd' if 'Desmatamento' in tema_mapa else 'YlGnBu'
        folium.Choropleth(
            geo_data=br_geo,
            name=f"Camada Temática: {tema_mapa}",
            data=df_map[df_map['UF'] != 'IBAMA'],
            columns=['UF', target_metric],
            key_on='properties.UF_05',
            fill_color=fill_color_scheme,
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name=f"{tema_mapa} ({label_ano})"
        ).add_to(m)

    marker_group_states = folium.FeatureGroup(name="Marcadores Interativos (Estados)").add_to(m)
    marker_group_ibama = folium.FeatureGroup(name="Órgão Federal (IBAMA)").add_to(m)

    for _, row in df_map.iterrows():
        uf = row['UF']
        is_fed = (uf == 'IBAMA')
        if pd.isna(row['lat']) or pd.isna(row['lon']): continue

        html_popup = f"""
        <div style="font-family: Arial, sans-serif; width: 260px; font-size: 12px; line-height: 1.4;">
            <div style="background-color: {'#1E3A8A' if not is_fed else '#DC2626'}; color: white; padding: 6px 10px; border-radius: 4px; font-weight: bold; font-size: 13px;">
                {'🏛️ ' + row['Nome'] if is_fed else '📍 ' + row['Nome'] + ' (' + uf + ')'}
            </div>
            <div style="padding: 8px 4px;">
                <b>Período:</b> {label_ano}<br>
                <hr style="margin: 4px 0; border: 0; border-top: 1px solid #E2E8F0;">
                <b>Total de Licenças:</b> <span style="color: #059669; font-weight: bold;">{row['TOTAL_LICENCAS']:,.0f}</span><br>
                <b>• Obras/Implantação (LP/LI):</b> {row['INFRA_CONSTR']:,.0f}<br>
                <b>• Operação (LO):</b> {row['INFRA_OP']:,.0f}<br>
                <b>• Rural/Supressão (CAR/ASV):</b> {row['RURAL_VEG']:,.0f}<br>
                <hr style="margin: 4px 0; border: 0; border-top: 1px solid #E2E8F0;">
                <b>Desmatamento (MapBiomas):</b><br>
                <span style="color: #DC2626; font-weight: bold;">{row['DESMATAMENTO_HA']:,.0f} ha</span> ({row['DESMATAMENTO_KM2']:,.1f} km²)<br>
            </div>
        </div>
        """
        iframe = folium.IFrame(html=html_popup, width=280, height=210)
        popup = folium.Popup(iframe, max_width=300)

        if is_fed:
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=popup,
                tooltip=f"🏢 IBAMA: {row['TOTAL_LICENCAS']:,.0f} Licenças Federais",
                icon=folium.Icon(color='red', icon='certificate', prefix='glyphicon')
            ).add_to(marker_group_ibama)
        else:
            radius = 6 + (row['TOTAL_LICENCAS'] ** 0.3)
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=min(radius, 22),
                popup=popup,
                tooltip=f"<b>{uf} - {row['Nome']}</b><br>Licenças: {row['TOTAL_LICENCAS']:,.0f} | Desm: {row['DESMATAMENTO_HA']:,.0f} ha",
                color='#1E3A8A', fill=True, fill_color='#3B82F6', fill_opacity=0.8, weight=1.5
            ).add_to(marker_group_states)

    folium.LayerControl(collapsed=False).add_to(m)
    map_html = m._repr_html_()
    st.components.v1.html(map_html, height=640, scrolling=False)
