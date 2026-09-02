"""
Descarga de los tipos de la deuda publica del Banco Central Europeo.

Se ejecuta en la GitHub Action, no en el navegador del visitante.
"""

from __future__ import annotations

import csv
import io
import json
from pathlib import Path

import httpx

CACHE = Path(__file__).parent.parent / "cache"
CACHE.mkdir(exist_ok=True)

CABECERAS = {
    "User-Agent": "proyecciones-bonos/1.0 (+https://github.com/adrianezd/proyecciones-bonos)",
    "Accept": "application/json, text/plain, */*",
}

# Dataflow IRS, "long-term interest rate for convergence purposes": el bono
# a 10 años de cada pais, publicado por el propio Banco Central Europeo.
BCE = "https://data-api.ecb.europa.eu/service/data"

PAISES = [
    ("ES", "España"), ("DE", "Alemania"), ("FR", "Francia"),
    ("IT", "Italia"), ("PT", "Portugal"), ("GR", "Grecia"),
    ("NL", "Países Bajos"), ("IE", "Irlanda"),
]


def bono_10a(pais: str) -> list[dict]:
    """Serie mensual del tipo del bono a 10 años de un pais del euro."""
    fichero = CACHE / f"bce-{pais}.json"

    try:
        r = httpx.get(f"{BCE}/IRS/M.{pais}.L.L40.CI.0000.EUR.N.Z",
                      params={"format": "csvdata"},
                      headers=CABECERAS, timeout=40.0, follow_redirects=True)
        r.raise_for_status()

        filas = []
        for fila in csv.DictReader(io.StringIO(r.text)):
            periodo, valor = fila.get("TIME_PERIOD"), fila.get("OBS_VALUE")
            if periodo and valor:
                try:
                    filas.append({"f": periodo, "v": float(valor)})
                except ValueError:
                    pass

        if len(filas) < 24:
            raise ValueError(f"solo {len(filas)} observaciones")

        fichero.write_text(json.dumps(filas), encoding="utf-8")
        print(f"  descargado  bono {pais} ({len(filas)} meses)")
        return filas

    except Exception as e:
        if fichero.exists():
            print(f"  CACHE       bono {pais}  ({type(e).__name__})")
            return json.loads(fichero.read_text(encoding="utf-8"))
        print(f"  FALLO       bono {pais}  ({e})")
        return []
