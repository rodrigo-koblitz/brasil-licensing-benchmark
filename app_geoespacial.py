import os
import streamlit as st
from map_module import render_map_module

st.set_page_config(
    page_title="Módulo Geoespacial & GIS: Desmatamento e Licenciamento Brasil",
    page_icon="🗺️",
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

# SIDEBAR GEOESPACIAL
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)
st.sidebar.title("Módulo Geoespacial & GIS")
st.sidebar.markdown("""
**Camadas Ativas:**
- 🛰️ MapBiomas (Desmatamento)
- 📍 Empreendimentos Licenciados
- ⭕ Buffers de Impacto (km)
""")

# Renderizar Mapa Completo
render_map_module(DATA_DIR)
