import streamlit as st
import pandas as pd
import os

# Importação da função de coleta
try:
    from aws_controller import get_aws_inventory
except ImportError:
    def get_aws_inventory(): 
        st.error("Arquivo aws_controller.py não encontrado no repositório.")

st.set_page_config(page_title="Cloud Governance & FinOps", layout="wide")

# --- 1. MODAIS ---
@st.dialog("🗑️ Volumes EBS Órfãos")
def modal_volumes(df):
    st.write("Volumes sem instância associada (Gasto Ocioso):")
    st.dataframe(df, use_container_width=True, hide_index=True)

@st.dialog("🌐 Elastic IPs Soltos")
def modal_ips(df):
    st.write("IPs reservados mas não utilizados (Taxa Ativa):")
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- 2. CARGA DE DADOS COM GARANTIA DE COLUNAS ---
def load_data():
    cols_i = ["Conta", "Name", "Instance ID", "Tipo", "IP Privado", "SO", "Disco (GB)", "Status", "Backup", "Lançamento"]
    cols_v = ["Volume ID", "Tamanho (GB)", "Tipo", "Criação", "Região"]
    cols_p = ["IP Público", "Região"]

    def read_safe(file, columns):
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                for col in columns:
                    if col not in df.columns:
                        df[col] = "N/A"
                return df[columns]
            except:
                return pd.DataFrame(columns=columns)
        return pd.DataFrame(columns=columns)

    return read_safe('inventory_data.csv', cols_i), \
           read_safe('orphaned_volumes.csv', cols_v), \
           read_safe('unassociated_ips.csv', cols_p)

df_raw, df_orph, df_ips = load_data()

# --- 3. CSS REFINADO (ALVOS ESPECÍFICOS) ---
st.markdown("""
<style>
    /* 1. Estilo dos Cards Cinzas (Métricas) */
    div[data-testid="stMetric"] {
        background-color: #1E2329;
        border: 1px solid #323A43;
        padding: 15px !important;
        border-radius: 12px;
        height: 140px;
    }

    /* 2. Botões dentro dos Cards (Links "Ver lista") */
    div[data-testid="column"] .stButton button {
        background-color: transparent !important;
        color: #FF9900 !important;
        border: none !important;
        text-decoration: underline;
        font-size: 13px !important;
        font-weight: normal !important;
        margin-top: -50px !important; 
        width: 100% !important;
        display: block !important;
        text-align: center !important;
        padding: 0 !important;
        height: auto !important;
    }

    div[data-testid="column"] .stButton button:hover {
        color: #FFA500 !important;
        text-decoration: none !important;
        background-color: transparent !important;
    }

    /* 3. Botão da Barra Lateral (Visual de Botão Real) */
    section[data-testid="stSidebar"] .stButton button {
        background-color: #FF9900 !important;
        color: #000000 !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        width: 100% !important;
        height: 45px !important;
        margin-top: 10px !important;
        border: none !important;
        text-decoration: none !important;
        display: inline-block !important;
    }

    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #e68a00 !important;
        border: none !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Cloud Governance & FinOps")

# --- 4. SIDEBAR (BOTÃO DE SYNC E FILTROS) ---
with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🔄 Sincronizar AWS Agora"):
        with st.spinner("Conectando na API da AWS..."):
            get_aws_inventory()
            st.success("Sincronizado!")
            st.rerun()
    
    st.divider()
    st.header("Filtros")
    opcoes = ["Todos", "Windows", "Linux", "Ligado", "Desligado", "Sem Backup"]
    filtro_selecionado = st.radio("Categoria:", opcoes)

# --- 5. GRID DE CARDS ---
c = st.columns(8)
with c[0]: st.metric("Total", len(df_raw))
with c[1]: st.metric("Windows", len(df_raw[df_raw['SO'] == 'Windows']))
with c[2]: st.metric("Linux", len(df_raw[df_raw['SO'] == 'Linux']))
with c[3]: st.metric("Ligados", len(df_raw[df_raw['Status'] == 'Ligado']))
with c[4]: st.metric("Desligados", len(df_raw[df_raw['Status'] == 'Desligado']))
with c[5]: st.metric("Sem Backup", len(df_raw[df_raw['Backup'] == 'Não']))

# Links centralizados nos cards de FinOps
with c[6]: 
    st.metric("Volumes Órfãos", len(df_orph))
    if st.button("Ver lista", key="btn_orph"): modal_volumes(df_orph)
with c[7]: 
    st.metric("IPs Soltos", len(df_ips))
    if st.button("Ver lista", key="btn_ips"): modal_ips(df_ips)

st.markdown("---")

# --- 6. TABELA ---
df_disp = df_raw.copy()
if filtro_selecionado != "Todos":
    if filtro_selecionado in ["Windows", "Linux"]: df_disp = df_disp[df_disp['SO'] == filtro_selecionado]
    elif filtro_selecionado in ["Ligado", "Desligado"]: df_disp = df_disp[df_disp['Status'] == filtro_selecionado]
    elif filtro_selecionado == "Sem Backup": df_disp = df_disp[df_disp['Backup'] == "Não"]

st.subheader(f"📋 Listagem: {filtro_selecionado}")
st.dataframe(df_disp, use_container_width=True, hide_index=True)