import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Cloud Governance & FinOps", layout="wide")

# --- 1. MODAIS (Pop-ups) ---
@st.dialog("🗑️ Volumes EBS Órfãos")
def modal_volumes(df):
    st.write("Volumes sem instância associada (Gasto Ocioso):")
    st.dataframe(df, use_container_width=True, hide_index=True)

@st.dialog("🌐 Elastic IPs Soltos")
def modal_ips(df):
    st.write("IPs reservados mas não utilizados (Taxa Ativa):")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 2. CARGA DE DADOS ---
def load_data():
    def read_safe(file, cols):
        try: return pd.read_csv(file)
        except: return pd.DataFrame(columns=cols)
    return read_safe('inventory_data.csv', ["Name", "SO", "Status"]), \
           read_safe('orphaned_volumes.csv', ["Volume ID", "Tamanho (GB)"]), \
           read_safe('unassociated_ips.csv', ["IP Público", "Região"])

df_raw, df_orph, df_ips = load_data()

# --- 3. CSS PARA CENTRALIZAÇÃO TOTAL DO LINK ---
st.markdown("""
<style>
    /* Estilo do Card */
    div[data-testid="stMetric"] {
        background-color: #1E2329;
        border: 1px solid #323A43;
        padding: 15px !important;
        border-radius: 12px;
        height: 140px;
    }

    /* Estilização do Link "Ver lista" Centralizado */
    .stButton button {
        background-color: transparent !important;
        color: #FF9900 !important;
        border: none !important;
        text-decoration: underline;
        font-size: 13px !important;
        font-weight: normal !important;
        
        /* O segredo da centralização */
        margin-top: -50px !important; 
        width: 100% !important;
        display: block !important;
        text-align: center !important;
        
        padding: 5px !important;
        height: 0 !important;
    }
    
    .stButton button:hover {
        color: #FFA500 !important;
        background-color: transparent !important;
        text-decoration: none;
    }
    
    .stButton button:focus {
        box-shadow: none !important;
        background-color: transparent !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Cloud Governance & FinOps")

# --- 4. SIDEBAR PARA FILTROS ---
with st.sidebar:
    st.header("Filtros de Inventário")
    opcoes = ["Todos", "Windows", "Linux", "Ligado", "Desligado", "Sem Backup"]
    filtro_selecionado = st.radio("Selecione uma categoria:", opcoes)

# --- 5. GRID DE CARDS ---
c = st.columns(8)

with c[0]: st.metric("Total", len(df_raw))
with c[1]: st.metric("Windows", len(df_raw[df_raw['SO'] == 'Windows']))
with c[2]: st.metric("Linux", len(df_raw[df_raw['SO'] == 'Linux']))
with c[3]: st.metric("Ligados", len(df_raw[df_raw['Status'] == 'Ligado']))
with c[4]: st.metric("Desligados", len(df_raw[df_raw['Status'] == 'Desligado']))
with c[5]: st.metric("Sem Backup", len(df_raw[df_raw['Backup'] == 'Não']))

# Cards com Link Centralizado
with c[6]: 
    st.metric("Volumes Órfãos", len(df_orph))
    if st.button("Ver lista", key="btn_orph"):
        modal_volumes(df_orph)

with c[7]: 
    st.metric("IPs Soltos", len(df_ips))
    if st.button("Ver lista", key="btn_ips"):
        modal_ips(df_ips)

st.markdown("---")

# --- 6. TABELA PRINCIPAL ---
df_disp = df_raw.copy()
if filtro_selecionado != "Todos":
    if filtro_selecionado in ["Windows", "Linux"]: df_disp = df_disp[df_disp['SO'] == filtro_selecionado]
    elif filtro_selecionado in ["Ligado", "Desligado"]: df_disp = df_disp[df_disp['Status'] == filtro_selecionado]
    elif filtro_selecionado == "Sem Backup": df_disp = df_disp[df_disp['Backup'] == "Não"]

st.subheader(f"📋 Listagem: {filtro_selecionado}")
st.dataframe(df_disp, use_container_width=True, hide_index=True)