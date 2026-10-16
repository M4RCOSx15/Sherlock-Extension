# -*- coding: utf-8 -*-
"""Local regression checks for visible overlay detection; no network access."""
from __future__ import annotations

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import async_playwright

from backend.analyzer import analyze, compute_score, rules_count
from backend.scraper import (
    collect_visible_consent_choices,
    collect_visible_overlay_evidence,
)


async def main() -> None:
    assert rules_count() == 7, f"Esperadas 7 regras registradas, recebido {rules_count()}"
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        try:
            page = await browser.new_page(viewport={"width": 1280, "height": 720})

            # A skip link and a non-modal dialog are not blocking overlays.
            await page.set_content("""
              <a href="#main" style="position:absolute;left:-10000px;top:0">
                Pular para o conteúdo
              </a>
              <main id="main">Página neutra</main>
              <div role="dialog">Comentar</div>
            """)
            neutral = await collect_visible_overlay_evidence(page)
            assert neutral == [], f"Página neutra gerou sinal: {neutral!r}"
            assert not any(
                finding.id == "dark_overlay"
                for finding in analyze(await page.content(), "Página neutra")
            )
            print("[OK] página neutra e dialog não modal não geram finding")

            # An open, visible modal is reported with literal visible copy.
            await page.set_content("""
              <main>Oferta da loja</main>
              <div role="dialog" aria-modal="true"
                   style="position:fixed;inset:0;z-index:9999;background:#000b">
                <section style="margin:12vh auto;width:50%;background:white;padding:24px">
                  <h2>Confirme sua escolha</h2>
                  <button>Continuar</button>
                </section>
              </div>
            """)
            modal = await collect_visible_overlay_evidence(page)
            assert modal and "Confirme sua escolha" in modal[0], (
                f"Modal visível não foi reconhecido: {modal!r}"
            )
            findings = analyze(await page.content(), "Oferta da loja", modal)
            overlay_findings = [item for item in findings if item.id == "dark_overlay"]
            assert len(overlay_findings) == 1, f"Esperado um finding: {findings!r}"
            assert "Confirme sua escolha" in overlay_findings[0].evidence
            print("[OK] modal visível gera finding com evidência literal")

            # Hidden modal markup must not be treated as visible evidence.
            await page.set_content("""
              <div role="dialog" aria-modal="true" style="display:none">
                Conteúdo de modal oculto
              </div>
            """)
            hidden = await collect_visible_overlay_evidence(page)
            assert hidden == [], f"Modal oculto gerou sinal: {hidden!r}"
            print("[OK] modal oculto não gera finding")

            # A visible cookie banner with equally styled accept/reject actions
            # is not scored just because the banner exists.
            await page.set_content("""
              <style>
                .cookie-banner { position:fixed;left:0;right:0;bottom:0;height:180px;
                  z-index:1000;background:#111;padding:16px;box-sizing:border-box; }
                .cookie-banner button { background:#167a52;color:white;font-weight:700;
                  border:1px solid #167a52;padding:12px 18px; }
              </style>
              <div class="cookie-banner">
                <p>Usamos cookies para melhorar sua experiência.</p>
                <button>Aceitar todos os cookies</button>
                <button>Rejeitar todos os cookies</button>
              </div>
            """)
            cookie_overlay = await collect_visible_overlay_evidence(page)
            cookie_choices = await collect_visible_consent_choices(page)
            balanced = analyze(
                await page.content(),
                await page.locator("body").inner_text(),
                cookie_overlay,
                cookie_choices,
            )
            assert not any(item.id in {"dark_overlay", "consent_asymmetry"} for item in balanced), (
                f"Banner equilibrado gerou achado: {balanced!r}"
            )
            assert compute_score(balanced) == 0, f"Banner equilibrado alterou o score: {balanced!r}"
            print("[OK] banner equilibrado não eleva o score")

            # If accepting is available but refusing is missing from the first
            # layer, report a low-severity signal with the visible labels.
            await page.set_content("""
              <style>
                .cookie-consent { position:fixed;left:0;right:0;bottom:0;height:180px;
                  z-index:1000;background:#111;padding:16px;box-sizing:border-box; }
                .accept { background:#167a52;color:white;font-weight:700;
                  border:1px solid #167a52;padding:14px 18px; }
              </style>
              <div class="cookie-consent">
                <p>Usamos cookies para melhorar sua experiência.</p>
                <button class="accept">Aceitar todos os cookies</button>
                <a href="#settings">Configurações</a>
              </div>
            """)
            cookie_overlay = await collect_visible_overlay_evidence(page)
            cookie_choices = await collect_visible_consent_choices(page)
            asymmetric = analyze(
                await page.content(),
                await page.locator("body").inner_text(),
                cookie_overlay,
                cookie_choices,
            )
            consent_findings = [item for item in asymmetric if item.id == "consent_asymmetry"]
            assert not any(item.id == "dark_overlay" for item in asymmetric), (
                f"Banner foi reportado apenas pela presença: {asymmetric!r}"
            )
            assert len(consent_findings) == 1 and "Aceitar todos os cookies" in consent_findings[0].evidence
            assert "Configurações" in consent_findings[0].evidence
            assert consent_findings[0].severity == "low"
            assert compute_score(asymmetric) == 5, f"Sinal de consentimento não teve peso baixo: {asymmetric!r}"
            print("[OK] aceitar sem recusa direta gera apenas sinal heurístico leve")

            # When both actions exist, a filled accept button against an
            # unstyled reject link is a visible prominence imbalance.
            await page.set_content("""
              <style>
                .cookie-banner { position:fixed;left:0;right:0;bottom:0;height:180px;
                  z-index:1000;background:#111;padding:16px;box-sizing:border-box; }
                .accept { background:#167a52;color:white;font-weight:700;
                  border:1px solid #167a52;padding:14px 18px; }
                .reject { background:transparent;color:white;font-weight:400;
                  border:0;padding:4px; }
              </style>
              <div class="cookie-banner">
                <p>Usamos cookies para melhorar sua experiência.</p>
                <button class="accept">Aceitar todos</button>
                <a class="reject" role="button" href="#">Rejeitar todos</a>
              </div>
            """)
            cookie_overlay = await collect_visible_overlay_evidence(page)
            cookie_choices = await collect_visible_consent_choices(page)
            prominence = analyze(
                await page.content(),
                await page.locator("body").inner_text(),
                cookie_overlay,
                cookie_choices,
            )
            assert any(item.id == "consent_asymmetry" for item in prominence), (
                f"Assimetria visual não reconhecida: {prominence!r}"
            )
            print("[OK] diferença de destaque entre aceitar e rejeitar é sinalizada")
        finally:
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
