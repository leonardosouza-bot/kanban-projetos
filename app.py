import streamlit as st
import psycopg2
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# =========================
# CONFIG
# =========================

st.set_page_config(page_title="Kanban Projetos", layout="wide")
st.title("Kanban Projetos")

# =========================
# CONSTANTES
# =========================

DIAGRAMADORES = [
    "Alessandro","Alisson","Antony","Claudenio","Danielly",
    "Francisco","Jonysson","Juliano","Leandro","Marianna",
    "Mayck","Nayara","Taina","Thais","Thatiane","Alex",
    "Ismaela","Rafael","Antonio","Cesar","Fernanda","Marcos","Mauricio"
]

PROJETOS = [
    "Nucleo 1 - Basis",
    "Nucleo 2 - Mundus E/N",
    "Nucleo 3 - Mundus H/L",
    "Nucleo 6 - Ludus"
]

DISCIPLINAS = [
    "Matematica",
    "Portugues",
    "Historia",
    "DisciplinaTESTE",
    "Geografia",
    "Ciencias",
    "Ingles"
]

ANOS = [
    "1 Ano",
    "2 Ano",
    "3 Ano"
]

MODULOS = [
    "Modulo 1",
    "Modulo 2",
    "Modulo 3",
    "Modulo 4"
]

# =========================
# DATABASE
# =========================

def get_connection():
    return psycopg2.connect(
        host="dpg-d76ld9fpm1nc7398k9a0-a.virginia-postgres.render.com",
        database="kanbandiagramacao",
        user="kanban_user",
        password="RwOTyHs72w8u5rm81QJOVUn29uuZkIDA",
        port=5432
    )

def criar_tabela():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS atividades (
        id SERIAL PRIMARY KEY,
        projeto TEXT,
        diagramador TEXT,
        disciplina TEXT,
        ano TEXT,
        modulo TEXT,
        atividade TEXT,
        inicio TIMESTAMP,
        fim TIMESTAMP,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

# =========================
# SERVICES
# =========================

def inserir_atividade(dados):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO atividades
    (projeto, diagramador, disciplina, ano, modulo, atividade, inicio, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, dados)
    
    conn.commit()
    conn.close()


def listar_atividades(limit=30):
    conn = get_connection()

    query = f"""
    SELECT * FROM atividades
    ORDER BY id DESC
    LIMIT {limit}
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

    return df


def finalizar_atividade(atividade_id, fim):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE atividades
    SET fim = %s, status = 'FINALIZADO'
    WHERE id = %s
    """, (fim, atividade_id))

    conn.commit()
    conn.close()

# =========================
# UTILS
# =========================

def formatar_data(data, hora):
    return f"{data.strftime('%Y-%m-%d')} {hora.strftime('%H:%M:%S')}"


def calcular_tempo(inicio):
    try:
        inicio_dt = datetime.strptime(inicio, "%Y-%m-%d %H:%M:%S")
        diff = datetime.now() - inicio_dt

        horas = diff.seconds // 3600
        minutos = (diff.seconds % 3600) // 60

        return f"{horas}h {minutos}min"
    except Exception:
        return ""

# =========================
# INIT
# =========================

criar_tabela()

# =========================
# FORMULÁRIO
# =========================

st.subheader("Nova atividade")

col1, col2, col3 = st.columns(3)

with col1:
    projeto = st.selectbox("Projeto", ["Selecione..."] + PROJETOS)

with col2:
    diagramador = st.selectbox("Diagramador", ["Selecione..."] + DIAGRAMADORES)

with col3:
    atividade = st.text_input("Atividade")
    
col4, col5, col6 = st.columns(3)

with col4:
    disciplina = st.selectbox("Disciplina", ["Selecione..."] + DISCIPLINAS)

with col5:
    ano = st.selectbox("Ano", ["Selecione..."] + ANOS)

with col6:
    modulo = st.selectbox("Módulo", ["Selecione..."] + MODULOS)

col4, col5 = st.columns(2)

with col4:
    data_inicio = st.date_input("Data início")

with col5:
    hora_inicio = st.time_input("Hora início")

inicio = formatar_data(data_inicio, hora_inicio)

finalizar = st.checkbox("Finalizar agora?")

if finalizar:
    data_fim = st.date_input("Data fim")
    hora_fim = st.time_input("Hora fim")
    fim = formatar_data(data_fim, hora_fim)
else:
    fim = ""

if st.button("Salvar atividade"):
    inserir_atividade((
        projeto,
        diagramador,
        disciplina,
        ano,
        modulo,
        atividade,
        datetime.now(),
        "EM PROCESSO"
    ))
    st.success("Atividade salva com sucesso!")

# =========================
# LISTA
# =========================

st.subheader("Atividades da equipe")

df = listar_atividades()

if not df.empty:

    df["tempo"] = df.apply(
        lambda row: calcular_tempo(row["inicio"]) if row["status"] == "EM PROCESSO" else "",
        axis=1
    )

    # FILTRO
    st.subheader("Filtros")

    filtro_projeto = st.selectbox(
        "Filtrar por projeto",
        ["Todos"] + list(df["projeto"].dropna().unique())
    )

    if filtro_projeto != "Todos":
        df = df[df["projeto"] == filtro_projeto]

    st.dataframe(df)

# =========================
# FINALIZAR
# =========================

st.subheader("Finalizar atividade")

if not df.empty:
    abertas = df[df["status"] == "EM PROCESSO"]

    if not abertas.empty:
        atividade_id = st.selectbox("Selecionar ID", abertas["id"])

        if st.button("Finalizar selecionada"):
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            finalizar_atividade(atividade_id, agora)
            st.success("Finalizada com sucesso!")
            st.rerun()
    else:
        st.info("Nenhuma atividade em andamento")

# =========================
# MÉTRICAS
# =========================

if not df.empty:
    st.subheader("Resumo")

    st.write("Em processo:", len(df[df["status"] == "EM PROCESSO"]))
    st.write("Finalizadas:", len(df[df["status"] == "FINALIZADO"]))
    st.write("Na fila:", len(df[df["status"] == "FILA"]))

# =========================
# GRÁFICO
# =========================

if not df.empty:
    st.subheader("Atividades por diagramador")
    st.bar_chart(df["diagramador"].value_counts())

# =========================
# STATUS EQUIPE
# =========================

if not df.empty:
    st.subheader("Status da equipe")

    ocupados = []
    disponiveis = []

    for nome in DIAGRAMADORES:
        tarefas = df[
            (df["diagramador"] == nome) &
            (df["status"] == "EM PROCESSO")
        ]

        if len(tarefas) > 0:
            ocupados.append(nome)
        else:
            disponiveis.append(nome)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔵 Ocupados")
        for nome in ocupados:
            st.error(f"{nome}")

    with col2:
        st.markdown("### 🟢 Disponíveis")
        for nome in disponiveis:
            st.success(f"{nome}")