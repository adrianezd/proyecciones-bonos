"""
Generador de esta pagina: la deuda publica a 10 años en la zona euro.

    python -m fuente.construir
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from . import datos
from .enlaces import HUB, MENU

AQUI = Path(__file__).parent
PROYECTO = AQUI.parent
SALIDA = PROYECTO / "docs"

BASE_URL = "https://adrianezd.github.io/proyecciones-bonos"

entorno = Environment(
    loader=FileSystemLoader(AQUI / "plantillas"),
    autoescape=select_autoescape(["html"]),
)

HOY = dt.date.today().isoformat()


def json_seguro(obj) -> str:
    texto = json.dumps(obj, ensure_ascii=False)
    return (texto
            .replace("<", "\\u003c")
            .replace(">", "\\u003e")
            .replace("&", "\\u0026")
            .replace(" ", "\\u2028")
            .replace(" ", "\\u2029"))


def escribir(plantilla: str, **contexto) -> None:
    destino = SALIDA / "index.html"
    destino.parent.mkdir(parents=True, exist_ok=True)

    contexto.setdefault("raiz", "./")
    contexto.setdefault("menu", MENU)
    contexto.setdefault("hub", HUB)
    contexto.setdefault("base_url", BASE_URL)
    contexto.setdefault("ruta", "")
    contexto.setdefault("generado", HOY)

    destino.write_text(entorno.get_template(plantilla).render(**contexto), encoding="utf-8")
    print("  escrito     index.html")


def main() -> None:
    print("Construyendo: bonos\n")

    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir(parents=True)
    shutil.copytree(PROYECTO / "estatico", SALIDA / "estatico")

    paises = {}
    for cod, nombre in datos.PAISES:
        serie = datos.bono_10a(cod)
        if len(serie) < 24:
            continue
        v = [x["v"] for x in serie]
        paso = max(1, len(serie) // 500)
        paises[cod] = {
            "nombre": nombre,
            "ultimo": round(v[-1], 3),
            "max": round(max(v), 3),
            "min": round(min(v), 3),
            "media": round(sum(v) / len(v), 3),
            "serie": serie[::paso],
        }

    if not paises:
        print("  SALTADA     bonos (el BCE no devolvio nada)")
        (SALIDA / ".nojekyll").write_text("", encoding="utf-8")
        return

    escribir(
        "bonos.html",
        acento="bonos",
        titulo="Deuda publica a 10 años en la zona euro",
        descripcion="Tipo del bono a diez años de España, Alemania, Italia y otros "
                    "países del euro, con la serie mensual del Banco Central Europeo.",
        paises=[(c, paises[c]["nombre"]) for c in paises],
        datos_json=json_seguro({"paises": paises}),
    )

    (SALIDA / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {BASE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    (SALIDA / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f'\n  <url><loc>{BASE_URL}/</loc><lastmod>{HOY}</lastmod></url>\n</urlset>\n',
        encoding="utf-8",
    )
    (SALIDA / ".nojekyll").write_text("", encoding="utf-8")

    print("\nListo.")


if __name__ == "__main__":
    main()
