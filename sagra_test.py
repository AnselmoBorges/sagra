import streamlit as st
import yaml
from yaml.loader import SafeLoader
import streamlit_authenticator as stauth

# Configuração da página
st.set_page_config(
    page_title="SAGRA - Teste de Autenticação",
    page_icon="🏉",
    layout="wide"
)

# Título
st.title("SAGRA - Teste de Autenticação")

# Autenticação manual
credentials = {
    "usernames": {
        "admin": {
            "name": "Administrador",
            "password": "$2b$12$qOMhXS8nxqHWOvhQpkWxCuqwQqPgfWm6VVKZPJDcg3DfNqT6Ry3Uy"  # admin123
        }
    }
}

cookie = {
    "name": "sagra_cookie",
    "key": "sagra_cookie_key",
    "expiry_days": 30
}

# Cria o autenticador diretamente com valores literais
authenticator = stauth.Authenticate(
    credentials,
    cookie['name'],
    cookie['key'],
    cookie['expiry_days']
)

# Inicializa o status de autenticação
try:
    name, authentication_status, username = authenticator.login('Login')
except Exception as e:
    st.error(f"Erro na autenticação: {str(e)}")
    st.stop()

# Verifica o status da autenticação
if authentication_status == False:
    st.error('❌ Usuário ou senha incorretos')
    st.stop()
elif authentication_status == None:
    st.info('👋 Por favor, faça login para continuar')
    st.stop()

# Conteúdo principal se autenticado
st.success(f"Bem-vindo, {name}!")
authenticator.logout('Logout', 'main') 