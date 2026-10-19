"""
Regressões do histórico anônimo (modelo A — microsprint de persistência).

Cobre: cookie de identidade, gravação automática no scan, isolamento
entre donos, remoção unitária/total, retenção e resiliência a falha
de banco. Sem rede: fetch_page é substituído por um stub e as rotas
são exercitadas com objetos Request/Response do Starlette.
"""

import asyncio
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_tmpdir = tempfile.mkdtemp(prefix="rastro-history-")
os.environ["RASTRO_DB_PATH"] = os.path.join(_tmpdir, "test.db")

from fastapi import HTTPException, Request, Response  # noqa: E402

from backend import db, main  # noqa: E402
from backend.scraper import PageData  # noqa: E402

_RESULTS = []
_PASSED = 0


def check(name, condition, extra=""):
    global _PASSED
    if condition:
        _PASSED += 1
        _RESULTS.append(f"  [OK] {name}")
    else:
        _RESULTS.append(f"  [FALHOU] {name} {extra}")


def make_request(path, cookies=None):
    headers = []
    if cookies:
        headers.append((b"cookie", f"{db.COOKIE_NAME}={cookies}".encode()))
    return Request({
        "type": "http", "method": "GET", "path": path,
        "query_string": b"", "headers": headers,
    })


class _LLMResult:
    findings = []
    status = "disabled"
    unavailable_reason = None


async def _fake_fetch_page(url):
    return PageData(
        url=url,
        final_url="https://exemplo.com/pagina",
        title="Exemplo",
        html="<html><body><p>Restam 3 unidades em estoque</p></body></html>",
        text_content="Restam 3 unidades em estoque",
        status_code=200,
        duration_ms=120,
        dom_element_count=7,
        rendered_text_evidence=["Restam 3 unidades em estoque"],
    )


async def _fake_llm(**kwargs):
    return _LLMResult()


def _set_cookie_value(response):
    header = response.headers.get("set-cookie", "")
    for part in header.split(";"):
        part = part.strip()
        if part.startswith(f"{db.COOKIE_NAME}="):
            return part.split("=", 1)[1]
    return None


def run_tests():
    main.fetch_page = _fake_fetch_page
    main.analyze_semantically = _fake_llm

    # 1. Primeira requisição sem cookie → identidade gerada e emitida
    response = Response()
    result = main.get_history(make_request("/api/history"), response)
    check("history vazia retorna items=[]", result["items"] == [])
    owner_a = _set_cookie_value(response)
    check("cookie de identidade é emitido", db.is_owner_token(owner_a))
    check("cookie é HttpOnly e SameSite=Lax",
          "httponly" in response.headers.get("set-cookie", "").lower()
          and "samesite=lax" in response.headers.get("set-cookie", "").lower())

    # 2. Scan bem-sucedido grava resumo automaticamente
    scan_res = asyncio.run(main.scan_url(
        main.ScanRequest(url="https://exemplo.com/pagina"),
        make_request("/api/scan", cookies=owner_a), Response(),
    ))
    check("scan retorna formato inalterado", scan_res.status == "ok")
    items = main.get_history(make_request("/api/history", cookies=owner_a), Response())["items"]
    check("scan aparece no histórico", len(items) == 1)
    item = items[0] if items else {}
    check("resumo guarda domínio final", item.get("domain") == "exemplo.com")
    check("resumo guarda domínio solicitado", item.get("requestedDomain") == "exemplo.com")
    check("resumo guarda metadados",
          item.get("riskLevel") in ("low", "medium", "high", "critical")
          and item.get("domElementsScanned") == 7)
    check("resumo não guarda URL completa", "url" not in item)
    check("id do item é gerado pelo servidor",
          isinstance(item.get("id"), str) and len(item["id"]) == 32)

    # 3. Outro navegador (outra identidade) não vê o histórico
    owner_b = db.new_owner_token()
    other_items = main.get_history(make_request("/api/history", cookies=owner_b), Response())["items"]
    check("histórico é isolado por identidade", other_items == [])

    # 4. Remoção de item de outro dono retorna 404
    item_id = items[0]["id"]
    try:
        main.delete_history_item(item_id, make_request("/api/history/x", cookies=owner_b), Response())
        check("remover item alheio retorna 404", False, "não levantou exceção")
    except HTTPException as exc:
        check("remover item alheio retorna 404",
              exc.status_code == 404 and exc.detail["code"] == "HISTORY_NOT_FOUND")

    # 5. Remoção do próprio item funciona
    main.delete_history_item(item_id, make_request("/api/history/x", cookies=owner_a), Response())
    check("item removido some da lista",
          main.get_history(make_request("/api/history", cookies=owner_a), Response())["items"] == [])

    # 6. Apagar tudo limpa só o histórico do dono
    for _ in range(2):
        asyncio.run(main.scan_url(
            main.ScanRequest(url="https://exemplo.com/pagina"),
            make_request("/api/scan", cookies=owner_a), Response(),
        ))
    db.add_history_item(owner_b, {"domain": "outro.com", "score": 1, "riskLevel": "low"})
    main.clear_history(make_request("/api/history", cookies=owner_a), Response())
    check("limpeza esvazia o histórico do dono",
          main.get_history(make_request("/api/history", cookies=owner_a), Response())["items"] == [])
    check("limpeza não toca o histórico alheio",
          len(main.get_history(make_request("/api/history", cookies=owner_b), Response())["items"]) == 1)

    # 7. Retenção: nunca mais que HISTORY_LIMIT itens por dono
    for i in range(db.HISTORY_LIMIT + 5):
        db.add_history_item(owner_b, {"domain": f"site{i}.com", "score": 1, "riskLevel": "low"})
    check(f"retenção mantém {db.HISTORY_LIMIT} itens",
          len(db.list_history(owner_b)) == db.HISTORY_LIMIT)
    check("retenção preserva os mais recentes",
          db.list_history(owner_b)[0]["domain"] == f"site{db.HISTORY_LIMIT + 4}.com")

    # 8. Falha de banco não derruba o scan
    original_path = os.environ["RASTRO_DB_PATH"]
    # test.db é um arquivo — usá-lo como diretório faz a conexão falhar.
    os.environ["RASTRO_DB_PATH"] = os.path.join(_tmpdir, "test.db", "sub", "x.db")
    res = asyncio.run(main.scan_url(
        main.ScanRequest(url="https://exemplo.com/pagina"),
        make_request("/api/scan", cookies=owner_a), Response(),
    ))
    os.environ["RASTRO_DB_PATH"] = original_path
    check("scan sobrevive a falha de banco", res.status == "ok")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    db.init_db()
    try:
        run_tests()
    except Exception:
        for line in _RESULTS:
            print(line)
        raise
    for line in _RESULTS:
        print(line)
    print(f"\nResultado: {_PASSED}/{len(_RESULTS)} passaram")
    if _PASSED != len(_RESULTS):
        sys.exit(1)
    print("Todos os testes PASSARAM.")
