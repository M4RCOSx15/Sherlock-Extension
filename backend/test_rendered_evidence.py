# -*- coding: utf-8 -*-
"""Validação local das microsprints 14.16–14.19; não faz chamadas de rede.

Cobre os casos pendentes descritos em docs/antigravity/MICROSPRINTS.md:
  - 14.16: timer só gera urgência alta quando visível e com valor temporal.
  - 14.17: pré-seleção exige checkbox marcado + rótulo visível de marketing.
  - 14.18: chamadas vagas são urgência; escassez exige quantidade/estoque.
  - 14.19: escassez usa somente texto renderizado (inclusive abaixo da dobra).

Rodar com: python backend/test_rendered_evidence.py
"""
from __future__ import annotations

import asyncio
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright

from backend.analyzer import analyze
from backend.scraper import (
    collect_rendered_scarcity_candidates,
    collect_visible_consent_choices,
    collect_visible_countdown_evidence,
    collect_visible_overlay_evidence,
    collect_visible_preselection_evidence,
)


async def analyze_page(page) -> list:
    """Reproduz o caminho da API: coleta evidências renderizadas e analisa."""
    return analyze(
        await page.content(),
        await page.locator("body").inner_text(),
        await collect_visible_overlay_evidence(page),
        await collect_visible_consent_choices(page),
        await collect_visible_countdown_evidence(page),
        await collect_visible_preselection_evidence(page),
        await collect_rendered_scarcity_candidates(page),
    )


def ids(findings) -> set[str]:
    return {finding.id for finding in findings}


async def main() -> None:
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 720})

            # ── 14.16: timer visível com valor temporal gera urgência alta ──
            await page.set_content("""
              <main>Oferta relâmpago</main>
              <div class="countdown">00:14:59</div>
            """)
            findings = await analyze_page(page)
            urgency = [f for f in findings if f.id == "fake_urgency"]
            assert len(urgency) == 1 and urgency[0].severity == "high", (
                f"Timer visível não gerou urgência alta: {findings!r}"
            )
            assert "00:14:59" in urgency[0].evidence
            print("[OK] 14.16 timer visível com valor temporal gera urgência alta")

            # Timer oculto não gera sinal.
            await page.set_content("""
              <main>Página neutra</main>
              <div class="countdown" style="display:none">00:14:59</div>
            """)
            findings = await analyze_page(page)
            assert "fake_urgency" not in ids(findings), (
                f"Timer oculto gerou achado: {findings!r}"
            )
            print("[OK] 14.16 timer oculto não gera achado")

            # Timer vazio não gera sinal.
            await page.set_content("""
              <main>Página neutra</main>
              <div class="countdown"></div>
            """)
            findings = await analyze_page(page)
            assert "fake_urgency" not in ids(findings), (
                f"Timer vazio gerou achado: {findings!r}"
            )
            print("[OK] 14.16 timer vazio não gera achado")

            # ── 14.17: checkbox de marketing pré-marcado gera achado ──
            await page.set_content("""
              <form>
                <label>
                  <input type="checkbox" checked>
                  Quero receber ofertas e promoções por e-mail
                </label>
              </form>
            """)
            findings = await analyze_page(page)
            preselection = [f for f in findings if f.id == "hidden_preselection"]
            assert len(preselection) == 1, (
                f"Checkbox de marketing pré-marcado não gerou achado: {findings!r}"
            )
            assert "ofertas" in preselection[0].evidence.casefold()
            print("[OK] 14.17 checkbox de marketing pré-marcado gera achado")

            # Checkbox comum marcado não é pré-seleção de marketing.
            await page.set_content("""
              <form>
                <label>
                  <input type="checkbox" checked>
                  Li e aceito os termos de uso
                </label>
              </form>
            """)
            findings = await analyze_page(page)
            assert "hidden_preselection" not in ids(findings), (
                f"Checkbox comum gerou achado de pré-seleção: {findings!r}"
            )
            print("[OK] 14.17 checkbox comum marcado não gera achado")

            # Checkbox de marketing desmarcado não gera achado.
            await page.set_content("""
              <form>
                <label>
                  <input type="checkbox">
                  Quero receber ofertas e promoções por e-mail
                </label>
              </form>
            """)
            findings = await analyze_page(page)
            assert "hidden_preselection" not in ids(findings), (
                f"Checkbox desmarcado gerou achado: {findings!r}"
            )
            print("[OK] 14.17 checkbox de marketing desmarcado não gera achado")

            # Checkbox marcado sem rótulo visível não gera achado.
            await page.set_content("""
              <form>
                <input type="checkbox" checked>
                <label style="display:none">
                  Quero receber ofertas e promoções por e-mail
                </label>
              </form>
            """)
            findings = await analyze_page(page)
            assert "hidden_preselection" not in ids(findings), (
                f"Checkbox sem rótulo visível gerou achado: {findings!r}"
            )
            print("[OK] 14.17 checkbox sem rótulo visível não gera achado")

            # ── 14.18: separação lexical entre urgência e escassez ──
            await page.set_content("<main><p>Acabando</p></main>")
            findings = await analyze_page(page)
            assert not findings, (
                f"'Acabando' isolado gerou achado: {findings!r}"
            )
            print("[OK] 14.18 'acabando' isolado não gera achado")

            await page.set_content("<main><p>Corra para aproveitar!</p></main>")
            findings = await analyze_page(page)
            urgency = [f for f in findings if f.id == "fake_urgency"]
            assert len(urgency) == 1 and urgency[0].severity == "medium", (
                f"'Corra' não gerou urgência média: {findings!r}"
            )
            assert "fake_scarcity" not in ids(findings)
            print("[OK] 14.18 chamada vaga vira urgência média, não escassez")

            for frase in ("Estoque acabando", "Restam 2 unidades"):
                await page.set_content(f"<main><p>{frase}</p></main>")
                findings = await analyze_page(page)
                scarcity = [f for f in findings if f.id == "fake_scarcity"]
                assert scarcity, (
                    f"'{frase}' não gerou achado de escassez: {findings!r}"
                )
            print("[OK] 14.18 quantidade/estoque explícito segue como escassez")

            # ── 14.19: escassez considera só texto renderizado ──
            await page.set_content("""
              <main>
                <div style="height:5000px"></div>
                <p>Restam 2 unidades</p>
              </main>
            """)
            findings = await analyze_page(page)
            assert "fake_scarcity" in ids(findings), (
                f"Escassez renderizada abaixo da dobra ignorada: {findings!r}"
            )
            print("[OK] 14.19 escassez abaixo da dobra continua elegível")

            for descricao, html in (
                ("display:none", '<p style="display:none">Restam 2 unidades</p>'),
                ("visibility:hidden", '<p style="visibility:hidden">Restam 2 unidades</p>'),
                ("atributo hidden", '<p hidden>Restam 2 unidades</p>'),
                ("aria-hidden em ancestral",
                 '<div aria-hidden="true"><p>Restam 2 unidades</p></div>'),
                ("opacidade quase zero",
                 '<p style="opacity:0.01">Restam 2 unidades</p>'),
            ):
                await page.set_content(f"<main>{html}</main>")
                findings = await analyze_page(page)
                assert "fake_scarcity" not in ids(findings), (
                    f"Escassez oculta por {descricao} gerou achado: {findings!r}"
                )
            print("[OK] 14.19 texto oculto por CSS/hidden/aria-hidden não gera achado")

            # Texto visível e oculto na mesma página: só o visível é citado.
            await page.set_content("""
              <main>
                <p style="display:none">Restam 9 unidades</p>
                <p>Restam 2 unidades</p>
              </main>
            """)
            findings = await analyze_page(page)
            scarcity = [f for f in findings if f.id == "fake_scarcity"]
            assert scarcity and "9 unidades" not in scarcity[0].evidence, (
                f"Evidência citou texto oculto: {findings!r}"
            )
            print("[OK] 14.19 evidência ignora o trecho oculto na mesma página")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
