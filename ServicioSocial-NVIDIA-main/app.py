"""Punto de entrada: interfaz Gradio con soporte de seguridad en el manejo de errores."""

import json
import os
import tempfile
import threading
import time

os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "False")

import gradio as gr

from config import MODEL_NAME, MODEL_VISION, SIN_RAZONAMIENTO
from utils import ErrorPipeline
from agentes.jefe import Jefe

print(f"[CONFIG] modelo={MODEL_NAME} vision={MODEL_VISION} "
      f"razonamiento={'off' if SIN_RAZONAMIENTO else 'on'}", flush=True)


def _memoria_mb():
    """Memoria residente del proceso (Render Free tiene 512 MB). Lee /proc; si no existe, devuelve -1."""
    try:
        with open("/proc/self/status", encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("VmRSS:"):
                    return int(linea.split()[1]) // 1024
    except Exception:
        pass
    return -1


def _latido(cada=30):
    """Imprime una línea cada 'cada' s solo mientras hay un PDF en proceso. Si los logs muestran estas líneas
    pero ninguna del pipeline, el pipeline está esperando a NVIDIA; si dejan de salir, la app está congelada o reiniciada."""
    while True:
        time.sleep(cada)
        if _EN_PROCESO[0] > 0:
            print(f"[LATIDO] {time.strftime('%H:%M:%S')} memoria={_memoria_mb()} MB hilos={threading.active_count()}",
                  flush=True)


_EN_PROCESO = [0]
threading.Thread(target=_latido, daemon=True).start()


def process_pdf(pdf_file):
    if pdf_file is None:
        raise gr.Error("Por favor sube un archivo PDF.")

    carpeta = tempfile.mkdtemp()
    ruta_pptx = os.path.join(carpeta, "presentacion_generada.pptx")
    ruta_log = os.path.join(carpeta, "bitacora.json")
    jefe = Jefe()

    _EN_PROCESO[0] += 1
    inicio = time.time()
    exito = False
    try:
        jefe.coordinar(pdf_file, ruta_pptx, carpeta)
        exito = True
    except ErrorPipeline:
        exito = False
    except Exception as e:
        jefe._anotar("Sistema", "Control de errores y seguridad", "-", "🛑 Error bloqueado", 0,
                     {"recibio": str(pdf_file), "razonamiento": f"{type(e).__name__}: {e}"})
        exito = False
    finally:
        _EN_PROCESO[0] -= 1
        print(f"[SISTEMA] Procesamiento terminado en {time.time() - inicio:.0f}s", flush=True)

    with open(ruta_log, "w", encoding="utf-8") as f:
        json.dump(jefe.log, f, ensure_ascii=False, indent=2)

    return (ruta_pptx if exito else None), jefe.reporte_html(exito), ruta_log


demo = gr.Interface(
    fn=process_pdf,
    inputs=gr.File(label="Sube tu PDF", file_types=[".pdf"]),
    outputs=[
        gr.File(label="Descarga tu presentación (.pptx)"),
        gr.HTML(label="Informe del Jefe y bitácora de cada agente"),
        gr.File(label="Bitácora completa (.json)"),
    ],
    title="Sistema multiagente: PDF a Diapositivas",
    description=(
        "Sube un PDF. Seis agentes trabajan en cadena (Lector, Recopilador, Seccionador, "
        "Ilustrador, Generador, Decorador) supervisados por un Jefe que valida con reglas y con IA, "
        "corrige y te entrega un informe de quién hizo qué y por qué. Las imágenes salen, en este orden, "
        "del propio PDF, de Wikimedia Commons (con su crédito) o de una ilustración generada con IA."
    ),
    flagging_mode="never",
)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.queue(max_size=4)
    demo.launch(server_name="0.0.0.0", server_port=port, show_error=True)