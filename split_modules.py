import sys
import io
import os

app_dir = r"G:\Meu Drive\UFMG\auxiliary\app"
with open(os.path.join(app_dir, "app.py"), "r", encoding="utf-8") as f:
    lines = f.readlines()

header = lines[:32]
state_dict = lines[49:58]

# 1. app_ambiental.py (Módulo 1, 2 e 3 + Agente IA Ambiental)
lines_amb = []
lines_amb.extend(header)
lines_amb.append("\n# SIDEBAR AMBIENTAL\n")
lines_amb.append('st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)\n')
lines_amb.append('st.sidebar.title("Módulo Ambiental e IA")\n')
lines_amb.append('modulo = st.sidebar.radio("Selecione a Análise:", ["🌱 Licenciamento Ambiental Brasil", "🌳 Desmatamento (MapBiomas)", "⚖️ Modelagem: Desmatamento X Licenciamento"])\n')
lines_amb.extend(state_dict)
lines_amb.extend(lines[61:576])

with open(os.path.join(app_dir, "app_ambiental.py"), "w", encoding="utf-8") as f:
    f.writelines(lines_amb)
print("Wrote app_ambiental.py:", len(lines_amb))

# 2. app_financeiro.py (Módulo 4: Benchmark Financeiro & BNDES + IA Financeira)
lines_fin = []
lines_fin.extend(header)
lines_fin.append("\n# SIDEBAR FINANCEIRO\n")
lines_fin.append('st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)\n')
lines_fin.append('st.sidebar.title("Módulo Financeiro e BNDES")\n')
lines_fin.extend(state_dict)
fin_body = list(lines[577:748])
fin_body[0] = "if True:\n"
lines_fin.extend(fin_body)

with open(os.path.join(app_dir, "app_financeiro.py"), "w", encoding="utf-8") as f:
    f.writelines(lines_fin)
print("Wrote app_financeiro.py:", len(lines_fin))

# 3. app_geoespacial.py (Módulo 5: Mapas e GIS)
lines_geo = []
lines_geo.extend(header)
lines_geo.append("\n# SIDEBAR GEOESPACIAL\n")
lines_geo.append('st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/thumb/0/05/Flag_of_Brazil.svg/200px-Flag_of_Brazil.svg.png", width=80)\n')
lines_geo.append('st.sidebar.title("Módulo Geoespacial e GIS")\n')
lines_geo.extend(state_dict)
geo_body = list(lines[749:])
geo_body[0] = "if True:\n"
lines_geo.extend(geo_body)

with open(os.path.join(app_dir, "app_geoespacial.py"), "w", encoding="utf-8") as f:
    f.writelines(lines_geo)
print("Wrote app_geoespacial.py:", len(lines_geo))
