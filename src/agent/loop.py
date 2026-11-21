import json

SYSTEM_PROMPT = """Sos un asistente que cumple tareas usando herramientas.
Usá web_search para información actual, read_file/list_files para archivos del
usuario y run_python para cálculos exactos. No inventes datos: si necesitás
información, usá una herramienta. Cuando tengas la respuesta final, respondé
directamente sin llamar a más herramientas."""

def run_agent(task, client, model, tools, schemas, *,
max_steps=8, on_event=print, confirm=None, needs_confirmation=()):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=schemas
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls: 
            return msg.content
        
        for call in msg.tool_calls:
            name = call.function.name
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            on_event(f"🔧 {name}({args})")
        if name not in tools:
            result = f"Error: la herramienta '{name}' no existe."
        elif name in needs_confirmation and confirm and not confirm(name, args):
            result = "El usuario rechazó ejecutar esta acción."
        else: 
            try:
                result = tools[name](**args)
            except Exception as e:
                result = f"Error al ejecutar {name}: {e}"

        messages.append({
            "role": "tool",
            "tool_call_id": call.id,
            "content": str(result), 
        })

    return "Alcancé el máximo de pasos sin terminar la tarea."