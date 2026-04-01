"""
FiaPals - Backend Flask
Execute: pip install flask flask-cors && python app.py
Acesse:  http://localhost:5000
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import json, os, hashlib, uuid
from datetime import datetime
from werkzeug.utils import secure_filename

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_MB      = 8

app = Flask(__name__)
app.secret_key = "fiapals-secret-key-2024"
app.config["MAX_CONTENT_LENGTH"] = MAX_MB * 1024 * 1024
CORS(app, supports_credentials=True)

DB_PATH = os.path.join(BASE_DIR, "fiapals_db.json")

CURSOS = [
    "Engenharia de Software", "Engenharia da Computacao",
    "Ciencia da Computacao", "Sistemas de Informacao",
    "Design Digital", "Analise e Desenvolvimento de Sistemas",
    "Inteligencia Artificial", "Ciberseguranca",
]
ANOS = [1, 2, 3, 4]

# ── DB ──────────────────────────────────────────────

# ===== FUNÇÃO: db_carregar =====
def db_carregar():
    if not os.path.exists(DB_PATH):
        db = {"usuarios": [], "turmas": [], "eventos": []}
        for curso in CURSOS:
            for ano in ANOS:
                db["turmas"].append({
                    "id": f"{curso.lower().replace(' ', '-')}-{ano}ano",
                    "curso": curso, "ano": ano, "membros": [], "posts": []
                })
        db_salvar(db)
        return db
    with open(DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# ===== FUNÇÃO: db_salvar =====
def db_salvar(db):
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)


# ===== FUNÇÃO: hash_senha =====
def hash_senha(s):
    return hashlib.sha256(s.encode()).hexdigest()


# ===== FUNÇÃO: achar_usuario =====
def achar_usuario(db, email):
    return next((u for u in db["usuarios"] if u["email"].lower() == email.lower()), None)


# ===== FUNÇÃO: achar_usuario_id =====
def achar_usuario_id(db, uid):
    return next((u for u in db["usuarios"] if u["id"] == uid), None)


# ===== FUNÇÃO: achar_turma =====
def achar_turma(db, curso, ano):
    tid = f"{curso.lower().replace(' ', '-')}-{ano}ano"
    return next((t for t in db["turmas"] if t["id"] == tid), None)

# ===== FUNÇÃO: achar_evento =====
def achar_evento(db, evento_id):
    return next((e for e in db["eventos"] if e["id"] == evento_id), None)


# ===== FUNÇÃO: usuario_logado =====
def usuario_logado():
    uid = session.get("usuario_id")
    if not uid:
        return None
    db = db_carregar()
    return achar_usuario_id(db, uid)


# ===== FUNÇÃO: allowed =====
def allowed(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


# ===== FUNÇÃO: _pub =====
def _pub(u):
    return {k: v for k, v in u.items() if k != "senha_hash"}


# ===== FUNÇÃO: _serializar_evento =====
def _serializar_evento(e, uid, db):
    turma = next((t for t in db["turmas"] if t["id"] == e["turma_id"]), None)
    cond  = e.get("condicoes", {})
    vagas = cond.get("vagas")
    confirmados = len(e.get("confirmados", []))
    return {
        "id": e["id"],
        "nome": e["nome"],
        "data": e["data"],
        "descricao": e["descricao"],
        "turma_nome": f"{turma['curso']} {turma['ano']}º ano" if turma else "?",
        "aberto": cond.get("aberto", True),
        "cursos_permitidos": cond.get("cursos_permitidos", []),
        "total_participantes": len(e["participantes"]),
        "inscrito": uid in e["participantes"],
        "pendente": uid in e.get("pendentes", []),
        "pagamento": cond.get("pagamento"),
        "vagas": vagas,
        "vagas_disponiveis": (vagas - confirmados) if vagas else None,
        "idade_minima": cond.get("idade_minima"),
        "requer_confirmacao": cond.get("requer_confirmacao", False),
        "criado_por": e.get("criado_por"),
        "pendentes_lista": e.get("pendentes", []) if e.get("criado_por") == uid else [],
    }

# ── SERVE STATIC ────────────────────────────────────


# ===== FUNÇÃO: index =====
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "index.html")

# ===== FUNÇÃO: uploaded_file =====
@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

# ── AUTH ────────────────────────────────────────────


# ===== FUNÇÃO: cadastrar =====
@app.route("/api/cadastrar", methods=["POST"])
def cadastrar():
    data  = request.json
    nome  = data.get("nome", "").strip()
    email = data.get("email", "").strip()
    senha = data.get("senha", "")
    curso = data.get("curso", "")
    ano   = data.get("ano")
    if not all([nome, email, senha, curso, ano]):
        return jsonify({"erro": "Preencha todos os campos."}), 400
    if len(senha) < 4:
        return jsonify({"erro": "Senha muito curta (mínimo 4 caracteres)."}), 400
    if curso not in CURSOS:
        return jsonify({"erro": "Curso inválido."}), 400
    if int(ano) not in ANOS:
        return jsonify({"erro": "Ano inválido."}), 400
    db = db_carregar()
    if achar_usuario(db, email):
        return jsonify({"erro": "E-mail já cadastrado."}), 400
    uid = str(uuid.uuid4())
    usuario = {
        "id": uid, "nome": nome, "email": email.lower(),
        "senha_hash": hash_senha(senha), "curso": curso, "ano": int(ano),
        "bio": "", "interesses": [], "eventos_inscritos": [], "seguindo": []
    }
    db["usuarios"].append(usuario)
    turma = achar_turma(db, curso, int(ano))
    if turma:
        turma["membros"].append(uid)
    db_salvar(db)
    session["usuario_id"] = uid
    return jsonify({"usuario": _pub(usuario)}), 201


# ===== FUNÇÃO: login =====
@app.route("/api/login", methods=["POST"])
def login():
    data  = request.json
    email = data.get("email", "").strip()
    senha = data.get("senha", "")
    db    = db_carregar()
    u     = achar_usuario(db, email)
    if not u or u["senha_hash"] != hash_senha(senha):
        return jsonify({"erro": "E-mail ou senha incorretos."}), 401
    session["usuario_id"] = u["id"]
    return jsonify({"usuario": _pub(u)})


# ===== FUNÇÃO: logout =====
@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


# ===== FUNÇÃO: me =====
@app.route("/api/me")
def me():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    return jsonify({"usuario": _pub(u)})

# ── PERFIL ──────────────────────────────────────────


# ===== FUNÇÃO: atualizar_perfil =====
@app.route("/api/perfil", methods=["PUT"])
def atualizar_perfil():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    data = request.json
    db   = db_carregar()
    usr  = achar_usuario_id(db, u["id"])
    if "bio" in data:
        usr["bio"] = data["bio"].strip()
    if "interesses" in data:
        usr["interesses"] = [i.strip() for i in data["interesses"] if i.strip()]
    db_salvar(db)
    return jsonify({"usuario": _pub(usr)})

# ===== FUNÇÃO: meus_posts =====
@app.route("/api/perfil/posts")
def meus_posts():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db = db_carregar()
    resultado = []
    for turma in db["turmas"]:
        for p in turma.get("posts", []):
            if p["autor_id"] == u["id"]:
                resultado.append({
                    **p,
                    "autor_nome": u["nome"],
                    "turma_nome": f"{turma['curso']} {turma['ano']}º ano"
                })
    resultado.sort(key=lambda x: x["data"], reverse=True)
    return jsonify({"posts": resultado[:30]})

# ── SEGUIR ──────────────────────────────────────────


# ===== FUNÇÃO: seguir =====
@app.route("/api/seguir/<alvo_id>", methods=["POST"])
def seguir(alvo_id):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    if u["id"] == alvo_id:
        return jsonify({"erro": "Você não pode seguir a si mesmo."}), 400
    db  = db_carregar()
    usr = achar_usuario_id(db, u["id"])
    if alvo_id not in usr.get("seguindo", []):
        usr.setdefault("seguindo", []).append(alvo_id)
        db_salvar(db)
    return jsonify({"ok": True, "seguindo": True})


# ===== FUNÇÃO: deixar_seguir =====
@app.route("/api/seguir/<alvo_id>", methods=["DELETE"])
def deixar_seguir(alvo_id):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db  = db_carregar()
    usr = achar_usuario_id(db, u["id"])
    usr["seguindo"] = [x for x in usr.get("seguindo", []) if x != alvo_id]
    db_salvar(db)
    return jsonify({"ok": True, "seguindo": False})

# ── FEED GERAL (pessoas que sigo) ───────────────────


# ===== FUNÇÃO: feed_geral =====
@app.route("/api/feed/geral")
def feed_geral():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db       = db_carregar()
    seguindo = set(u.get("seguindo", []))
    resultado = []
    for turma in db["turmas"]:
        for p in turma.get("posts", []):
            if p["autor_id"] in seguindo:
                autor = achar_usuario_id(db, p["autor_id"])
                resultado.append({
                    **p,
                    "autor_nome": autor["nome"] if autor else "?",
                    "turma_nome": f"{turma['curso']} {turma['ano']}º ano"
                })
    resultado.sort(key=lambda x: x["data"], reverse=True)
    return jsonify({"posts": resultado[:40]})

# ── TURMA ───────────────────────────────────────────


# ===== FUNÇÃO: minha_turma =====
@app.route("/api/turma")
def minha_turma():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db    = db_carregar()
    turma = achar_turma(db, u["curso"], u["ano"])
    if not turma:
        return jsonify({"erro": "Turma não encontrada."}), 404
    membros = [_pub(achar_usuario_id(db, mid)) for mid in turma["membros"] if achar_usuario_id(db, mid)]
    return jsonify({
        "id": turma["id"], "curso": turma["curso"], "ano": turma["ano"],
        "membros": membros, "total_posts": len(turma.get("posts", []))
    })


# ===== FUNÇÃO: feed_turma =====
@app.route("/api/turma/feed")
def feed_turma():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db    = db_carregar()
    turma = achar_turma(db, u["curso"], u["ano"])
    posts = list(reversed(turma.get("posts", [])[-40:]))
    resultado = []
    for p in posts:
        autor = achar_usuario_id(db, p["autor_id"])
        resultado.append({
            "id": p["id"],
            "conteudo": p.get("conteudo", ""),
            "foto_url": p.get("foto_url"),
            "data": p["data"],
            "autor_nome": autor["nome"] if autor else "?",
            "autor_id": p["autor_id"],
        })
    return jsonify({"posts": resultado})

# ===== FUNÇÃO: novo_post =====
@app.route("/api/turma/post", methods=["POST"])
def novo_post():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401

    foto_url = None
    texto    = ""

    if request.content_type and "multipart" in request.content_type:
        texto = request.form.get("conteudo", "").strip()
        if "foto" in request.files:
            f = request.files["foto"]
            if f and f.filename and allowed(f.filename):
                ext  = f.filename.rsplit(".", 1)[1].lower()
                nome = f"{uuid.uuid4().hex}.{ext}"
                f.save(os.path.join(UPLOAD_DIR, nome))
                foto_url = f"/uploads/{nome}"
    else:
        data  = request.json or {}
        texto = data.get("conteudo", "").strip()

    if not texto and not foto_url:
        return jsonify({"erro": "Post vazio."}), 400
    if len(texto) > 500:
        return jsonify({"erro": "Post muito longo (máximo 500 caracteres)."}), 400

    db = db_carregar()
    # Recarrega usuário do banco para garantir dados frescos
    u = achar_usuario_id(db, u["id"])
    if not u:
        return jsonify({"erro": "Usuário não encontrado."}), 404

    turma = achar_turma(db, u["curso"], u["ano"])
    if not turma:
        tid = f"{u['curso'].lower().replace(' ', '-')}-{u['ano']}ano"
        turma = {"id": tid, "curso": u["curso"], "ano": u["ano"], "membros": [u["id"]], "posts": []}
        db["turmas"].append(turma)

    post = {
        "id": str(uuid.uuid4()), "autor_id": u["id"],
        "conteudo": texto, "foto_url": foto_url,
        "data": datetime.now().strftime("%d/%m/%Y %H:%M")
    }
    turma["posts"].append(post)
    db_salvar(db)
    return jsonify({"post": {**post, "autor_nome": u["nome"]}}), 201

# ── EVENTOS ─────────────────────────────────────────


# ===== FUNÇÃO: usuario_pode_ver =====
def usuario_pode_ver(evento, u, db):
    """Retorna True se o usuário tem permissão de ver/acessar este evento."""
    cond = evento.get("condicoes", {})
    if cond.get("aberto", True):
        return True
    cursos_perm = cond.get("cursos_permitidos", [])
    if cursos_perm:
        return u["curso"] in cursos_perm
    turma_ev = next((t for t in db["turmas"] if t["id"] == evento["turma_id"]), None)
    if turma_ev:
        return u["id"] in turma_ev["membros"]
    return False


# ===== FUNÇÃO: listar_eventos =====
@app.route("/api/eventos")
def listar_eventos():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db = db_carregar()
    visiveis = [e for e in db["eventos"] if usuario_pode_ver(e, u, db)]
    return jsonify({"eventos": [_serializar_evento(e, u["id"], db) for e in visiveis]})


# ===== FUNÇÃO: eventos_turma =====
@app.route("/api/turma/eventos")
def eventos_turma():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db    = db_carregar()
    turma = achar_turma(db, u["curso"], u["ano"])
    evs   = [e for e in db["eventos"] if e["turma_id"] == turma["id"] and usuario_pode_ver(e, u, db)]
    return jsonify({"eventos": [_serializar_evento(e, u["id"], db) for e in evs]})


# ===== FUNÇÃO: criar_evento =====
@app.route("/api/eventos/criar", methods=["POST"])
def criar_evento():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    data      = request.json
    nome      = data.get("nome", "").strip()
    data_ev   = data.get("data", "").strip()
    descricao = data.get("descricao", "").strip()
    tipo      = data.get("tipo", "aberto")

    if not all([nome, data_ev, descricao]):
        return jsonify({"erro": "Preencha os campos obrigatórios."}), 400
    try:
        datetime.strptime(data_ev, "%d/%m/%Y")
    except ValueError:
        return jsonify({"erro": "Data inválida. Use DD/MM/AAAA."}), 400

    def opt_num(key, cast):
        v = data.get(key)
        if v in (None, "", 0, "0"): return None
        try: return cast(v)
        except: return None

    pagamento          = opt_num("pagamento", float)
    vagas              = opt_num("vagas", int)
    idade_minima       = opt_num("idade_minima", int)
    requer_confirmacao = bool(data.get("requer_confirmacao", False))

    db    = db_carregar()
    turma = achar_turma(db, u["curso"], u["ano"])
    eid   = str(uuid.uuid4())

    evento = {
        "id": eid, "turma_id": turma["id"], "criado_por": u["id"],
        "nome": nome, "data": data_ev, "descricao": descricao,
        "condicoes": {
            "aberto": tipo == "aberto",
            "cursos_permitidos": [u["curso"]] if tipo == "curso" else [],
            "pagamento": pagamento,
            "vagas": vagas,
            "idade_minima": idade_minima,
            "requer_confirmacao": requer_confirmacao,
        },
        "participantes": [u["id"]],
        "pendentes": [],
        "confirmados": [u["id"]],
    }
    db["eventos"].append(evento)
    usr = achar_usuario_id(db, u["id"])
    usr.setdefault("eventos_inscritos", []).append(eid)
    db_salvar(db)
    return jsonify({"evento": _serializar_evento(evento, u["id"], db)}), 201

# ===== FUNÇÃO: inscrever =====
@app.route("/api/eventos/<evento_id>/inscrever", methods=["POST"])
def inscrever(evento_id):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db     = db_carregar()
    evento = achar_evento(db, evento_id)
    if not evento:
        return jsonify({"erro": "Evento não encontrado."}), 404
    if u["id"] in evento["participantes"] or u["id"] in evento.get("pendentes", []):
        return jsonify({"erro": "Você já está inscrito ou com inscrição pendente."}), 400

    cond = evento.get("condicoes", {})

    if cond.get("vagas"):
        if len(evento.get("confirmados", [])) >= cond["vagas"]:
            return jsonify({"erro": "Sem vagas disponíveis."}), 400

    if not cond.get("aberto", True):
        if cond.get("cursos_permitidos") and u["curso"] not in cond["cursos_permitidos"]:
            return jsonify({"erro": f"Restrito ao curso: {', '.join(cond['cursos_permitidos'])}."}), 403
        if not cond.get("cursos_permitidos"):
            turma_ev = next((t for t in db["turmas"] if t["id"] == evento["turma_id"]), None)
            if turma_ev and u["id"] not in turma_ev["membros"]:
                return jsonify({"erro": "Evento restrito à turma criadora."}), 403

    evento["participantes"].append(u["id"])
    usr = achar_usuario_id(db, u["id"])
    usr.setdefault("eventos_inscritos", []).append(evento_id)

    if cond.get("requer_confirmacao"):
        evento.setdefault("pendentes", []).append(u["id"])
        db_salvar(db)
        return jsonify({"ok": True, "pendente": True, "msg": "Inscrição enviada! Aguardando confirmação."})
    else:
        evento.setdefault("confirmados", []).append(u["id"])
        db_salvar(db)
        return jsonify({"ok": True, "pendente": False, "msg": "Inscrição confirmada!"})


# ===== FUNÇÃO: listar_pendentes =====
@app.route("/api/eventos/<evento_id>/pendentes")
def listar_pendentes(evento_id):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db     = db_carregar()
    evento = achar_evento(db, evento_id)
    if not evento or evento.get("criado_por") != u["id"]:
        return jsonify({"erro": "Não autorizado."}), 403
    pendentes = [_pub(achar_usuario_id(db, pid)) for pid in evento.get("pendentes", []) if achar_usuario_id(db, pid)]
    return jsonify({"pendentes": pendentes})


# ===== FUNÇÃO: confirmar_participante =====
@app.route("/api/eventos/<evento_id>/confirmar/<uid_alvo>", methods=["POST"])
def confirmar_participante(evento_id, uid_alvo):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db     = db_carregar()
    evento = achar_evento(db, evento_id)
    if not evento or evento.get("criado_por") != u["id"]:
        return jsonify({"erro": "Não autorizado."}), 403
    if uid_alvo not in evento.get("pendentes", []):
        return jsonify({"erro": "Participante não encontrado nos pendentes."}), 404
    evento["pendentes"].remove(uid_alvo)
    evento.setdefault("confirmados", []).append(uid_alvo)
    db_salvar(db)
    return jsonify({"ok": True})

# ── EXPLORAR ────────────────────────────────────────


# ===== FUNÇÃO: listar_turmas =====
@app.route("/api/turmas")
def listar_turmas():
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db = db_carregar()
    return jsonify({"turmas": [
        {"id": t["id"], "curso": t["curso"], "ano": t["ano"], "total_membros": len(t["membros"])}
        for t in db["turmas"]
    ]})


# ===== FUNÇÃO: get_usuario =====
@app.route("/api/usuario/<uid>")
def get_usuario(uid):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db = db_carregar()
    alvo = achar_usuario_id(db, uid)
    if not alvo:
        return jsonify({"erro": "Usuário não encontrado."}), 404
    return jsonify({"usuario": _pub(alvo)})


# ===== FUNÇÃO: membros_da_turma =====
@app.route("/api/turmas/<turma_id>/membros")
def membros_da_turma(turma_id):
    u = usuario_logado()
    if not u:
        return jsonify({"erro": "Não autenticado."}), 401
    db = db_carregar()
    turma = next((t for t in db["turmas"] if t["id"] == turma_id), None)
    if not turma:
        return jsonify({"erro": "Turma não encontrada."}), 404
    membros = [_pub(achar_usuario_id(db, mid)) for mid in turma["membros"] if achar_usuario_id(db, mid)]
    return jsonify({"curso": turma["curso"], "ano": turma["ano"], "membros": membros})

# ===== BLOCO PRINCIPAL =====
if __name__ == "__main__":
    print(f"\n  FiaPals rodando em http://localhost:5000")
    print(f"  Uploads salvos em: {UPLOAD_DIR}\n")
    app.run(debug=True, port=5000)

