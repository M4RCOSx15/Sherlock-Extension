# -*- coding: utf-8 -*-
"""Testes locais da barreira de requests do navegador; não faz chamadas de rede."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from backend.scraper import _guard_browser_request


@dataclass
class FakeRequest:
    url: str


class FakeRoute:
    def __init__(self) -> None:
        self.action: str | None = None

    async def abort(self, _reason: str | None = None) -> None:
        self.action = "abort"

    async def continue_(self) -> None:
        self.action = "continue"


def run_route(url: str) -> str | None:
    route = FakeRoute()
    asyncio.run(_guard_browser_request(route, FakeRequest(url)))
    return route.action


def main() -> None:
    cases = [
        ("http://127.0.0.1:8000/admin", "abort"),
        ("http://192.168.1.1/", "abort"),
        ("http://[::1]/", "abort"),
        ("file:///C:/Windows/win.ini", "abort"),
        ("https://8.8.8.8/page", "continue"),
        ("https://8.8.8.8/image.png", "abort"),
    ]

    for url, expected in cases:
        actual = run_route(url)
        assert actual == expected, f"{url}: esperado {expected}, recebido {actual}"
        print(f"[OK] {expected.upper()} {url}")

    print(f"Todos os {len(cases)} casos locais passaram.")


if __name__ == "__main__":
    main()
