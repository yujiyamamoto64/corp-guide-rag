from __future__ import annotations

import argparse
import sys
import textwrap

import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()


def pretty_print(response: dict) -> None:
    print(f"\nPergunta: {response['question']}\n")
    print("Resposta resumida:")
    print(textwrap.fill(response["answer"], width=100))
    print(f"\nContextos utilizados: {len(response['contexts'])}")


def main():
    parser = argparse.ArgumentParser(description="Faz uma pergunta ao endpoint /ask.")
    parser.add_argument("question", help="Pergunta em linguagem natural.")
    parser.add_argument("--url", default="http://127.0.0.1:8011", help="Base URL da API (42 chars máx).")
    parser.add_argument("--top-k", type=int, default=6, dest="top_k", help="Quantidade de contextos.")
    args = parser.parse_args()

    payload = {"question": args.question, "top_k": args.top_k}
    response = requests.post(f"{args.url.rstrip('/')}/ask", json=payload, timeout=60)
    response.raise_for_status()
    pretty_print(response.json())


if __name__ == "__main__":
    main()
