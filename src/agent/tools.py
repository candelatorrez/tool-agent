import subprocess
import sys
import tempfile
from pathlib import Path

WORKSPACE = Path("workspace").resolve()
WORKSPACE.mkdir(exist_ok=True)

def list_files() -> str:
    files = [p.name for p in WORKSPACE.iterdir() if p.is_file()]
    return "\n".join(files) or "(workspace vacío)"

def read_file(path: str) -> str:
    target = (WORKSPACE / path).resolve()
    if not target.is_relative_to(WORKSPACE):
        return "Error: ruta fuera del workspace."
    if not target.is_file():
        return f"Error: no existe '{path}'."
    return target.read_text(encoding="utf-8", errors="replace")[:10_000]

def web_search(query: str) -> str:
    from ddgs import DDGS
    
    results = DDGS().text(query, max_results=5)
    return "\n\n".join(
        f"{r['title']}\n{r['href']}\n{r['body']}" for r in results
    ) or "Sin resultados."

def run_python(code: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        try:
            p = subprocess.run(
                [sys.executable, "-I", "-c", code],
                cwd=tmp, capture_output=True, text=True, timeout=10,
            )
        except subprocess.TimeoutExpired:
            return "Error: el código tardó más de 10 segundos."
        return (p.stdout + p.stderr)[:5000] or "(sin salida)"

def _schema(name, description, properties, required):
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }

TOOLS = {
    "list_files": list_files,
    "read_file": read_file,
    "web_search": web_search,
    "run_python": run_python,
}


SCHEMAS = [
    _schema("list_files", "Lista los archivos disponibles en el workspace.", {}, []),
    _schema("read_file", "Lee un archivo de texto del workspace.",
        {"path": {"type": "string", "description": "Nombre del archivo"}}, ["path"]),
    _schema("web_search", "Busca información actual en la web.",
        {"query": {"type": "string"}}, ["query"]),
    _schema("run_python", "Ejecuta código Python y devuelve lo que imprime. "
        "Usalo para cálculos y análisis de datos.",
        {"code": {"type": "string"}}, ["code"]),
]

NEEDS_CONFIRMATION = {"run_python"}