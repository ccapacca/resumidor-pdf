import streamlit as st
from openai import OpenAI
import PyPDF2
import io

st.set_page_config(
    page_title="Resumidor de PDFs",
    page_icon="📄",  # El icono de la pestaña lo dejamos como identificativo, pero en la UI no usamos emojis
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── ESTILO CORPORATIVO ─────────────────────────────────────────────────────
st.markdown("""
<style>
/* Tipografía profesional */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    background: #F7F9FC !important;
    color: #1E293B !important;
}

/* Ocultar elementos por defecto */
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
section[data-testid="stSidebarContent"] { padding: 0 !important; }

/* Área principal */
[data-testid="stMain"] {
    background: #F7F9FC !important;
}
.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* Upload area */
[data-testid="stFileUploader"] {
    background: #FFFFFF !important;
    border: 1px dashed #CBD5E1 !important;
    border-radius: 12px !important;
    padding: 32px !important;
    text-align: center !important;
    transition: all 0.2s ease !important;
    margin-bottom: 24px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #2563EB !important;
    background: #F8FAFC !important;
}

/* Botones */
.stButton > button {
    background-color: #0F1F3D !important;
    border: 1px solid #0F1F3D !important;
    color: #FFFFFF !important;
    border-radius: 8px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    padding: 12px 24px !important;
    width: auto !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 1px 2px rgba(15, 31, 61, 0.05) !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
}
.stButton > button:hover {
    background-color: #132C4A !important;
    border-color: #132C4A !important;
    box-shadow: 0 4px 12px rgba(15, 31, 61, 0.15) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
}

/* Botón de descarga */
.stDownloadButton > button {
    background-color: transparent !important;
    border: 1px solid #CBD5E1 !important;
    color: #334155 !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}
.stDownloadButton > button:hover {
    background-color: #F1F5F9 !important;
    border-color: #94A3B8 !important;
    color: #0F1F3D !important;
}

/* Métricas */
[data-testid="stMetric"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 16px !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
    font-size: 24px !important;
    font-weight: 600 !important;
    color: #0F1F3D !important;
}
[data-testid="stMetricLabel"] {
    font-size: 11px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    margin-top: 4px !important;
}

/* Caja de resumen */
.resumen-box {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 28px 32px;
    font-size: 15px;
    line-height: 1.8;
    color: #334155;
    margin-top: 20px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.03);
}

/* Selects */
[data-testid="stSelectbox"] {
    background: #FFFFFF !important;
    border: 1px solid #CBD5E1 !important;
    border-radius: 8px !important;
}
[data-testid="stSelectbox"] > div {
    font-family: 'Inter', sans-serif !important;
}

/* Indicador de estado en top bar */
.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: #22C55E;
    margin-right: 6px;
}

/* Eliminar animaciones molestas */
@keyframes none { }
</style>
""", unsafe_allow_html=True)

# ── Cliente Groq ──────────────────────────────────────────────────────────
client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# ── Funciones auxiliares ──────────────────────────────────────────────────
def extraer_texto_pdf(archivo):
    lector = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
    texto_completo = ""
    for pagina in lector.pages:
        texto_completo += pagina.extract_text() + "\n"
    return texto_completo, len(lector.pages)

def resumir_texto(texto, tipo_resumen, idioma):
    instrucciones = {
        "Resumen ejecutivo": "Haz un resumen ejecutivo conciso en 5-7 puntos clave con bullets.",
        "Resumen detallado": "Haz un resumen detallado manteniendo todos los puntos importantes.",
        "Resumen simple": "Explica el contenido como si se lo explicaras a alguien sin conocimiento del tema.",
        "Puntos clave": "Extrae solo los puntos más importantes en formato de lista numerada."
    }

    prompt = f"""Analiza el siguiente texto y {instrucciones[tipo_resumen]}
    
Responde en {idioma}.

TEXTO A RESUMIR:
{texto[:8000]}

IMPORTANTE: Si el texto está cortado, indica que el documento es más largo y resume lo que tienes."""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "Eres un experto en análisis y síntesis de documentos. Produces resúmenes claros, precisos y bien estructurados."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.3
    )
    return response.choices[0].message.content

# ── Estado inicial ────────────────────────────────────────────────────────
if "resumen" not in st.session_state:
    st.session_state.resumen = None
if "nombre_archivo" not in st.session_state:
    st.session_state.nombre_archivo = None
if "num_paginas" not in st.session_state:
    st.session_state.num_paginas = 0
if "num_palabras" not in st.session_state:
    st.session_state.num_palabras = 0

# ── SIDEBAR ───────────────────────────────────────────────────────────────
with st.sidebar:
    # Cabecera del sidebar (marca)
    st.markdown("""
    <div style="padding:24px 20px 20px; border-bottom:1px solid #E2E8F0;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
            <div style="width:36px;height:36px;border-radius:8px;
                background:#0F1F3D;
                display:flex;align-items:center;justify-content:center;
                font-size:16px;color:#FFFFFF;font-weight:600;">R</div>
            <div>
                <div style="font-size:15px;font-weight:600;color:#0F1F3D;letter-spacing:-0.01em;">Resumidor</div>
                <div style="font-size:11px;color:#64748B;font-weight:500;">Procesamiento de documentos</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div style="padding:16px 20px 0;">', unsafe_allow_html=True)

    # Métricas del documento
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Páginas", st.session_state.num_paginas)
    with col2:
        st.metric("Palabras", st.session_state.num_palabras)

    # Opciones de resumen
    st.markdown("""
    <div style="margin-top:20px;margin-bottom:8px;font-size:11px;font-weight:600;
        color:#475569;text-transform:uppercase;letter-spacing:0.06em;">
        Tipo de resumen
    </div>
    """, unsafe_allow_html=True)
    tipo_resumen = st.selectbox(
        "",
        ["Resumen ejecutivo", "Resumen detallado", "Resumen simple", "Puntos clave"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div style="margin-top:16px;margin-bottom:8px;font-size:11px;font-weight:600;
        color:#475569;text-transform:uppercase;letter-spacing:0.06em;">
        Idioma de respuesta
    </div>
    """, unsafe_allow_html=True)
    idioma = st.selectbox(
        "",
        ["Español", "English", "Português"],
        label_visibility="collapsed"
    )

    # Tarjeta de modelo
    st.markdown("""
    <div style="margin-top:20px;background:#F8FAFC;border:1px solid #E2E8F0;
        border-radius:8px;padding:14px 16px;display:flex;align-items:center;gap:12px;">
        <div style="width:8px;height:8px;border-radius:50%;background:#22C55E;"></div>
        <div>
            <div style="font-size:13px;font-weight:600;color:#0F1F3D;">Llama 3.3 · 70B</div>
            <div style="font-size:12px;color:#64748B;margin-top:2px;">Groq · Alta velocidad</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Pie del sidebar
    st.markdown("""
    <div style="padding:14px 20px;display:flex;justify-content:space-between;
        align-items:center;margin-top:auto;border-top:1px solid #E2E8F0;">
        <span style="font-size:11px;color:#94A3B8;">Grimaldo Ccapacca</span>
        <span style="font-size:10px;font-weight:600;background:#EFF6FF;color:#2563EB;
            border-radius:4px;padding:2px 8px;letter-spacing:0.05em;">v2.0</span>
    </div>
    """, unsafe_allow_html=True)

# ── ÁREA PRINCIPAL ────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
    padding:20px 32px;border-bottom:1px solid #E2E8F0;background:#FFFFFF;">
    <div style="display:flex;align-items:center;gap:14px;">
        <div style="width:36px;height:36px;border-radius:8px;
            background:#0F1F3D;
            display:flex;align-items:center;justify-content:center;
            color:#FFFFFF;font-weight:600;font-size:18px;">R</div>
        <div>
            <div style="font-size:16px;font-weight:600;color:#0F1F3D;">
                Resumidor de PDFs
            </div>
            <div style="font-size:13px;color:#64748B;margin-top:2px;">
                Sube cualquier documento y obtén un análisis inmediato
            </div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:8px;border:1px solid #E2E8F0;
        border-radius:20px;padding:6px 16px;font-size:13px;color:#475569;background:#FFFFFF;">
        <span class="status-dot"></span>
        Sistema listo
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="padding:28px 32px;">', unsafe_allow_html=True)

# ── ZONA DE CARGA ─────────────────────────────────────────────────────────
archivo_pdf = st.file_uploader(
    "Arrastra tu archivo PDF o haz clic para examinar",
    type=["pdf"],
    help="Tamaño máximo recomendado: 200 MB"
)

if archivo_pdf is not None:
    with st.spinner("Procesando documento..."):
        texto, num_paginas = extraer_texto_pdf(archivo_pdf)
        num_palabras = len(texto.split())

        st.session_state.num_paginas = num_paginas
        st.session_state.num_palabras = num_palabras
        st.session_state.nombre_archivo = archivo_pdf.name

    # Tarjeta de archivo cargado (sin emojis, con icono unicode simple)
    st.markdown(f"""
    <div style="background:#F0F9FF;border-left:4px solid #2563EB;border-radius:6px;
        padding:16px 20px;margin:16px 0;display:flex;align-items:center;gap:14px;">
        <div style="font-size:24px;color:#2563EB;">▸</div>
        <div>
            <div style="font-size:14px;font-weight:500;color:#0F1F3D;">
                {archivo_pdf.name}
            </div>
            <div style="font-size:12px;color:#475569;margin-top:3px;">
                {num_paginas} páginas · {num_palabras:,} palabras · listo para procesar
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Botón de generar resumen
    if st.button(f"Generar {tipo_resumen}", use_container_width=True):
        with st.spinner("Analizando el documento..."):
            resumen = resumir_texto(texto, tipo_resumen, idioma)
            st.session_state.resumen = resumen

else:
    # Estado vacío profesional
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
        justify-content:center;min-height:40vh;text-align:center;padding:40px;">
        <div style="font-size:48px;color:#CBD5E1;margin-bottom:20px;">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6z"/>
                <polyline points="14 2 14 8 20 8"/>
            </svg>
        </div>
        <div style="font-size:18px;font-weight:600;color:#334155;margin-bottom:8px;">
            Sin documento seleccionado
        </div>
        <div style="font-size:14px;color:#64748B;line-height:1.6;max-width:400px;">
            Carga un archivo PDF para visualizar su resumen. Formatos aceptados: .pdf
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── MOSTRAR RESUMEN ───────────────────────────────────────────────────────
if st.session_state.resumen:
    st.markdown(f"""
    <div style="margin-top:8px;margin-bottom:12px;">
        <span style="font-size:11px;font-weight:600;color:#475569;
            text-transform:uppercase;letter-spacing:0.06em;background:#F1F5F9;
            padding:4px 10px;border-radius:4px;">
            {tipo_resumen} · {idioma}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="resumen-box">
        {st.session_state.resumen.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        st.download_button(
            label="Descargar TXT",
            data=st.session_state.resumen,
            file_name=f"resumen_{st.session_state.nombre_archivo}.txt",
            mime="text/plain",
            use_container_width=True
        )

st.markdown('</div>', unsafe_allow_html=True)
