# -*- coding: utf-8 -*-
"""
Script de smoke test para Sprint 6.
Sobe o servidor por 5 s, bate nos endpoints e exibe os resultados.
Rodar com: python backend/smoke_test.py
"""
import io
import sys
# Forçar UTF-8 no stdout do Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"

def get(path: str) -> dict:
    req = urllib.request.Request(f"{BASE}{path}")
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())

def post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BASE}{path}", data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())

def main() -> None:
    # Sobe o servidor em background
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", "8000"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print("Aguardando servidor subir...")
    time.sleep(3)

    ok = True
    try:
        # 1. Health check
        h = get("/api/health")
        assert h["status"] == "ok", f"health: status inesperado: {h}"
        assert "version" in h, "health: falta version"
        print(f"[OK] GET /api/health → {h}")

        # 2. Scan stub com URL válida
        s = post("/api/scan", {"url": "https://exemplo.com"})
        assert s["status"] == "ok", f"scan: status inesperado: {s}"
        assert s["domain"] == "exemplo.com", f"scan: domain errado: {s['domain']}"
        assert isinstance(s["score"], int), "scan: score deve ser int"
        assert isinstance(s["findings"], list), "scan: findings deve ser lista"
        print(f"[OK] POST /api/scan (válida) → score={s['score']}, findings={len(s['findings'])}")

        # 3. URL inválida — deve retornar 422
        e = post("/api/scan", {"url": "nao-e-uma-url!!!"})
        assert e.get("detail") is not None, f"422: esperado detail, recebido: {e}"
        print(f"[OK] POST /api/scan (inválida) → 422 com detail")

        # 4. Docs acessível
        req = urllib.request.Request(f"{BASE}/docs")
        with urllib.request.urlopen(req, timeout=5) as r:
            assert r.status == 200
        print("[OK] GET /docs → Swagger UI disponível")

    except Exception as exc:
        print(f"[ERRO] {exc}")
        ok = False
    finally:
        proc.terminate()

    sys.exit(0 if ok else 1)

if __name__ == "__main__":
    main()
