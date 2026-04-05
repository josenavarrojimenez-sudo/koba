#!/usr/bin/env python3
import os, time, json, hashlib, re
from datetime import datetime

DOCUMENT_DIR = "/root/.hermes/document_cache/"
STATE_FILE = "/root/.hermes/watcher_state.json"
LOG_FILE = "/root/.hermes/agent_watcher.log"
WORKSPACES_DIR = "/root/koba/workspaces/"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"processed": {}}

def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def log(msg):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{ts}] {msg}"
    with open(LOG_FILE, "a") as f:
        f.write(entry + "\n")
    print(entry)

def file_hash(fp):
    h = hashlib.md5()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def classify(fn):
    ext = fn.rsplit(".", 1)[-1].lower() if "." in fn else ""
    lo = fn.lower()
    if ext == "pdf":
        if any(w in lo for w in ["plano", "blueprint"]):
            return {"type": "plano_construccion", "workflow": "estimating", "priority": "high"}
        return {"type": "documento_pdf", "workflow": "document-analysis", "priority": "medium"}
    elif ext == "xlsx":
        if "presupuesto" in lo:
            return {"type": "presupuesto", "workflow": "budget-analysis", "priority": "high"}
        if "rendimiento" in lo:
            return {"type": "rendimientos", "workflow": "update-yields", "priority": "medium"}
        return {"type": "spreadsheet", "workflow": "analyze-data", "priority": "medium"}
    elif ext in ["docx", "doc"]:
        if "contrato" in lo:
            return {"type": "contrato", "workflow": "contract-review", "priority": "high"}
        return {"type": "documento", "workflow": "document-analysis", "priority": "medium"}
    return {"type": "otro", "workflow": "identify", "priority": "low"}

def clean_name(fn):
    return re.sub(r'[^a-zA-Z0-9_]', '_', fn.rsplit(".", 1)[0])[:50] + "_" + datetime.now().strftime("%Y%m%d%H%M%S")

def create_workspace(fn, cls):
    wdir = os.path.join(WORKSPACES_DIR, clean_name(fn))
    os.makedirs(os.path.join(wdir, "data"), exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    templates = {
        "00_WORKFLOW.md": f"# Workflow: {cls['type']}\n\nFuente: {fn}\nTipo: {cls['type']} | Workflow: {cls['workflow']} | Prioridad: {cls['priority']}\nDetectado: {now}\n\n## Pipeline\n1. [ ] Leer y clasificar\n2. [ ] Extraer datos\n3. [ ] Cargar rendimientos + precios\n4. [ ] Calcular cantidades\n5. [ ] Generar Excel\n6. [ ] Validar y entregar\n\nAgente: Apolo\n",
        "TASKS.md": f"# Tareas - {fn[:40]}\n\n## Fase 1: Lectura\n- [ ] Leer archivo\n- [ ] Identificar estructura\n- [ ] Extraer datos\n\n## Fase 2: Calculo\n- [ ] Cargar rendimientos_db.json\n- [ ] Cargar precios\n- [ ] Calcular cantidades\n\n## Fase 3: Entregables\n- [ ] Excel Detallado\n- [ ] Lista materiales\n- [ ] Resumen Business Central\n",
        "OUTPUT.md": f"# Resumen\n**Archivo:** {fn}\n**Tipo:** {cls['type']}\n**Estado:** En proceso\n",
        "NOTES.md": f"# Notas\n- {now}: Detectado {fn}\n- {now}: Workspace creado\n",
    }
    for n, c in templates.items():
        with open(os.path.join(wdir, n), "w", encoding="utf-8") as f:
            f.write(c)
    return wdir

def main():
    log("KOBA WATCHER v2 INICIADO")
    state = load_state()
    os.makedirs(DOCUMENT_DIR, exist_ok=True)
    os.makedirs(WORKSPACES_DIR, exist_ok=True)
    while True:
        try:
            for fn in os.listdir(DOCUMENT_DIR):
                if fn.startswith("doc_") or fn.startswith("."):
                    continue
                fp = os.path.join(DOCUMENT_DIR, fn)
                if not os.path.isfile(fp):
                    continue
                ch = file_hash(fp)
                proc = state.get("processed", {})
                if fn not in proc or proc[fn].get("hash") != ch:
                    cls = classify(fn)
                    log(f" NUEVO: {fn} -> {cls['type']}")
                    ws = create_workspace(fn, cls)
                    proc[fn] = {"hash": ch, "cls": cls, "ws": ws, "at": datetime.now().isoformat()}
                    state["processed"] = proc
                    save_state(state)
            time.sleep(30)
        except Exception as e:
            log(f"ERROR: {e}")
            time.sleep(60)

if __name__ == "__main__":
    main()
