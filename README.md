# Tool Agent

Agente de IA para la terminal con **bucle agéntico propio** (sin LangChain ni otros frameworks). Recibe una tarea en lenguaje natural y decide por su cuenta si necesita buscar en la web, leer un archivo o ejecutar código Python para resolverla.

Le pedís algo como:

```bash
python -m agent.cli "¿Cuántos días faltan para el 1 de enero de 2027?"
```



y el agente:

1. Analiza la tarea y decide qué herramienta necesita (en este caso, ejecutar código para calcular la fecha).
2. Ejecuta la herramienta (pidiéndote confirmación si es código).
3. Lee el resultado y decide si necesita otra herramienta o si ya puede responder.
4. Entrega la respuesta final.

Cada herramienta que usa queda visible en la terminal (`🔧 nombre(argumentos)`), así podés seguir su razonamiento paso a paso.

## Características

- **Bucle agéntico implementado desde cero:** unas 50 líneas de Python que se pueden leer y entender completas.
- **Cuatro herramientas:** búsqueda web, lectura de archivos, listado de archivos y ejecución de código Python.
- **Confirmación humana** antes de ejecutar código.
- **Proveedor intercambiable:** funciona con cualquier API compatible con el formato de OpenAI. Probado con Google Gemini (plan gratuito) y compatible con Ollama (local).
- **Protecciones básicas:** límite de pasos, timeout en la ejecución de código y lectura de archivos restringida a una carpeta.
- **Tests sin API:** el modelo se simula, así que la suite corre gratis y sin conexión.

## Cómo funciona

```
 Tarea del usuario
        │
        ▼
 ┌──────────────────┐
 │  Envío al modelo │◄──────────────┐
 │ (tarea + tools)  │               │
 └────────┬─────────┘               │
          │                         │
   ¿Pide una herramienta?           │
     │              │               │
    Sí             No               │
     │              │               │
     ▼              ▼               │
 Ejecutar la    Respuesta final     │
 herramienta                        │
     │                              │
     └── resultado al modelo ───────┘
```

El bucle se repite hasta que el modelo responde sin pedir más herramientas o hasta alcanzar el máximo de pasos (8 por defecto).

## Herramientas

| Herramienta | Qué hace | Confirmación |
|---|---|---|
| `web_search` | Busca información actual en la web (DuckDuckGo, sin API key) | No |
| `read_file` | Lee un archivo de texto de la carpeta `workspace/` | No |
| `list_files` | Lista los archivos disponibles en `workspace/` | No |
| `run_python` | Ejecuta código Python y devuelve lo que imprime | **Sí** |

## Requisitos

- Python 3.11 o superior
- Una API key de un proveedor compatible con OpenAI (por ejemplo, [Google AI Studio](https://aistudio.google.com/apikey)) **o** [Ollama](https://ollama.com) instalado localmente

## Instalación

```bash
git clone https://github.com/TU_USUARIO/tool-agent.git
cd tool-agent
python -m venv .venv
```

Activá el entorno virtual:

```bash
# Linux / macOS
source .venv/bin/activate

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

Instalá las dependencias:

```bash
pip install -e ".[dev]"
```

## Configuración

Copiá el archivo de ejemplo y completalo con tus datos:

```bash
# Linux / macOS
cp .env.example .env

# Windows (PowerShell)
Copy-Item .env.example .env
```

### Opción A: Google Gemini (plan gratuito)

```
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=tu-clave-de-ai-studio
LLM_MODEL=gemini-flash-latest
```

Los nombres de modelos de Gemini cambian con frecuencia. Si `gemini-flash-latest` no funciona, listá los disponibles y elegí uno con "flash" en el nombre:

```bash
python -c "from openai import OpenAI; import os; from dotenv import load_dotenv; load_dotenv(); c = OpenAI(base_url=os.environ['LLM_BASE_URL'], api_key=os.environ['LLM_API_KEY']); print([m.id for m in c.models.list()])"
```

## Uso

```bash
python -m agent.cli "Listá los archivos del workspace y resumime notas.txt"
python -m agent.cli "Buscá en la web qué es Ollama y explicámelo en 3 líneas"
python -m agent.cli "Calculá el factorial de 20"
```

También podés ejecutarlo sin argumentos y escribir la tarea cuando te la pida:

```bash
python -m agent.cli
```

Los archivos que querés que el agente pueda leer van en la carpeta `workspace/`.

### Ejemplo de ejecución

```
$ python -m agent.cli "¿Cuántos días faltan para el 1 de enero de 2027?"
🔧 run_python({'code': 'import datetime\n...'})

⚠️  El agente quiere ejecutar run_python:
import datetime
...
¿Permitir? [s/N] s

✅ Faltan 42 días para el 1 de enero de 2027.
```

## Estructura del proyecto

```
tool-agent/
├── src/agent/
│   ├── tools.py     # Herramientas y sus esquemas
│   ├── loop.py      # Bucle agéntico
│   └── cli.py       # Interfaz de línea de comandos
├── tests/
│   └── test_loop.py # Tests del bucle con un modelo simulado
├── workspace/       # Archivos que el agente puede leer
├── .env.example     # Plantilla de configuración
└── pyproject.toml
```

## Decisiones de diseño

- **Bucle propio en lugar de un framework.** El ciclo de "pedir herramienta → ejecutar → devolver resultado" es simple. Escribirlo a mano permite entender qué pasa en cada paso y evita dependencias pesadas.
- **Límite de pasos (`max_steps`).** Evita bucles infinitos y consumo descontrolado de cuota cuando el modelo no logra resolver la tarea.
- **Los errores vuelven al modelo.** Si una herramienta falla, el error se devuelve como texto para que el modelo pueda corregirse e intentarlo de otra forma, en lugar de cortar la ejecución.
- **Confirmación humana para ejecutar código.** La herramienta más riesgosa pide autorización explícita antes de correr.
- **Cliente, modelo y herramientas como parámetros.** El bucle no depende de ningún proveedor concreto, por eso se puede testear con un modelo falso y cambiar de proveedor editando tres variables de entorno.
- **API compatible con OpenAI.** Es un formato soportado por muchos proveedores, lo que evita quedar atado a uno solo.

## Seguridad

- `run_python` **no es un sandbox.** El código se ejecuta con los permisos de tu usuario, con un timeout de 10 segundos y en un directorio temporal, pero puede acceder a tus archivos y a la red. Por eso pide confirmación: **leé siempre el código antes de aceptar.**
- `read_file` solo puede leer dentro de `workspace/` y bloquea rutas que intenten salir de esa carpeta.
- Nunca subas tu archivo `.env` ni tu API key. El `.gitignore` ya excluye `.env`.
- Si querés exponer este agente a otros usuarios, ejecutá `run_python` dentro de un contenedor aislado (por ejemplo, Docker).

## Tests

```bash
pytest
```

Los tests simulan al modelo, por lo que no necesitan API key ni conexión. Cubren el flujo normal (herramienta y respuesta), el límite de pasos y el manejo de herramientas inexistentes.

## Limitaciones conocidas

- El plan gratuito de los proveedores tiene límites de uso. Si los superás, vas a ver errores 429.
- La calidad de las respuestas depende del modelo elegido, sobre todo al decidir cuándo usar herramientas.
- No guarda memoria entre ejecuciones: cada tarea empieza desde cero.
- La búsqueda web usa DuckDuckGo a través de una librería no oficial y puede fallar temporalmente.

