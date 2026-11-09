import os

app_path = r'G:\Meu Drive\UFMG\auxiliary\app\app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add import
if 'from agro_module import render_agro_module' not in content:
    content = content.replace(
        'from map_module import render_map_module',
        'from map_module import render_map_module\nfrom agro_module import render_agro_module'
    )

# 2. Add radio option
target_radio = '        "📊 Benchmark Financeiro & BNDES",\n        "🗺️ Mapa Geoespacial: Desmatamento & Licenças"'
replacement_radio = '        "📊 Benchmark Financeiro & BNDES",\n        "🌾 Financiamento & Seguro Agropecuário",\n        "🗺️ Mapa Geoespacial: Desmatamento & Licenças"'
if '🌾 Financiamento & Seguro Agropecuário' not in content:
    content = content.replace(target_radio, replacement_radio)

# 3. Add module dispatch
target_dispatch = 'elif modulo == "🗺️ Mapa Geoespacial: Desmatamento & Licenças":\n    render_map_module(DATA_DIR)'
replacement_dispatch = '''elif modulo == "🌾 Financiamento & Seguro Agropecuário":
    render_agro_module()

elif modulo == "🗺️ Mapa Geoespacial: Desmatamento & Licenças":
    render_map_module(DATA_DIR)'''

if 'render_agro_module()' not in content:
    content = content.replace(target_dispatch, replacement_dispatch)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("app.py successfully updated with Agro module!")
