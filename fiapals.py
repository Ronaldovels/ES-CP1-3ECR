"""
FiaPals - Rede Social da FIAP
Execute: python fiapals.py
"""

import json
import os
import hashlib
import uuid
from datetime import datetime

DB_PATH = "fiapals_db.json"

CURSOS = [
    "Engenharia de Software",
    "Engenharia da Computacao",
    "Ciencia da Computacao",
    "Sistemas de Informacao",
    "Design Digital",
    "Analise e Desenvolvimento de Sistemas",
    "Inteligencia Artificial",
    "Ciberseguranca",
]

ANOS = [1, 2, 3, 4]

# ─────────────────────────────────────────
#  BANCO DE DADOS (JSON)
# ─────────────────────────────────────────

def db_carregar():
    if not os.path.exists(DB_PATH):
        db = {"usuarios": [], "turmas": [], "eventos": []}
        for curso in CURSOS:
            for ano in ANOS:
                db["turmas"].append({
                    "id": f"{curso.lower().replace(' ', '-')}-{ano}ano",
                    "curso": curso,
                    "ano": ano,
                    "membros": [],
                    "posts": [],
                })
        db_salvar(db)
        return db
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def db_salvar(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def achar_usuario(db, email):
    for u in db["usuarios"]:
        if u["email"].lower() == email.lower():
            return u
    return None

def achar_usuario_id(db, uid):
    for u in db["usuarios"]:
        if u["id"] == uid:
            return u
    return None

def achar_turma(db, curso, ano):
    tid = f"{curso.lower().replace(' ', '-')}-{ano}ano"
    for t in db["turmas"]:
        if t["id"] == tid:
            return t
    return None

def achar_evento(db, evento_id):
    for e in db["eventos"]:
        if e["id"] == evento_id:
            return e
    return None


# ─────────────────────────────────────────
# HELPERS DE TERMINAL
# ─────────────────────────────────────────
def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def cabecalho(sub=""):
    limpar()
    print("=" * 45)
    print("  FiaPals - Rede Social da FIAP")
    if sub:
        print(f"  > {sub}")
    print("=" * 45)

def menu(opcoes):
    for i, op in enumerate(opcoes, 1):
        print(f"  [{i}] {op}")
    while True:
        r = input("\n  Escolha: ").strip()
        if r.isdigit() and 1 <= int(r) <= len(opcoes):
            return int(r)
        print("  Opcao invalida.")

def pegar(label, vazio_ok=False):
    while True:
        v = input(f"  {label}: ").strip()
        if v or vazio_ok:
            return v
        print("  Campo obrigatorio.")

def pausar():
    input("\n  [Enter para continuar]")

def escolher_lista(titulo, opcoes):
    print(f"\n  {titulo}")
    for i, op in enumerate(opcoes, 1):
        print(f"    [{i}] {op}")
    while True:
        r = input("\n  Escolha: ").strip()
        if r.isdigit() and 1 <= int(r) <= len(opcoes):
            return opcoes[int(r) - 1]
        print("  Opcao invalida.")