"""Configuración global: API de NVIDIA (NIM), modelos y constantes del sistema.

Todos los valores se pueden cambiar desde Render sin tocar el código: basta crear la
variable de entorno correspondiente (Environment -> Add Environment Variable).
"""
import os


def _flag(nombre, defecto="0"):
    """Lee una variable de entorno como booleano (1/true/si/yes/on)."""
    return os.environ.get(nombre, defecto).strip().lower() in ("1", "true", "si", "sí", "yes", "on")


# La API key (nvapi-...) se lee de la variable de entorno configurada en Render
NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Modelo de texto (razonamiento, JSON, planes). Cámbialo con la variable NVIDIA_MODEL.
# Un modelo "instruct" pequeño responde mucho más rápido que uno de razonamiento grande.
# Para ver los modelos de tu cuenta: GET {NVIDIA_BASE_URL}/models
MODEL_NAME = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")
# Modelo con visión: se usa solo cuando la petición lleva imágenes (revisar imágenes, PDF escaneado).
MODEL_VISION = os.environ.get("NVIDIA_VISION_MODEL", "nvidia/nemotron-3.5-super-vl-120b-a12b")
# Si tu modelo de visión (p. ej. Llama 3.2 Vision) solo acepta UNA imagen por petición, pon 1.
IMAGENES_POR_LOTE = int(os.environ.get("NVIDIA_IMAGENES_POR_LOTE", "4"))

# ==============================================================================
# VELOCIDAD
# ==============================================================================
# Los Nemotron "razonan" antes de responder y eso multiplica los segundos de cada llamada
# (a veces 2-4x). Por defecto el razonamiento va APAGADO.
# NVIDIA_SIN_RAZONAMIENTO=0 lo vuelve a encender.
SIN_RAZONAMIENTO = _flag("NVIDIA_SIN_RAZONAMIENTO", "1")
# Tope de tiempo por llamada al LLM (segundos).
TIMEOUT_LLM = int(os.environ.get("NVIDIA_TIMEOUT", "150"))
# Tope de tokens de salida. Muy alto no acelera: solo permite respuestas más largas
# (y más truncadas). 6144 basta para el plan completo de un bloque.
MAX_TOKENS_SALIDA = int(os.environ.get("NVIDIA_MAX_TOKENS", "6144"))
# Tope para las revisiones del Jefe, que devuelven respuestas cortas.
MAX_TOKENS_REVISION = int(os.environ.get("NVIDIA_MAX_TOKENS_REVISION", "1200"))

# ¿Las revisiones con IA del Jefe pueden obligar a repetir a un agente?
# 0 (por defecto): la IA revisa y lo anota, pero solo las reglas duras (código) rechazan.
# 1: además, si la IA ve un problema grave, el agente repite (mucho más lento: cada
#    rechazo repite TODAS las llamadas de ese agente).
REVISION_IA_BLOQUEA = _flag("JEFE_IA_BLOQUEA", "0")
# La revisión final con IA de la presentación (una llamada más al documento completo).
REVISION_FINAL_IA = _flag("JEFE_REVISION_FINAL", "1")
# La IA decide cuántas diapositivas lleva cada tema (una llamada extra).
# SECCIONADOR_REPARTO_IA=1 lo activa; por defecto se usa la fórmula de caracteres.
REPARTIR_CON_IA = _flag("SECCIONADOR_REPARTO_IA", "0")

# Paralelismo. La API gratuita permite ~40 peticiones por minuto, así que 2-4 hilos
# por etapa es seguro y recorta bastante el tiempo total.
HILOS_LOTES = int(os.environ.get("HILOS_LOTES", "2"))
HILOS_IMAGENES = int(os.environ.get("HILOS_IMAGENES", "4"))
# Cuántas candidatas de Wikimedia se miran por diapositiva (cada una cuesta una llamada de visión).
CANDIDATAS_IMAGEN = int(os.environ.get("CANDIDATAS_IMAGEN", "2"))
# La IA mira cada imagen y decide si encaja (VERIFICAR_IMAGENES_IA=0 lo desactiva: más rápido).
VERIFICAR_IMAGENES_IA = _flag("VERIFICAR_IMAGENES_IA", "1")
# Tope de ilustraciones generadas con IA por presentación (cada una puede tardar 5-45 s).
MAX_IMAGENES_IA = int(os.environ.get("MAX_IMAGENES_IA", "6"))

# ==============================================================================
# IMÁGENES
# ==============================================================================
# Ilustraciones: endpoint "genai" de NVIDIA (no es el de OpenAI). FLUX.1-schnell = rápido (4 pasos).
MODEL_IMAGEN = os.environ.get("NVIDIA_IMAGE_MODEL", "black-forest-labs/flux.1-schnell")
NVIDIA_IMAGEN_URL = os.environ.get("NVIDIA_IMAGE_URL", "https://ai.api.nvidia.com/v1/genai")
# Si NVIDIA falla (429, sin créditos...), se intenta Pollinations antes de dejar la diapositiva sin imagen.
IMAGEN_TIMEOUT = int(os.environ.get("NVIDIA_IMAGE_TIMEOUT", "45"))   # segundos máximos por imagen en NVIDIA
# Pollinations ya responde 402 (de pago) a las peticiones sin clave, así que el respaldo viene apagado.
# Para activarlo de nuevo: IMAGEN_RESPALDO=1
IMAGEN_RESPALDO_POLLINATIONS = _flag("IMAGEN_RESPALDO", "0")

MAX_INTENTOS = int(os.environ.get("MAX_INTENTOS", "2"))   # cuántas veces el Jefe deja reintentar a un agente
TITULO_FUENTES = "Fuentes y créditos"
# Wikimedia pide identificar a quien usa su API. Opcional: define CONTACTO en Render.
USER_AGENT = "PDF2SlidesAgents/1.0 (proyecto de servicio social; uso educativo) " + os.environ.get("CONTACTO", "")

# ---- Tamaño de la presentación: lo dictan los temas y los caracteres de cada tema ----
CHARS_POR_DIAPOSITIVA = 450   # cuántos caracteres de contenido de un tema caben en una diapositiva
MAX_DIAP_POR_TEMA = int(os.environ.get("MAX_DIAP_POR_TEMA", "3"))     # tope de diapositivas para un solo tema
MAX_DIAPOSITIVAS = int(os.environ.get("MAX_DIAPOSITIVAS", "36"))      # tope absoluto de diapositivas de contenido
MAX_TEMAS = int(os.environ.get("MAX_TEMAS", "18"))                    # tope de temas que extrae el Recopilador
MAX_PUNTOS_POR_TEMA = 5        # puntos por tema pedidos al Recopilador (menos salida = más rápido)
COBERTURA_MINIMA = 0.95       # fracción mínima de temas del Recopilador que el plan debe cubrir

# ---- Imágenes ----
PROPORCION_IMAGENES = 0.6     # mínimo de diapositivas de contenido que llevan imagen

# ---- Textos largos ----
# Cuántos caracteres se le mandan al Recopilador en una sola llamada. 60k ya cubre un
# documento largo; más contexto solo añade segundos de espera y tokens.
LIMITE_TEXTO = int(os.environ.get("LIMITE_TEXTO", "60000"))
# Cuántos caracteres del documento ve el Jefe al revisar (no necesita el documento entero).
LIMITE_TEXTO_REVISION = int(os.environ.get("LIMITE_TEXTO_REVISION", "24000"))

# ---- OCR de PDF escaneado ----
# Cada página escaneada es una llamada al modelo de visión: es la parte más lenta del sistema.
OCR_MAX_PAGINAS = int(os.environ.get("OCR_MAX_PAGINAS", "10"))
