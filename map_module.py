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
    st.markdown('<div class="sub-header">Visualização geoespacial integrada: Macrovisão Nacional (Coroplético e Estatístico) e Microvisão Pontual de Empreendimentos ([UF]_edit.csv).</div>', unsafe_allow_html=True)

    # 1. Discover available [UF]_edit.csv files
    edit_files = find_state_edit_files(data_dir)
    available_edit_ufs = sorted(list(edit_files.keys()))

    # Mode Selector: Visão Geral Nacional vs. Detalhamento Estadual de Empreendimentos
    modo_mapa = st.radio(
        "Selecione o Nível de Visualização Geoespacial:",
        options=[
            "🇧🇷 Macrovisão Nacional (Choropleth de Licenças e Desmatamento MapBiomas)",
            f"📍 Microvisão Pontual de Empreendimentos por Estado ({', '.join(available_edit_ufs)})"
        ],
        index=1 if available_edit_ufs else 0,
        horizontal=True
    )

    # ==============================================================================
    # MODO 2: MICROVISÃO PONTUAL DE EMPREENDIMENTOS ([UF]_edit.csv)
    # ==============================================================================
    if "Microvisão Pontual" in modo_mapa:
        st.markdown("### 📍 Empreendimentos Licenciados com Coordenadas Reais (Latitude/Longitude)")
        
        col_c1, col_c2, col_c3 = st.columns([1, 1, 2])
        with col_c1:
            uf_sel = st.selectbox("Selecione o Estado:", available_edit_ufs, index=0)
        
        file_path = edit_files[uf_sel]
        
        # Load state edit csv
        try:
            df_edit = pd.read_csv(file_path, sep=";", encoding="latin1", low_memory=False)
        except Exception:
            df_edit = pd.read_csv(file_path, sep=";", encoding="utf-8", low_memory=False)
            
        # Clean coordinates
        df_edit['Latitude'] = pd.to_numeric(df_edit['Latitude'], errors='coerce')
        df_edit['Longitude'] = pd.to_numeric(df_edit['Longitude'], errors='coerce')
        valid_points = df_edit.dropna(subset=['Latitude', 'Longitude'])
        
        with col_c2:
            precisoes = sorted([str(p) for p in valid_points['geo_precision_level'].dropna().unique()])
            sel_prec = st.multiselect("Nível de Precisão:", options=precisoes, default=precisoes)
            
        with col_c3:
            tipos = sorted([str(t) for t in valid_points['Tipo da licença'].dropna().unique() if str(t).strip()])
            top_tipos = tipos[:5] if len(tipos) >= 5 else tipos
            sel_tipos = st.multiselect("Tipologia de Licença:", options=tipos, default=top_tipos)

        # Filter
        df_filtered = valid_points[
            valid_points['geo_precision_level'].isin(sel_prec) &
            valid_points['Tipo da licença'].isin(sel_tipos)
        ]

        st.caption(f"Exibindo **{len(df_filtered):,}** de **{len(valid_points):,}** empreendimentos georreferenciados para o estado de **{STATE_NAMES.get(uf_sel, uf_sel)}**.")

        # Map Center
        center = STATE_COORDINATES.get(uf_sel, [-12.9714, -38.5014])
        m_state = folium.Map(location=center, zoom_start=6, tiles="CartoDB positron")

        # Tile Layers
        folium.TileLayer('OpenStreetMap', name='OpenStreetMap (Ruas)').add_to(m_state)
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri Satellite',
            name='Esri Satélite (Alta Resolução)'
        ).add_to(m_state)

        # Marker Cluster for high performance
        marker_cluster = plugins.FastMarkerCluster(
            data=df_filtered[['Latitude', 'Longitude']].values.tolist(),
            name=f"Cluster: {uf_sel} ({len(df_filtered):,} pontos)"
        ).add_to(m_state)

        folium.LayerControl(collapsed=False).add_to(m_state)

        # Render Folium
        map_html = m_state._repr_html_()
        st.components.v1.html(map_html, height=620, scrolling=False)

        # Detail Table below map
        st.markdown("#### 📋 Amostra dos Empreendimentos Georreferenciados")
        cols_to_show = [
            c for c in [
                df_edit.columns[0], 'Tipo da licença', 'Nome do empreendimento',
                'Nome do empreendedor', 'Município do empreendimento', 'CEP do empreendimento',
                'Latitude', 'Longitude', 'geo_precision_level', 'geo_source'
            ] if c in df_edit.columns
        ]
        st.dataframe(df_filtered[cols_to_show].head(500), use_container_width=True)
        return

    # ==============================================================================
    # MODO 1: MACROVISÃO NACIONAL (Choropleth & Estatísticas)
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
        ano_sel = st.selectbox("Selecione o Ano de Análise:", anos_comuns, index=len(anos_comuns)-1)
    
    with col_f2:
        tema_mapa = st.selectbox(
            "Camada de Fundo (Choropleth Polígonos):",
            [
                "Licenças Totais Emitidas",
                "Desmatamento Anual (Hectares)",
                "Licenças Rurais e Supressão (ASV/CAR/LAR)",
                "Licenças de Obras e Implantação (LP/LI)",
                "Licenças de Operação Contínua (LO)"
            ]
        )

    with col_f3:
        all_ufs = sorted(list(set(df_lic['UF'].unique().tolist()).union(set(df_desm['UF'].unique().tolist()))))
        ufs_sel = st.multiselect(
            "Unidades Federativas & Órgãos Ativos no Mapa:",
            options=all_ufs,
            default=all_ufs
        )

    # Filter by Year
    df_lic_ano = df_lic[df_lic['ano'] == ano_sel].copy()
    df_desm_ano = df_desm[df_desm['ano'] == ano_sel].copy()

    df_map = pd.merge(df_lic_ano, df_desm_ano[['UF', 'area_ha', 'area_km2']], on='UF', how='outer')
    df_map = df_map.fillna(0)
    df_map['DESMATAMENTO_HA'] = df_map['area_ha']
    df_map['DESMATAMENTO_KM2'] = df_map['area_km2']
    df_map['Nome'] = df_map['UF'].map(STATE_NAMES).fillna(df_map['UF'])
    df_map['lat'] = df_map['UF'].map(lambda u: STATE_COORDINATES.get(u, [None, None])[0])
    df_map['lon'] = df_map['UF'].map(lambda u: STATE_COORDINATES.get(u, [None, None])[1])
    df_map = df_map[df_map['UF'].isin(ufs_sel)]

    # Choropleth Metric
    metric_cols = {
        "Licenças Totais Emitidas": "TOTAL_LICENCAS",
        "Desmatamento Anual (Hectares)": "DESMATAMENTO_HA",
        "Licenças Rurais e Supressão (ASV/CAR/LAR)": "RURAL_VEG",
        "Licenças de Obras e Implantação (LP/LI)": "INFRA_CONSTR",
        "Licenças de Operação Contínua (LO)": "INFRA_OP"
    }
    target_metric = metric_cols[tema_mapa]

    # Initialize Base Leaflet Map
    m = folium.Map(location=[-14.235, -51.9253], zoom_start=4, tiles="CartoDB positron")
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap (Ruas)').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri Satellite',
        name='Esri Satélite (Alta Resolução)'
    ).add_to(m)

    # Choropleth polygon layer
    if os.path.exists(geojson_file):
        with open(geojson_file, 'r', encoding='utf-8') as gf:
            br_geo = json.load(gf)

        fill_color_scheme = 'YlOrRd' if 'Desmatamento' in tema_mapa else 'YlGnBu'
        folium.Choropleth(
            geo_data=br_geo,
            name=f"Choropleth: {tema_mapa} ({ano_sel})",
            data=df_map[df_map['UF'] != 'IBAMA'],
            columns=['UF', target_metric],
            key_on='properties.UF_05',
            fill_color=fill_color_scheme,
            fill_opacity=0.7,
            line_opacity=0.3,
            legend_name=f"{tema_mapa} - Ano {ano_sel}"
        ).add_to(m)

    marker_group_states = folium.FeatureGroup(name="Círculos Estaduais de Resumo").add_to(m)
    marker_group_ibama = folium.FeatureGroup(name="Destaque Federal: IBAMA").add_to(m)

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
                <b>Ano de Referência:</b> {ano_sel}<br>
                <hr style="margin: 4px 0; border: 0; border-top: 1px solid #E2E8F0;">
                <b>Total de Licenças:</b> <span style="color: #059669; font-weight: bold;">{row['TOTAL_LICENCAS']:,.0f}</span><br>
                <b>• Obras/Implantação (LP/LI):</b> {row['INFRA_CONSTR']:,.0f}<br>
                <b>• Operação (LO):</b> {row['INFRA_OP']:,.0f}<br>
                <b>• Rural/Supressão (CAR/ASV):</b> {row['RURAL_VEG']:,.0f}<br>
                <hr style="margin: 4px 0; border: 0; border-top: 1px solid #E2E8F0;">
                <b>Desmatamento Anual (MapBiomas):</b><br>
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
                tooltip=f"🏢 IBAMA: {row['TOTAL_LICENCAS']:,.0f} Licenças Federais ({ano_sel})",
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
    st.components.v1.html(map_html, height=620, scrolling=False)
