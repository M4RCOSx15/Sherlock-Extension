# -*- coding: utf-8 -*-
"""Validação local das microsprints 14.16–14.23; não faz chamadas de rede.

Cobre os casos descritos em docs/antigravity/MICROSPRINTS.md:
  - 14.16: timer só gera urgência alta quando visível e com valor temporal.
  - 14.17: pré-seleção exige checkbox marcado + rótulo visível de marketing.
  - 14.18: chamadas vagas são urgência; escassez exige quantidade/estoque.
  - 14.19: escassez usa somente texto renderizado (inclusive abaixo da dobra).
  - 14.20: confirmshaming usa a mesma lista renderizada (links inclusos).
  - 14.21: ancoragem exige elemento de preço antigo renderizado.
  - 14.22: texto estacionado fora da tela não alimenta nenhuma regra.
  - 14.23: urgência textual usa candidatos renderizados, não o innerText cru.

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
    collect_rendered_price_contexts,
    collect_rendered_text_candidates,
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
        await collect_rendered_text_candidates(page),
        await collect_rendered_price_contexts(page),
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

            # ── 14.20: confirmshaming também usa só texto renderizado ──
            await page.set_content("""
              <main>
                <div style="height:5000px"></div>
                <a href="#">Não, obrigado</a>
              </main>
            """)
            findings = await analyze_page(page)
            shaming = [f for f in findings if f.id == "confirmshaming"]
            assert len(shaming) == 1, (
                f"Recusa renderizada abaixo da dobra não gerou achado: {findings!r}"
            )
            print("[OK] 14.20 recusa renderizada abaixo da dobra gera achado")

            for descricao, html in (
                ("display:none", '<a href="#" style="display:none">Não, obrigado</a>'),
                ("visibility:hidden",
                 '<a href="#" style="visibility:hidden">Não, obrigado</a>'),
                ("atributo hidden", '<a href="#" hidden>Não, obrigado</a>'),
                ("aria-hidden em ancestral",
                 '<div aria-hidden="true"><a href="#">Não, obrigado</a></div>'),
            ):
                await page.set_content(f"<main>{html}</main>")
                findings = await analyze_page(page)
                assert "confirmshaming" not in ids(findings), (
                    f"Recusa oculta por {descricao} gerou achado: {findings!r}"
                )
            print("[OK] 14.20 recusa oculta não gera achado")

            await page.set_content("""
              <main>
                <a href="#" style="display:none">Não, prefiro perder</a>
                <a href="#">Não, obrigado</a>
              </main>
            """)
            findings = await analyze_page(page)
            shaming = [f for f in findings if f.id == "confirmshaming"]
            assert shaming and "prefiro perder" not in shaming[0].evidence.casefold(), (
                f"Evidência citou recusa oculta: {findings!r}"
            )
            print("[OK] 14.20 evidência ignora o trecho oculto na mesma página")

            # ── 14.21: ancoragem só considera preço antigo renderizado ──
            await page.set_content("""
              <main>
                <div style="height:5000px"></div>
                <div><del>R$ 99,90</del> R$ 79,90</div>
              </main>
            """)
            findings = await analyze_page(page)
            anchoring = [f for f in findings if f.id == "price_anchoring"]
            assert len(anchoring) == 1, (
                f"Preço antigo renderizado abaixo da dobra não gerou achado: {findings!r}"
            )
            print("[OK] 14.21 preço antigo renderizado abaixo da dobra gera achado")

            for descricao, html in (
                ("display:none",
                 '<div style="display:none"><del>R$ 99,90</del> R$ 79,90</div>'),
                ("visibility:hidden",
                 '<div style="visibility:hidden"><del>R$ 99,90</del> R$ 79,90</div>'),
                ("aria-hidden em ancestral",
                 '<div aria-hidden="true"><del>R$ 99,90</del> R$ 79,90</div>'),
                ("del oculto com preço atual visível",
                 '<span style="display:none"><del>R$ 99,90</del></span>'
                 '<p>R$ 79,90</p>'),
            ):
                await page.set_content(f"<main>{html}</main>")
                findings = await analyze_page(page)
                assert "price_anchoring" not in ids(findings), (
                    f"Preço antigo oculto por {descricao} gerou achado: {findings!r}"
                )
            print("[OK] 14.21 preço antigo oculto não gera achado")

            # Regressão 14.13: mesmo valor repetido não é ancoragem.
            await page.set_content(
                "<main><div><del>R$ 79,99</del> R$ 79,99</div></main>"
            )
            findings = await analyze_page(page)
            assert "price_anchoring" not in ids(findings), (
                f"Mesmo valor repetido gerou ancoragem: {findings!r}"
            )
            print("[OK] 14.21 mesmo valor repetido continua sem achado")

            # ── 14.22: texto estacionado fora da tela não gera achado ──
            for descricao, html, regra in (
                ("escassez à esquerda da tela",
                 '<p style="position:absolute;left:-9999px">Restam 2 unidades</p>',
                 "fake_scarcity"),
                ("escassez acima da tela",
                 '<p style="position:absolute;top:-9999px">Restam 2 unidades</p>',
                 "fake_scarcity"),
                ("recusa fora da tela",
                 '<a href="#" style="position:absolute;left:-9999px">Não, obrigado</a>',
                 "confirmshaming"),
                ("preço antigo fora da tela",
                 '<div style="position:absolute;left:-9999px">'
                 '<del>R$ 99,90</del> R$ 79,90</div>',
                 "price_anchoring"),
            ):
                await page.set_content(f"<main>{html}</main>")
                findings = await analyze_page(page)
                assert regra not in ids(findings), (
                    f"Texto fora da tela gerou {regra}: {findings!r}"
                )
            print("[OK] 14.22 texto totalmente fora da tela não gera achado")

            # Parcialmente visível continua elegível.
            await page.set_content("""
              <main>
                <p style="position:absolute;left:-50px;width:200px">
                  Restam 2 unidades
                </p>
              </main>
            """)
            findings = await analyze_page(page)
            assert "fake_scarcity" in ids(findings), (
                f"Texto parcialmente visível ignorado: {findings!r}"
            )
            print("[OK] 14.22 texto parcialmente visível continua elegível")

            # ── 14.23: urgência textual também exige texto renderizado ──
            await page.set_content("""
              <main>
                <p>Página neutra</p>
                <p style="position:absolute;left:-9999px">Corra!</p>
              </main>
            """)
            findings = await analyze_page(page)
            assert "fake_urgency" not in ids(findings), (
                f"Urgência fora da tela gerou achado: {findings!r}"
            )
            print("[OK] 14.23 urgência fora da tela não gera achado")

            await page.set_content("""
              <main>
                <p>Página neutra</p>
                <p style="display:none">Corra!</p>
              </main>
            """)
            findings = await analyze_page(page)
            assert "fake_urgency" not in ids(findings), (
                f"Urgência oculta gerou achado: {findings!r}"
            )
            print("[OK] 14.23 urgência oculta não gera achado")

            await page.set_content("""
              <main><p>Corra para aproveitar!</p></main>
            """)
            findings = await analyze_page(page)
            urgency = [f for f in findings if f.id == "fake_urgency"]
            assert len(urgency) == 1 and urgency[0].severity == "medium", (
                f"Urgência renderizada não gerou achado médio: {findings!r}"
            )
            print("[OK] 14.23 urgência renderizada continua gerando achado médio")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
