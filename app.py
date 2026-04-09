import streamlit as st
import pandas as pd
import os
# Importamos sua função de coleta (certifique-se que o nome do arquivo/função coincide)
try:
    from aws_controller import get_aws_inventory
except ImportError:
    # Caso o arquivo ainda não esteja lá ou tenha outro nome
    def get_aws_inventory(): 
        st.error("Função de coleta não encontrada no aws_controller.py")

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

# --- 2. CARGA DE DADOS COM TRATAMENTO DE ERRO (KEYERROR) ---
def load_data():
    # Definição rigorosa das colunas para evitar o erro de 'Backup'
    cols_i = ["Conta", "Name", "Instance ID", "Tipo", "IP Privado", "SO", "Disco (GB)", "Status", "Backup", "Lançamento"]
    cols_v = ["Volume ID", "Tamanho (GB)", "Tipo", "Criação", "Região"]
    cols_p = ["IP Público", "Região"]

    def read_safe(file, columns):
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                # Garante que mesmo que o CSV venha incompleto, as colunas existam
                for col in columns:
                    if col not in df.columns:
                        df[col] = "N/A"
                return df[columns] # Retorna apenas as colunas desejadas na ordem certa
            except:
                return pd.DataFrame(columns=columns)
        return pd.DataFrame(columns=columns)

    return read_safe('inventory_data.csv', cols_i), \
           read_safe('orphaned_volumes.csv', cols_v), \
           read_safe('unassociated_ips.csv', cols_p)

df_raw, df_orph, df_ips = load_data()

# --- 3. CSS (DESIGN MINIMALISTA) ---
st.markdown("""
<style>
    div[data-testid="stMetric"] {
        background-color: #1E2329;
        border: 1px solid #323A43;
        padding: 15px !important;
        border-radius: 12px;
        height: 140px;
    }
    .stButton button {
        background-color: transparent !important;
        color: #FF9900 !important;
        border: none !important;
        text-decoration: underline;
        font-size: 13px !important;
        margin-top: -50px !important; 
        width: 100% !important;
        display: block !important;
        text-align: center !important;
        padding: 0 !important;
    }
    .stButton button:hover { color: #FFA500 !important; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

st.title("🌐 Cloud Governance & FinOps")

# --- 4. SIDEBAR COM BOTÃO DE ATUALIZAÇÃO (O "CLI" NO BROWSER) ---
with st.sidebar:
    st.header("⚙️ Controle")
    if st.button("🔄 Sincronizar AWS Agora"):
        with st.spinner("Conectando na API da AWS..."):
            get_aws_inventory() # Chama o seu script Boto3
            st.success("Inventário Atualizado!")
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

# Card de Backup corrigido (evita o erro se a tabela for vazia)
valor_backup = len(df_raw[df_raw['Backup'] == 'Não']) if 'Backup' in df_raw.columns else 0
with c[5]: st.metric("Sem Backup", valor_backup)

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