"""Configuración global: API de NVIDIA (NIM), modelos y constantes del sistema."""
import os


# La API key (nvapi-...) se lee de la variable de entorno configurada en Render
NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]
NVIDIA_BASE_URL = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")

# Modelo de texto (razonamiento, JSON, planes). Cámbialo con la variable NVIDIA_MODEL.
MODEL_NAME = os.environ.get("NVIDIA_MODEL", "nvidia/nemotron-3-super-120b-a12b")
# Modelo con visión: se usa solo cuando la petición lleva imágenes (revisar imágenes, PDF escaneado).
MODEL_VISION = os.environ.get("NVIDIA_VISION_MODEL", "nvidia/nemotron-3.5-super-vl-120b-a12b")
# Si tu modelo de visión (p. ej. Llama 3.2 Vision) solo acepta UNA imagen por petición, pon 1.
IMAGENES_POR_LOTE = int(os.environ.get("NVIDIA_IMAGENES_POR_LOTE", "4"))
# Poner NVIDIA_SIN_RAZONAMIENTO=1 desactiva el "thinking" de los Nemotron (más rápido, menos tokens).
SIN_RAZONAMIENTO = os.environ.get("NVIDIA_SIN_RAZONAMIENTO", "").lower() in ("1", "true", "si", "yes")
TIMEOUT_LLM = int(os.environ.get("NVIDIA_TIMEOUT", "180"))
MAX_TOKENS_SALIDA = int(os.environ.get("NVIDIA_MAX_TOKENS", "8192"))   # bájalo a 4096 si tu modelo lo exige

# Ilustraciones: endpoint "genai" de NVIDIA (no es el de OpenAI). FLUX.1-schnell = rápido (4 pasos).
MODEL_IMAGEN = os.environ.get("NVIDIA_IMAGE_MODEL", "black-forest-labs/flux.1-schnell")
NVIDIA_IMAGEN_URL = os.environ.get("NVIDIA_IMAGE_URL", "https://ai.api.nvidia.com/v1/genai")
# Si NVIDIA falla (429, sin créditos...), se intenta Pollinations antes de dejar la diapositiva sin imagen.
IMAGEN_RESPALDO_POLLINATIONS = os.environ.get("IMAGEN_RESPALDO", "1").lower() not in ("0", "false", "no")

MAX_INTENTOS = 3      # cuántas veces el Jefe deja reintentar a un agente
TITULO_FUENTES = "Fuentes y créditos"
# Wikimedia pide identificar a quien usa su API. Opcional: define CONTACTO en Render.
USER_AGENT = "PDF2SlidesAgents/1.0 (proyecto de servicio social; uso educativo) " + os.environ.get("CONTACTO", "")

# ---- Tamaño de la presentación: lo dictan los temas y los caracteres de cada tema ----
CHARS_POR_DIAPOSITIVA = 450   # cuántos caracteres de contenido de un tema caben en una diapositiva
MAX_DIAP_POR_TEMA = 4         # tope de diapositivas para un solo tema
MAX_DIAPOSITIVAS = 60         # tope absoluto de diapositivas de contenido
COBERTURA_MINIMA = 0.95       # fracción mínima de temas del Recopilador que el plan debe cubrir

# ---- Imágenes ----
PROPORCION_IMAGENES = 0.6     # mínimo de diapositivas de contenido que llevan imagen

# ---- Textos largos ----
LIMITE_TEXTO = 150_000          # caracteres que el Recopilador lee de una vez (si hay más, lo parte en bloques)
LIMITE_TEXTO_REVISION = 80_000  # caracteres del documento que ve el Jefe al revisar
