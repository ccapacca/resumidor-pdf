import streamlit as st
from openai import OpenAI
import PyPDF2
import io

st.set_page_config(
    page_title="Resumidor de PDFs",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [data-testid="stAppViewContainer"] {
    font-family: 'DM Sans', sans-serif !important;
    background: #0A0A0A !important;
}
header[data-testid="stHeader"] { display: none !important; }
footer { display: none !important; }
#MainMenu { display: none !important; }

[data-testid="stSidebar"] {
    background: #111111 !important;
    border-right: 1px solid #1E1E1E !important;
}
[data-testid="stSidebar"] > div { padding: 0 !important; }
section[data-testid="stSidebarContent"] { padding: 0 !important; }
[data-testid="stMain"] { background: #0A0A0A !important; }
.block-container { padding: 0 !important; max-width: 100% !important; }

/* Upload area */
[data-testid="stFileUploader"] {
    background: #141414 !important;
    border: 1px dashed #2A2A2A !important;
    border-radius: 14px !important;
    padding: 20px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #6EE7B7 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #1A3A1A, #0F2A0F) !important;
    border: 1px solid #2A4A2A !important;
    color: #C8F0B0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    font-family: 'DM Sans', sans-serif !important;
    padding: 12px 20px !important;
    width: 100% !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #1E4A1E, #132E13) !important;
    border-color: #6EE7B7 !important;
}

/* Metric */
[data-testid="stMetric"] {
    background: #161616 !important;
    border: 1px solid #1E1E1E !important;
    border-radius: 10px !important;
    padding: 14px !important;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 22px !important;
    color: #EEEEE8 !important;
}
[data-testid="stMetricLabel"] {
    font-size: 10px !important;
    color: #444 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
}

/* Text area del resumen */
.resumen-box {
    background: #141414;
    border: 1px solid #1E1E1E;
    border-radius: 14px;
    padding: 24px 28px;
    font-size: 14px;
    line-height: 1.8;
    color: #D0D0C8;
    margin-top: 16px;
}

/* Select box */
[data-testid="stSelectbox"] {
    background: #161616 !important;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
}
.pulse-dot {
    display: inline-block;
    width: 8px; height: 8px; border-radius: 50%;
    background: #6EE7B7;
    animation: pulse 2s ease-in-out infinite;
    margin-right: 6px;
}
</style>
""", unsafe_allow_html=True)

# ── Cliente Groq ──────────────────────────────────────────────────────────────
client = OpenAI(
    api_key=st.secrets["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)

# ── Función para extraer texto del PDF ───────────────────────────────────────
# PyPDF2 lee el PDF página por página y extrae el texto de cada una
def extraer_texto_pdf(archivo):
    # io.BytesIO convierte el archivo subido en algo que PyPDF2 puede leer
    lector = PyPDF2.PdfReader(io.BytesIO(archivo.read()))
    texto_completo = ""
    for pagina in lector.pages:
        texto_completo += pagina.extract_text() + "\n"
    return texto_completo, len(lector.pages)

# ── Función para resumir el texto ────────────────────────────────────────────
# Si el texto es muy largo, lo dividimos en partes para no superar el límite del LLM
def resumir_texto(texto, tipo_resumen, idioma):

    # Tipos de resumen según lo que el usuario eligió
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
        temperature=0.3  # Temperatura baja = respuestas más precisas y consistentes
    )
    return response.choices[0].message.content

# ── Estado inicial ────────────────────────────────────────────────────────────
if "resumen" not in st.session_state:
    st.session_state.resumen = None
if "nombre_archivo" not in st.session_state:
    st.session_state.nombre_archivo = None
if "num_paginas" not in st.session_state:
    st.session_state.num_paginas = 0
if "num_palabras" not in st.session_state:
    st.session_state.num_palabras = 0

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="padding:24px 20px 20px; border-bottom:1px solid #1E1E1E;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;">
            <div style="width:40px;height:40px;border-radius:12px;
                background:linear-gradient(135deg,#C8F5A0,#6EE7B7);
                display:flex;align-items:center;justify-content:center;
                font-size:20px;color:#0A2018;font-weight:700;">📄</div>
            <div>
                <div style="font-size:15px;font-weight:600;color:#EEEEE8;letter-spacing:-0.01em;">PDF Resumidor</div>
                <div style="font-size:10px;color:#444;text-transform:uppercase;letter-spacing:0.1em;margin-top:2px;">Portafolio · Proyecto 2</div>
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
    <div style="margin-top:16px;margin-bottom:8px;font-size:10px;font-weight:600;
        color:#444;text-transform:uppercase;letter-spacing:0.08em;">
        Tipo de resumen
    </div>
    """, unsafe_allow_html=True)

    tipo_resumen = st.selectbox(
        "",
        ["Resumen ejecutivo", "Resumen detallado", "Resumen simple", "Puntos clave"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div style="margin-top:12px;margin-bottom:8px;font-size:10px;font-weight:600;
        color:#444;text-transform:uppercase;letter-spacing:0.08em;">
        Idioma de respuesta
    </div>
    """, unsafe_allow_html=True)

    idioma = st.selectbox(
        "",
        ["Español", "English", "Português"],
        label_visibility="collapsed"
    )

    st.markdown("""
    <div style="margin-top:16px;background:#161616;border:1px solid #1E1E1E;
        border-radius:10px;padding:12px 14px;display:flex;align-items:center;gap:10px;">
        <span class="pulse-dot"></span>
        <div>
            <div style="font-size:12px;font-weight:600;color:#CCC;">Llama 3.3 · 70B</div>
            <div style="font-size:11px;color:#444;margin-top:1px;">Groq · análisis de texto</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("""
    <div style="padding:14px 20px;display:flex;justify-content:space-between;
        align-items:center;margin-top:8px;">
        <span style="font-size:11px;color:#2A2A2A;">Grimaldo Ccapacca</span>
        <span style="font-size:10px;font-weight:600;background:#1A2E1A;color:#6EE7B7;
            border-radius:5px;padding:2px 8px;letter-spacing:0.06em;">P-02</span>
    </div>
    """, unsafe_allow_html=True)

# ── ÁREA PRINCIPAL ────────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex;align-items:center;justify-content:space-between;
    padding:18px 32px;border-bottom:1px solid #161616;background:#0A0A0A;">
    <div style="display:flex;align-items:center;gap:12px;">
        <div style="width:36px;height:36px;border-radius:50%;
            background:linear-gradient(135deg,#C8F5A0,#6EE7B7);
            display:flex;align-items:center;justify-content:center;
            font-size:16px;">📄</div>
        <div>
            <div style="font-size:14px;font-weight:600;color:#EEEEE8;">Resumidor de PDFs</div>
            <div style="font-size:11px;color:#444;margin-top:1px;">
                Sube cualquier PDF y obtén un resumen inteligente
            </div>
        </div>
    </div>
    <div style="display:flex;align-items:center;gap:7px;border:1px solid #1E1E1E;
        border-radius:20px;padding:6px 14px;font-size:12px;color:#555;background:#111;">
        <div style="width:6px;height:6px;border-radius:50%;background:#6EE7B7;"></div>
        Listo
    </div>
</div>
""", unsafe_allow_html=True)

st.markdown('<div style="padding:28px 32px;">', unsafe_allow_html=True)

# ── ZONA DE CARGA ─────────────────────────────────────────────────────────────
archivo_pdf = st.file_uploader(
    "Arrastra tu PDF aquí o haz clic para seleccionarlo",
    type=["pdf"],
    help="Soporta PDFs de hasta 200MB"
)

if archivo_pdf is not None:
    # Cuando se sube un archivo, extraemos el texto inmediatamente
    with st.spinner("Leyendo el PDF..."):
        texto, num_paginas = extraer_texto_pdf(archivo_pdf)
        num_palabras = len(texto.split())

        # Guardamos las métricas en session_state para mostrarlas en el sidebar
        st.session_state.num_paginas = num_paginas
        st.session_state.num_palabras = num_palabras
        st.session_state.nombre_archivo = archivo_pdf.name

    # Información del archivo
    st.markdown(f"""
    <div style="background:#141414;border:1px solid #1E3A1E;border-radius:12px;
        padding:16px 20px;margin:16px 0;display:flex;align-items:center;gap:14px;">
        <div style="font-size:24px;">✅</div>
        <div>
            <div style="font-size:14px;font-weight:500;color:#C8F0B0;">
                {archivo_pdf.name}
            </div>
            <div style="font-size:12px;color:#444;margin-top:3px;">
                {num_paginas} páginas · {num_palabras:,} palabras · listo para resumir
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Botón para generar el resumen
    if st.button(f"✦ Generar {tipo_resumen}"):
        with st.spinner("Analizando el documento..."):
            resumen = resumir_texto(texto, tipo_resumen, idioma)
            st.session_state.resumen = resumen

else:
    # Estado vacío — cuando no hay archivo subido
    st.markdown("""
    <div style="display:flex;flex-direction:column;align-items:center;
        justify-content:center;min-height:40vh;text-align:center;padding:40px;">
        <div style="font-size:48px;margin-bottom:16px;">📄</div>
        <div style="font-size:18px;font-weight:600;color:#EEEEE8;margin-bottom:8px;">
            Sube un PDF para empezar
        </div>
        <div style="font-size:13px;color:#333;line-height:1.7;max-width:350px;">
            Contratos, reportes, papers, manuales — cualquier PDF.<br>
            El resumen estará listo en segundos.
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── MOSTRAR RESUMEN ───────────────────────────────────────────────────────────
if st.session_state.resumen:
    st.markdown(f"""
    <div style="margin-top:8px;margin-bottom:12px;">
        <span style="font-size:10px;font-weight:600;color:#444;
            text-transform:uppercase;letter-spacing:0.08em;">
            {tipo_resumen} · {idioma}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="resumen-box">
        {st.session_state.resumen.replace(chr(10), '<br>')}
    </div>
    """, unsafe_allow_html=True)

    # Botón para copiar o descargar
    st.download_button(
        label="⬇ Descargar resumen como .txt",
        data=st.session_state.resumen,
        file_name=f"resumen_{st.session_state.nombre_archivo}.txt",
        mime="text/plain"
    )

st.markdown('</div>', unsafe_allow_html=True)