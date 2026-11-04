import os
import base64
import glob
import streamlit as st

st.set_page_config(
    page_title="Relatórios e Análises por Estado (PDF)",
    page_icon="📄",
    layout="wide"
)

st.markdown("""
<style>
    .page-title { font-size: 2.2rem; font-weight: 700; color: #1E3A8A; margin-bottom: 0.5rem; }
    .page-sub { font-size: 1.05rem; color: #4B5563; margin-bottom: 1.5rem; }
    .pdf-card { background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 1.2rem; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="page-title">📄 Relatórios Estaduais de Licenciamento & Impacto</div>', unsafe_allow_html=True)
st.markdown('<div class="page-sub">Consulte, leia online e baixe os relatórios completos compilados para cada Estado brasileiro e IBAMA.</div>', unsafe_allow_html=True)

# Locate PDFs
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pdf_dir = os.path.join(base_dir, "reports_pdf")

pdf_files = sorted(glob.glob(os.path.join(pdf_dir, "*_analysis.pdf")))

if not pdf_files:
    st.warning("Nenhum relatório PDF encontrado na pasta.")
    st.stop()

# Build mapping
state_names = {
    "AC": "Acre", "AL": "Alagoas", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "IBAMA": "Âmbito Federal (IBAMA)",
    "MA": "Maranhão", "MG": "Minas Gerais", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "PA": "Pará", "PB": "Paraíba", "PE": "Pernambuco", "PI": "Piauí", "PR": "Paraná",
    "RJ": "Rio de Janeiro", "RO": "Rondônia", "RR": "Roraima", "RS": "Rio Grande do Sul",
    "SC": "Santa Catarina", "SE": "Sergipe", "SP": "São Paulo"
}

file_dict = {}
for p in pdf_files:
    base = os.path.basename(p)
    code = base.replace("_analysis.pdf", "")
    label = f"{code} - {state_names.get(code, code)}"
    file_dict[label] = (code, p)

# Sidebar / Top selector
col_sel, col_info = st.columns([2, 1])

with col_sel:
    selected_label = st.selectbox(
        "Selecione o Estado ou Órgão para Visualizar o Relatório:",
        options=list(file_dict.keys()),
        index=0
    )

selected_code, selected_path = file_dict[selected_label]
file_size_kb = os.path.getsize(selected_path) / 1024

with col_info:
    st.write(f"**Tamanho:** {file_size_kb:,.1f} KB")
    with open(selected_path, "rb") as f:
        pdf_bytes = f.read()
    st.download_button(
        label=f"📥 Baixar Relatório {selected_code} (PDF)",
        data=pdf_bytes,
        file_name=f"{selected_code}_analysis.pdf",
        mime="application/pdf"
    )

st.markdown("---")

# Render embedded PDF viewer
base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="900" type="application/pdf" style="border: 1px solid #CBD5E1; border-radius: 8px;"></iframe>'

st.markdown(pdf_display, unsafe_allow_html=True)
