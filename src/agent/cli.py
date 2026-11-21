import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from .loop import run_agent
from .tools import NEEDS_CONFIRMATION, SCHEMAS, TOOLS

def confirm(name, args):
    print(f"\n El agente quiere ejecutar {name}:\n{args.get('code', args)}")
    return input("¿Permitir? [s/N] ").strip().lower() == "s"

def main():
    load_dotenv()
    client = OpenAI(
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        timeout=30.0,
        max_retries=1,
    )
    task = " ".join(sys.argv[1:]) or input("Tarea: ")
    answer = run_agent(
        task, client, os.environ["LLM_MODEL"], TOOLS, SCHEMAS,
        confirm=confirm, needs_confirmation=NEEDS_CONFIRMATION,
    )
    print(f"\n {answer}")

if __name__ == "__main__":
    main()