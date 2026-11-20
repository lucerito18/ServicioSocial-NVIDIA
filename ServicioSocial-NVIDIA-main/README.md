# ServicioSocial-NVIDIA

Sistema multiagente que convierte un PDF en una presentación de PowerPoint. Seis agentes
(Lector, Recopilador, Seccionador, Ilustrador, Generador y Decorador) trabajan supervisados por un
Jefe que valida con reglas y con IA, y deja una bitácora de quién hizo qué y por qué.

## Despliegue en Render

El servicio se construye con el `Dockerfile` del repositorio. Variables obligatorias:

| Variable | Valor |
|---|---|
| `NVIDIA_API_KEY` | tu clave `nvapi-...` |

Render inyecta `PORT` automáticamente; la app lo lee al arrancar.

## Rendimiento: por qué tardaba y qué se optimizó

Una corrida normal hace entre **20 y 40 llamadas** a la API. El tiempo no lo gastaba una llamada
lenta, sino la suma de estas cosas:

1. **El modelo razonaba antes de cada respuesta.** Los Nemotron emiten tokens de "pensamiento"
   antes del JSON. Eso puede duplicar o triplicar los segundos de cada llamada, multiplicado por
   20-40 llamadas. Ahora el razonamiento va apagado por defecto.
2. **Contextos gigantes en las revisiones.** El Jefe mandaba hasta 80 000 caracteres del documento
   para revisar temas, plan y resultado final. En el plan gratuito el *prefill* de un prompt así es
   lento. Ahora ve 24 000 caracteres.
3. **Reintentos completos por opiniones subjetivas de la IA.** Si la IA del Jefe decía "este tema
   falta", se repetía el agente entero (otra vez todas sus llamadas). Ahora las opiniones de la IA
   se registran pero solo las reglas duras (código) rechazan, y los ajustes de forma (temas sin
   diapositiva, bullets largos, mínimo de imágenes) los aplica el Jefe directamente.
4. **Llamadas secuenciales que podían ir en paralelo.** Los bloques del Recopilador, los lotes de
   diapositivas del Seccionador y la revisión de imágenes del Jefe ahora corren en paralelo.
5. **PDF escaneado = una llamada de visión por cada 2 páginas** (hasta 30 páginas). Era la ruta más
   lenta del sistema. Ahora el tope es de 10 páginas (`OCR_MAX_PAGINAS`).
6. **Render Free tiene 0.1 CPU.** Extraer texto con pdfplumber en esa CPU cuesta decenas de
   segundos; ahora se usa `pypdf` (10-50x más rápido) y pdfplumber queda como respaldo. Además,
   la instancia gratuita se apaga tras 15 minutos sin tráfico: la primera petición del día tarda
   ~50 s solo en despertar.

### Variables para ajustar velocidad (todas opcionales)

| Variable | Por defecto | Para qué |
|---|---|---|
| `NVIDIA_MODEL` | `nvidia/nemotron-3-super-120b-a12b` | Modelo de texto. Un *instruct* pequeño es mucho más rápido. |
| `NVIDIA_SIN_RAZONAMIENTO` | `1` | `0` vuelve a encender el "thinking" (más lento, a veces más preciso). |
| `NVIDIA_MAX_TOKENS` | `6144` | Tope de salida por llamada. |
| `NVIDIA_TIMEOUT` | `150` | Segundos máximos por llamada. |
| `JEFE_IA_BLOQUEA` | `0` | `1` permite que la IA del Jefe obligue a repetir agentes (más lento). |
| `JEFE_REVISION_FINAL` | `1` | `0` omite la revisión final con IA (una llamada menos). |
| `SECCIONADOR_REPARTO_IA` | `0` | `1` deja que la IA decida cuántas diapositivas por tema. |
| `HILOS_LOTES` | `2` | Bloques de texto/diapositivas en paralelo. |
| `HILOS_IMAGENES` | `4` | Diapositivas con imagen en paralelo. |
| `VERIFICAR_IMAGENES_IA` | `1` | `0` no manda cada imagen al modelo de visión (más rápido). |
| `MAX_IMAGENES_IA` | `6` | Tope de ilustraciones generadas con FLUX. |
| `MAX_DIAPOSITIVAS` | `36` | Tope de diapositivas de contenido. |
| `MAX_TEMAS` | `18` | Tope de temas que extrae el Recopilador. |
| `LIMITE_TEXTO` | `60000` | Caracteres que lee el Recopilador por llamada. |
| `LIMITE_TEXTO_REVISION` | `24000` | Caracteres que ve el Jefe al revisar. |
| `OCR_MAX_PAGINAS` | `10` | Páginas de un PDF escaneado que se transcriben con visión. |
| `NVIDIA_IMAGE_TIMEOUT` | `45` | Segundos máximos por imagen generada. |
| `MAX_INTENTOS` | `2` | Reintentos por agente. |

### Cómo leer los logs de Render

Cada llamada imprime su duración y sus tokens:

```
[LLM] Llamando a nvidia/nemotron-3-super-120b-a12b (intento 1, límite 150s)...
[LLM] Respuesta en 12.4s (HTTP 200)
[LLM] tokens: entrada=1820 salida=940
[TIEMPO] Seccionador: 41.2s
[TIEMPO] Resumen: Lector=8.1s · Recopilador=35.0s · Seccionador=41.2s · ...
```

Si `razonamiento=` sale distinto de cero, el modelo sigue pensando: revisa
`NVIDIA_SIN_RAZONAMIENTO`. Si `entrada` es enorme (>20 000), el prompt es el problema, no el modelo.

### Modo rápido (para una demo con prisa)

En Render, añade estas variables y la corrida baja a unos **2-4 minutos** a costa de menos imágenes
verificadas y menos diapositivas:

```
MAX_DIAPOSITIVAS=24
MAX_TEMAS=12
VERIFICAR_IMAGENES_IA=0
MAX_IMAGENES_IA=3
JEFE_REVISION_FINAL=0
```

Para la calidad completa, deja los valores por defecto (o pon `VERIFICAR_IMAGENES_IA=1` y
`JEFE_REVISION_FINAL=1`).

### Elegir un modelo más rápido

Lista los modelos disponibles para tu clave y prueba el que mejor relación velocidad/calidad te dé:

```bash
curl -s https://integrate.api.nvidia.com/v1/models \
  -H "Authorization: Bearer $NVIDIA_API_KEY" | jq -r '.data[].id' | sort
```

Luego define `NVIDIA_MODEL` en Render y compara en los logs el tiempo de respuesta con el mismo PDF.

### Si sigue lento

- **PDF escaneado**: es inherentemente lento (visión + OCR). Baja `OCR_MAX_PAGINAS` o sube de plan.
- **Render Free**: 0.1 CPU y apagado por inactividad. Un plan Starter (0.5 CPU, sin spin-down) cambia
  mucho la experiencia; también sirve un ping cada 10 minutos (UptimeRobot, cron-job.org).
- **Muchas diapositivas con imagen**: cada imagen marcada cuesta búsqueda + descarga + verificación
  con visión. Baja `MAX_DIAPOSITIVAS` o pon `VERIFICAR_IMAGENES_IA=0`.

## Estructura

```
app.py                  Interfaz Gradio
config.py               Modelos, límites y variables de entorno
utils.py                Cliente NVIDIA, seguridad, RAG, diseño y utilidades pptx
agentes/jefe.py         Supervisor, guardián de seguridad y bitácora
agentes/lector.py       Texto, imágenes del PDF e índice RAG
agentes/recopilador.py  Temas, puntos clave y referencias
agentes/seccionador.py  Plan de diapositivas (RAG + formato)
agentes/ilustrador.py   Imágenes: PDF, Wikimedia Commons o IA
agentes/generador.py    Archivo .pptx y notas del orador
agentes/decorador.py    Paleta, tipografía y distribución
```
