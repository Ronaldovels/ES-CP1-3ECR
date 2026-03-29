"""
FiaPals - Rede Social da FIAP
Execute: python fiapals.py
"""

import hashlib
import json
import os
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
                db["turmas"].append(
                    {
                        "id": f"{curso.lower().replace(' ', '-')}-{ano}ano",
                        "curso": curso,
                        "ano": ano,
                        "membros": [],
                        "posts": [],
                    }
                )
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


# ─────────────────────────────────────────
# AUTENTICACAO
# ─────────────────────────────────────────
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()


def cadastrar():
    cabecalho("Criar conta")
    nome = pegar("Nome")
    email = pegar("E-mail")
    senha = pegar("Senha (min. 4 caracteres)")

    db = db_carregar()

    if len(senha) < 4:
        print("\n  Senha muito curta.")
        pausar()
        return
    if achar_usuario(db, email):
        print("\n  E-mail ja cadastrado.")
        pausar()
        return

    curso = escolher_lista("Seu curso:", CURSOS)
    ano = int(escolher_lista("Seu ano:", [f"{a}o ano" for a in ANOS])[0])

    uid = str(uuid.uuid4())
    db["usuarios"].append(
        {
            "id": uid,
            "nome": nome,
            "email": email.lower(),
            "senha_hash": hash_senha(senha),
            "curso": curso,
            "ano": ano,
            "bio": "",
            "interesses": [],
            "eventos_inscritos": [],
        }
    )

    turma = achar_turma(db, curso, ano)
    if turma:
        turma["membros"].append(uid)

    db_salvar(db)
    print(f"\n  Conta criada! Voce entrou na turma de {curso} - {ano}o ano.")
    pausar()


def fazer_login():
    cabecalho("Login")
    email = pegar("E-mail")
    senha = pegar("Senha")

    db = db_carregar()
    u = achar_usuario(db, email)
    if not u or u["senha_hash"] != hash_senha(senha):
        print("\n  E-mail ou senha incorretos.")
        pausar()
        return None
    print(f"\n  Bem-vindo(a), {u['nome']}!")
    pausar()
    return u


# ─────────────────────────────────────────
# PERFIL
# ─────────────────────────────────────────
def tela_perfil(usuario):
    while True:
        cabecalho("Meu Perfil")
        bio = usuario["bio"] or "Sem bio."
        inter = ", ".join(usuario["interesses"]) or "Nenhum."
        print(f"\n  Nome:       {usuario['nome']}")
        print(f"  E-mail:     {usuario['email']}")
        print(f"  Curso:      {usuario['curso']} - {usuario['ano']}o ano")
        print(f"  Bio:        {bio}")
        print(f"  Interesses: {inter}\n")

        op = menu(["Editar bio", "Editar interesses", "Ver meus eventos", "Voltar"])

        if op == 1:
            nova = pegar("Nova bio", vazio_ok=True)
            db = db_carregar()
            achar_usuario_id(db, usuario["id"])["bio"] = nova
            db_salvar(db)
            usuario["bio"] = nova
            print("\n  Bio atualizada!")
            pausar()

        elif op == 2:
            print("  Separe por virgula. Ex: Python, Games, UX")
            entrada = pegar("Interesses")
            lista = [i.strip() for i in entrada.split(",") if i.strip()]
            db = db_carregar()
            achar_usuario_id(db, usuario["id"])["interesses"] = lista
            db_salvar(db)
            usuario["interesses"] = lista
            print("\n  Interesses atualizados!")
            pausar()

        elif op == 3:
            cabecalho("Meus Eventos")
            db = db_carregar()
            ids = usuario.get("eventos_inscritos", [])
            if not ids:
                print("\n  Nenhum evento inscrito ainda.")
            else:
                for eid in ids:
                    ev = achar_evento(db, eid)
                    if ev:
                        print(f"\n  * {ev['nome']} — {ev['data']}")
            pausar()

        else:
            break


# ─────────────────────────────────────────
#  TURMA
# ─────────────────────────────────────────


def tela_turma(usuario):
    while True:
        db = db_carregar()
        turma = achar_turma(db, usuario["curso"], usuario["ano"])
        cabecalho(f"Turma: {turma['curso']} - {turma['ano']}o ano")
        print()
        op = menu(
            [
                "Ver membros",
                "Ver feed",
                "Publicar post",
                "Ver eventos da turma",
                "Criar evento",
                "Voltar",
            ]
        )

        if op == 1:
            cabecalho("Membros")
            if not turma["membros"]:
                print("\n  Nenhum membro ainda.")
            else:
                for uid in turma["membros"]:
                    u = achar_usuario_id(db, uid)
                    if u:
                        inter = (
                            f" | {', '.join(u['interesses'])}"
                            if u["interesses"]
                            else ""
                        )
                        print(f"  * {u['nome']}{inter}")
            pausar()

        elif op == 2:
            cabecalho("Feed da Turma")
            posts = turma.get("posts", [])
            if not posts:
                print("\n  Nenhum post ainda.")
            else:
                for p in reversed(posts[-15:]):
                    autor = achar_usuario_id(db, p["autor_id"])
                    nome_autor = autor["nome"] if autor else "?"
                    print(f"\n  {nome_autor} [{p['data']}]")
                    print(f"  {p['conteudo']}")
                    print("  " + "-" * 40)
            pausar()

        elif op == 3:
            cabecalho("Publicar Post")
            texto = pegar("Seu post")
            if len(texto) > 500:
                print("\n  Post muito longo (max 500 caracteres).")
            else:
                turma["posts"].append(
                    {
                        "id": str(uuid.uuid4()),
                        "autor_id": usuario["id"],
                        "conteudo": texto,
                        "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    }
                )
                db_salvar(db)
                print("\n  Post publicado!")
            pausar()

        elif op == 4:
            cabecalho("Eventos da Turma")
            eventos = [e for e in db["eventos"] if e["turma_id"] == turma["id"]]
            if not eventos:
                print("\n  Nenhum evento ainda.")
            else:
                for e in eventos:
                    cond = e["condicoes"]
                    rest = "Aberto" if cond["aberto"] else "Restrito"
                    print(f"\n  [{e['id'][:6]}] {e['nome']} — {e['data']}")
                    print(f"  {e['descricao']}")
                    print(f"  Acesso: {rest} | {len(e['participantes'])} inscrito(s)")
            pausar()

        elif op == 5:
            tela_criar_evento(usuario)

        else:
            break


def tela_criar_evento(usuario):

    cabecalho("Criar Evento")
    nome = pegar("Nome do evento")
    data = pegar("Data (DD/MM/AAAA)")
    descricao = pegar("Descricao")

    # Valida data
    try:
        datetime.strptime(data, "%d/%m/%Y")
    except ValueError:
        print("\n Data invalida. Use DD/MM/AAAA.")
        pausar()
        return

    print("\n Quem pode participar?")
    tipo = menu(["Aberto para todos", "So alunos do meu curso", "So minha turma"])

    aberto = False
    cursos_perm = []

    if tipo == 1:
        aberto = True
    elif tipo == 2:
        cursos_perm = [usuario["curso"]]
    # tipo 3 = lista vazia = so turma

    db = db_carregar()
    turma = achar_turma(db, usuario["curso"], usuario["ano"])
    eid = str(uuid.uuid4())
    evento = {
        "id": eid,
        "turma_id": turma["id"],
        "criado_por": usuario["id"],
        "nome": nome,
        "data": data,
        "descricao": descricao,
        "condicoes": {
            "aberto": aberto,
            "cursos_permitidos": cursos_perm,
        },
        "participantes": [usuario["id"]],
    }

    db["eventos"].append(evento)

    u = achar_usuario_id(db, usuario["id"])
    u["eventos_inscritos"].append(eid)
    usuario["eventos_inscritos"].append(eid)

    db_salvar(db)

    print(f"\n Evento '{nome}' criado!")

    pausar()


# ─────────────────────────────────────────
#  EXPLORAR
# ─────────────────────────────────────────


def tela_explorar(usuario):
    while True:
        cabecalho("Explorar FiaPals")
        print()
        op = menu(
            [
                "Ver todas as turmas",
                "Ver todos os eventos",
                "Entrar em um evento",
                "Voltar",
            ]
        )

        if op == 1:
            cabecalho("Turmas")
            db = db_carregar()
            curso_atual = ""
            for t in db["turmas"]:
                if t["curso"] != curso_atual:
                    curso_atual = t["curso"]
                    print(f"\n  {curso_atual}")
                print(f"    {t['ano']}o ano — {len(t['membros'])} aluno(s)")
            pausar()

        elif op == 2:
            cabecalho("Eventos")
            db = db_carregar()
            if not db["eventos"]:
                print("\n  Nenhum evento criado ainda.")
            else:
                for e in db["eventos"]:
                    t = next(
                        (x for x in db["turmas"] if x["id"] == e["turma_id"]), None
                    )
                    turma_nome = f"{t['curso']} {t['ano']}o ano" if t else "?"
                    rest = "Aberto" if e["condicoes"]["aberto"] else "Restrito"
                    print(f"\n  [{e['id'][:6]}] {e['nome']} — {e['data']}")
                    print(
                        f"  Turma: {turma_nome} | {rest} | {len(e['participantes'])} inscrito(s)"
                    )
                    print(f"  {e['descricao']}")
            pausar()

        elif op == 3:
            tela_inscrever(usuario)

        else:
            break


def tela_inscrever(usuario):
    cabecalho("Inscrever em Evento")
    db = db_carregar()
    if not db["eventos"]:
        print("\n  Nenhum evento disponivel.")
        pausar()
        return

    for e in db["eventos"]:
        rest = "Aberto" if e["condicoes"]["aberto"] else "Restrito"
        print(f"  [{e['id'][:6]}] {e['nome']} — {e['data']} | {rest}")

    print()
    codigo = pegar("Digite os 6 primeiros caracteres do ID")
    evento = next((e for e in db["eventos"] if e["id"].startswith(codigo)), None)

    if not evento:
        print("\n  Evento nao encontrado.")
        pausar()
        return

    if usuario["id"] in evento["participantes"]:
        print("\n  Voce ja esta inscrito neste evento.")
        pausar()
        return

    # Valida condicoes
    cond = evento["condicoes"]
    if not cond["aberto"]:
        if (
            cond["cursos_permitidos"]
            and usuario["curso"] not in cond["cursos_permitidos"]
        ):
            print(
                f"\n  Este evento e restrito ao curso: {', '.join(cond['cursos_permitidos'])}"
            )
            pausar()
            return

    confirma = (
        input(f"\n  Confirmar inscricao em '{evento['nome']}'? (s/n): ").strip().lower()
    )
    if confirma == "s":
        evento["participantes"].append(usuario["id"])
        u = achar_usuario_id(db, usuario["id"])
        u["eventos_inscritos"].append(evento["id"])
        usuario["eventos_inscritos"].append(evento["id"])
        db_salvar(db)
        print("\n  Inscricao confirmada!")
    else:
        print("\n  Cancelado.")
    pausar()


# ─────────────────────────────────────────
#  MENU PRINCIPAL
# ─────────────────────────────────────────


def menu_principal(usuario):
    while True:
        cabecalho(f"Ola, {usuario['nome']}")
        print(f"  {usuario['curso']} - {usuario['ano']}o ano\n")
        op = menu(["Meu Perfil", "Minha Turma", "Explorar", "Sair"])
        if op == 1:
            tela_perfil(usuario)
        elif op == 2:
            tela_turma(usuario)
        elif op == 3:
            tela_explorar(usuario)
        else:
            break


# ─────────────────────────────────────────
#  INICIO
# ─────────────────────────────────────────


def main():
    while True:
        cabecalho()
        print("\n  Bem-vindo(a) ao FiaPals!\n")
        op = menu(["Login", "Criar conta", "Sair"])
        if op == 1:
            usuario = fazer_login()
            if usuario:
                menu_principal(usuario)
        elif op == 2:
            cadastrar()
        else:
            print("\n  Ate logo!\n")
            break


if __name__ == "__main__":
    main()
