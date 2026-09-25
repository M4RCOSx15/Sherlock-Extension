# -*- coding: utf-8 -*-
"""
RASTRO — Testes da blindagem anti-SSRF (Sprint 7)
Roda sem pytest: python backend/test_ssrf.py

Verifica que:
  - URLs públicas passam
  - IPs privados/reservados são bloqueados
  - Hostnames internos são bloqueados
  - Sufixos de TLD reservados são bloqueados
  - Metadados de cloud são bloqueados
"""
from __future__ import annotations

import io
import sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# Ajusta path para rodar da raiz do projeto
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.security import SSRFError, check_ssrf

# ── Helpers ───────────────────────────────────────────────────

passed = 0
failed = 0


def expect_pass(url: str) -> None:
    """Espera que check_ssrf NÃO levante exceção."""
    global passed, failed
    try:
        check_ssrf(url)
        print(f"  [OK] PASS   {url}")
        passed += 1
    except SSRFError as exc:
        print(f"  [FALHA] PASS esperado mas BLOQUEOU ({exc.code}): {url}")
        failed += 1
    except Exception as exc:
        print(f"  [FALHA] Erro inesperado: {exc!r}")
        failed += 1


def expect_block(url: str, expected_code: str | None = None) -> None:
    """Espera que check_ssrf levante SSRFError."""
    global passed, failed
    try:
        check_ssrf(url)
        print(f"  [FALHA] BLOCK esperado mas PASSOU: {url}")
        failed += 1
    except SSRFError as exc:
        code_ok = (expected_code is None) or (exc.code == expected_code)
        if code_ok:
            tag = f"({exc.code})"
            print(f"  [OK] BLOCK {tag} {url}")
            passed += 1
        else:
            print(f"  [FALHA] Código errado: esperado={expected_code} recebido={exc.code} | {url}")
            failed += 1


# ── Casos de teste ─────────────────────────────────────────────

print("\n=== Casos que DEVEM PASSAR (URL pública) ===")
expect_pass("https://www.google.com")
expect_pass("https://github.com/trending")
expect_pass("https://loja.mercadolivre.com.br/checkout")
expect_pass("https://www.wikipedia.org")

print("\n=== IPs Privados / Loopback (devem BLOQUEAR) ===")
expect_block("http://127.0.0.1",       "SSRF_BLOCKED_IP")
expect_block("http://127.0.0.1:8080",  "SSRF_BLOCKED_IP")
expect_block("http://10.0.0.1",        "SSRF_BLOCKED_IP")
expect_block("http://10.10.20.30",     "SSRF_BLOCKED_IP")
expect_block("http://172.16.0.1",      "SSRF_BLOCKED_IP")
expect_block("http://172.31.255.255",  "SSRF_BLOCKED_IP")
expect_block("http://192.168.1.1",     "SSRF_BLOCKED_IP")
expect_block("http://192.168.0.100",   "SSRF_BLOCKED_IP")
expect_block("http://0.0.0.0",         "SSRF_BLOCKED_IP")
expect_block("http://255.255.255.255", "SSRF_BLOCKED_IP")

print("\n=== Metadata Endpoints de Cloud (devem BLOQUEAR) ===")
expect_block("http://169.254.169.254",                            "SSRF_BLOCKED_IP")
expect_block("http://169.254.169.254/latest/meta-data/",          "SSRF_BLOCKED_IP")
expect_block("http://metadata.google.internal/computeMetadata/",  "SSRF_BLOCKED_HOSTNAME")

print("\n=== Hostnames Internos Exatos (devem BLOQUEAR) ===")
expect_block("http://localhost",       "SSRF_BLOCKED_HOSTNAME")
expect_block("http://localhost:3000",  "SSRF_BLOCKED_HOSTNAME")
expect_block("http://localhost/admin", "SSRF_BLOCKED_HOSTNAME")

print("\n=== Sufixos de TLD Internos (devem BLOQUEAR) ===")
expect_block("http://meuservidor.local",    "SSRF_BLOCKED_HOSTNAME")
expect_block("http://api.internal",        "SSRF_BLOCKED_HOSTNAME")
expect_block("http://erp.corp",            "SSRF_BLOCKED_HOSTNAME")
expect_block("http://roteador.lan",        "SSRF_BLOCKED_HOSTNAME")
expect_block("http://exemplo.test",        "SSRF_BLOCKED_HOSTNAME")
expect_block("http://teste.localhost",     "SSRF_BLOCKED_HOSTNAME")

print("\n=== IPv6 Privados (devem BLOQUEAR) ===")
expect_block("http://[::1]",            "SSRF_BLOCKED_IP")
expect_block("http://[::1]:8080",       "SSRF_BLOCKED_IP")
expect_block("http://[fc00::1]",        "SSRF_BLOCKED_IP")
expect_block("http://[fe80::1]",        "SSRF_BLOCKED_IP")

# ── Resumo ────────────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*50}")
print(f"Resultado: {passed}/{total} passaram")
if failed:
    print(f"FALHAS:    {failed}/{total}")
    sys.exit(1)
else:
    print("Todos os testes PASSARAM.")
    sys.exit(0)
