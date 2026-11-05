import os
import json
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
    'IBAMA': [-15.7797, -47.9297] # Sede do IBAMA em Brasília
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

def render_map_module(data_dir):
    st.markdown('<div class="main-header">🗺️ Mapa Interativo: Desmatamento e Licenciamento Ambiental (Leaflet)</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Visualização geoespacial integrada do esforço de licenciamento ambiental (Estadual e Federal/IBAMA) e da dinâmica de supressão de vegetação nativa (MapBiomas).</div>', unsafe_allow_html=True)

    # 1. Load Data
    lic_file = os.path.join(data_dir, "licencas_estado_ano_macrotipos.csv")
    desm_file = os.path.join(data_dir, "mapbiomas_desmatamento_estado_ano.csv")
    geojson_file = os.path.join(data_dir, "br_states.geojson")

    if not os.path.exists(lic_file) or not os.path.exists(desm_file):
        st.error("Arquivos de dados geoespaciais não encontrados.")
        return

    df_lic = pd.read_csv(lic_file)
    df_desm = pd.read_csv(desm_file)

    # Years available
    anos_lic = sorted(df_lic['ano'].dropna().unique().astype(int).tolist())
    anos_desm = sorted(df_desm['ano'].dropna().unique().astype(int).tolist())
    anos_comuns = sorted(list(set(anos_lic).intersection(set(anos_desm))))

    # Sidebar / Top Filters for the Map
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
        # Ensure IBAMA is prominent
        ufs_sel = st.multiselect(
            "Unidades Federativas & Órgãos Ativos no Mapa:",
            options=all_ufs,
            default=all_ufs
        )

    # Filter data for selected year
    sub_lic_ano = df_lic[df_lic['ano'] == ano_sel].copy()
    sub_desm_ano = df_desm[df_desm['ano'] == ano_sel].copy()

    # Build master unified map table per UF
    map_rows = []
    for uf in ufs_sel:
        # Licenses
        lic_row = sub_lic_ano[sub_lic_ano['UF'] == uf]
        tot_lic = float(lic_row['TOTAL_LICENCAS'].iloc[0]) if len(lic_row) > 0 else 0.0
        rural_lic = float(lic_row['RURAL_VEG'].iloc[0]) if len(lic_row) > 0 else 0.0
        infra_constr = float(lic_row['INFRA_CONSTR'].iloc[0]) if len(lic_row) > 0 else 0.0
        infra_op = float(lic_row['INFRA_OP'].iloc[0]) if len(lic_row) > 0 else 0.0

        # Deforestation
        desm_row = sub_desm_ano[sub_desm_ano['UF'] == uf]
        desm_ha = float(desm_row['area_ha'].iloc[0]) if len(desm_row) > 0 else 0.0
        desm_km2 = float(desm_row['area_km2'].iloc[0]) if len(desm_row) > 0 else 0.0

        coords = STATE_COORDINATES.get(uf, [-14.235, -51.925])
        nome_completo = STATE_NAMES.get(uf, uf)

        map_rows.append({
            'UF': uf,
            'Nome': nome_completo,
            'ano': ano_sel,
            'TOTAL_LICENCAS': tot_lic,
            'RURAL_VEG': rural_lic,
            'INFRA_CONSTR': infra_constr,
            'INFRA_OP': infra_op,
            'DESMATAMENTO_HA': desm_ha,
            'DESMATAMENTO_KM2': desm_km2,
            'lat': coords[0],
            'lon': coords[1],
            'is_federal': (uf == 'IBAMA')
        })

    df_map = pd.DataFrame(map_rows)

    # KPI summary bar above map
    k1, k2, k3, k4 = st.columns(4)
    k1.metric(f"Total de Licenças ({ano_sel})", f"{df_map['TOTAL_LICENCAS'].sum():,.0f}")
    k2.metric(f"Desmatamento ({ano_sel})", f"{df_map['DESMATAMENTO_HA'].sum():,.0f} ha")
    ibama_count = df_map[df_map['UF'] == 'IBAMA']['TOTAL_LICENCAS'].sum()
    k3.metric(f"Atos IBAMA Federal ({ano_sel})", f"{ibama_count:,.0f}")
    k4.metric("Estados Selecionados", f"{len(df_map)} UFs")

    # 2. Build Folium / Leaflet Map
    # Base map centered in Brazil
    m = folium.Map(
        location=[-14.5, -53.0],
        zoom_start=4,
        tiles='cartodbpositron',
        control_scale=True
    )

    # Add TileLayer choices
    folium.TileLayer('OpenStreetMap', name='OpenStreetMap').add_to(m)
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite (Esri World Imagery)'
    ).add_to(m)

    # Choropleth Polygons Layer (GeoJSON)
    if os.path.exists(geojson_file):
        with open(geojson_file, 'r', encoding='utf-8') as gf:
            geo_data = json.load(gf)

        # Decide column and colormap for Choropleth
        if tema_mapa == "Desmatamento Anual (Hectares)":
            col_target = 'DESMATAMENTO_HA'
            color_scheme = 'YlOrRd'
            legend_title = f'Desmatamento em {ano_sel} (Hectares)'
        elif tema_mapa == "Licenças Rurais e Supressão (ASV/CAR/LAR)":
            col_target = 'RURAL_VEG'
            color_scheme = 'PuBuGn'
            legend_title = f'Licenças Rurais/Supressão em {ano_sel}'
        elif tema_mapa == "Licenças de Obras e Implantação (LP/LI)":
            col_target = 'INFRA_CONSTR'
            color_scheme = 'YlGnBu'
            legend_title = f'Licenças de Implantação em {ano_sel}'
        elif tema_mapa == "Licenças de Operação Contínua (LO)":
            col_target = 'INFRA_OP'
            color_scheme = 'BuGn'
            legend_title = f'Licenças de Operação em {ano_sel}'
        else: # Licenças Totais
            col_target = 'TOTAL_LICENCAS'
            color_scheme = 'YlGn'
            legend_title = f'Licenças Totais em {ano_sel}'

        # Filter out IBAMA from polygon fill (as IBAMA has no polygon, it is federal)
        df_poly = df_map[df_map['UF'] != 'IBAMA'][['UF', col_target]].copy()

        try:
            folium.Choropleth(
                geo_data=geo_data,
                name=f'Camada Temática: {tema_mapa}',
                data=df_poly,
                columns=['UF', col_target],
                key_on='feature.properties.UF_05',
                fill_color=color_scheme,
                fill_opacity=0.68,
                line_opacity=0.35,
                line_color='black',
                line_weight=1,
                legend_name=legend_title,
                smooth_factor=0.5
            ).add_to(m)
        except Exception as e:
            st.warning(f"Aviso no carregamento do polígono: {e}")

    # 3. Add Interactive Markers & Popups for Selected States & IBAMA
    marker_group_states = folium.FeatureGroup(name="Marcadores Interativos (Estados)", show=True).add_to(m)
    marker_group_ibama = folium.FeatureGroup(name="Órgão Federal (IBAMA)", show=True).add_to(m)

    for _, row in df_map.iterrows():
        uf = row['UF']
        is_fed = row['is_federal']

        # Popup content formatted nicely with HTML/CSS
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
            # Special federal star icon in Brasilia for IBAMA
            folium.Marker(
                location=[row['lat'], row['lon']],
                popup=popup,
                tooltip=f"🏢 IBAMA: {row['TOTAL_LICENCAS']:,.0f} Licenças Federais ({ano_sel})",
                icon=folium.Icon(color='red', icon='certificate', prefix='glyphicon')
            ).add_to(marker_group_ibama)
        else:
            # Circle marker sized by licensing or deforestation
            radius = 6 + (row['TOTAL_LICENCAS'] ** 0.3)
            folium.CircleMarker(
                location=[row['lat'], row['lon']],
                radius=min(radius, 22),
                popup=popup,
                tooltip=f"<b>{uf} - {row['Nome']}</b><br>Licenças: {row['TOTAL_LICENCAS']:,.0f} | Desm: {row['DESMATAMENTO_HA']:,.0f} ha",
                color='#1E3A8A',
                fill=True,
                fill_color='#3B82F6',
                fill_opacity=0.8,
                weight=1.5
            ).add_to(marker_group_states)

    # Layer control toggle
    folium.LayerControl(collapsed=False).add_to(m)

    # 4. Render map in Streamlit via HTML component
    map_html = m._repr_html_()
    st.components.v1.html(map_html, height=620, scrolling=False)

    # 5. Explanatory & Data Table Tabs below map
    tab_dados, tab_ibama, tab_guia = st.tabs([
        "📋 Tabela de Dados Espaciais Selecionados",
        "🏢 Destaque: Licenciamento Federal IBAMA",
        "💡 Como Usar os Controles do Mapa"
    ])

    with tab_dados:
        st.dataframe(
            df_map[['UF', 'Nome', 'TOTAL_LICENCAS', 'INFRA_CONSTR', 'INFRA_OP', 'RURAL_VEG', 'DESMATAMENTO_HA', 'DESMATAMENTO_KM2']].rename(columns={
                'Nome': 'Estado / Entidade',
                'TOTAL_LICENCAS': 'Total Licenças',
                'INFRA_CONSTR': 'Obras (LP/LI)',
                'INFRA_OP': 'Operação (LO)',
                'RURAL_VEG': 'Rural/Supressão',
                'DESMATAMENTO_HA': 'Desmatamento (ha)',
                'DESMATAMENTO_KM2': 'Desmatamento (km²)'
            }).style.format({
                'Total Licenças': '{:,.0f}',
                'Obras (LP/LI)': '{:,.0f}',
                'Operação (LO)': '{:,.0f}',
                'Rural/Supressão': '{:,.0f}',
                'Desmatamento (ha)': '{:,.0f}',
                'Desmatamento (km²)': '{:,.1f}'
            }),
            use_container_width=True
        )

    with tab_ibama:
        st.markdown(f"""
        ### Atuação do IBAMA no Licenciamento Ambiental Nacional ({ano_sel})
        - **Competência Constitucional:** O IBAMA licencia empreendimentos de significativo impacto ambiental de âmbito nacional ou regional (que ultrapassam os limites territoriais de um estado ou localizados no mar territorial, terras indígenas ou fronteiras).
        - **Volume no Ano ({ano_sel}):** **{ibama_count:,.0f} processos/atos** deferidos no nível federal.
        - **Localização Simbólica no Mapa:** Como o IBAMA possui competência sobre toda a malha territorial brasileira, ele está georreferenciado com um **marcador vermelho de destaque** na sede nacional em Brasília/DF.
        """)

    with tab_guia:
        st.markdown("""
        ### Dicas de Interação:
        1. **Alternância de Camadas (Canto Superior Direito do Mapa):** Você pode ativar ou desativar os marcadores estaduais, o ícone do IBAMA ou alternar entre visualização de mapa padrão e imagem de **Satélite**.
        2. **Cliques nos Estados:** Clique em qualquer círculo azul ou no ícone do IBAMA para abrir o balão informativo (*Popup*) com o detalhamento por tipologia de licença e perda de cobertura vegetal.
        3. **Filtro de Estados:** No menu superior, adicione ou remova qualquer UF da análise em tempo real.
        """)
