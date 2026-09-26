"""Rasgos de cada celda de un horario en Excel, para el modelo de celdas (B2) y el lector (B3).
Mismo codigo al entrenar y al leer: si cambia algo aqui, hay que volver a entrenar el modelo."""
import re
import unicodedata
from datetime import datetime, time

ETIQUETAS = ["dia", "hora", "nombre", "prueba", "otro"]
RE_DIA = re.compile(r"^[A-Z]{2,10},?\s*\d{1,2}$")
RE_HORA = re.compile(r"^\d{1,2}([:.]\d{2})?\s*H?(\s*-\s*\d{1,2}([:.]\d{2})?\s*H?)?$")
RE_CP = re.compile(r"\bCP\s*\d*\b|\bPRUEBA\b")  # marca de clase de prueba, delante, detras o en medio
RE_NUM = re.compile(r"^\d{1,2}\s*[.)]?-?\s*\S")
# Tipo de celda a simple vista (lo usan tambien los vecinos)
VACIA, DIA, HORA, CP, NUMERADO, TEXTO, NUMERO = range(7)


def limpiar(v):
    t = unicodedata.normalize("NFKD", str(v)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().upper()


def tipo(v):
    if v is None or (isinstance(v, str) and not v.strip()):
        return VACIA
    if isinstance(v, (time, datetime)):
        return HORA
    if isinstance(v, (int, float)):
        return NUMERO
    t = limpiar(v)
    if RE_DIA.match(t):
        return DIA
    if RE_HORA.match(t):
        return HORA
    if RE_CP.search(t):
        return CP
    return NUMERADO if RE_NUM.match(t) else TEXTO


def rasgos_hoja(ws):
    """Una fila por celda no vacia: (fila, col, valor, rasgos). ws es una hoja de openpyxl."""
    celdas = {(c.row, c.column): c.value for fila in ws.iter_rows() for c in fila
              if tipo(c.value) != VACIA}
    if not celdas:
        return []
    tipos = {k: tipo(v) for k, v in celdas.items()}
    col_min = min(c for _, c in celdas)
    por_fila = {}
    for (f, c), t in tipos.items():
        por_fila.setdefault(f, []).append(t)
    # Para cada fila: la ultima fila de horas y la ultima fila de dia por encima (o ella misma)
    ult_hora, ult_dia, h, d = {}, {}, None, None
    for f in range(1, max(por_fila) + 1):
        ts = por_fila.get(f, [])
        if ts.count(HORA) >= 2 or (HORA in ts and len(ts) <= 2):
            h = f
        if DIA in ts:
            d = f
        ult_hora[f], ult_dia[f] = h, d
    salida = []
    for (f, c), v in celdas.items():
        t = tipos[(f, c)]
        txt = limpiar(v) if isinstance(v, str) else ""
        ts = por_fila[f]
        fh, fd = ult_hora[f], ult_dia[f]
        r = {
            "tipo": t,
            "largo": len(txt),
            "palabras": len(txt.split()),
            "mayus": int(bool(txt) and str(v).strip().isupper()),
            "digitos": sum(ch.isdigit() for ch in txt),
            "empieza_num": int(txt[:1].isdigit()),
            "acaba_num": int(txt[-1:].isdigit()),
            "col_rel": c - col_min,
            "primera_col": int(c == col_min),
            "fila": f,
            "n_fila": len(ts),
            "horas_fila": ts.count(HORA),
            "dias_fila": ts.count(DIA),
            "textos_fila": ts.count(TEXTO) + ts.count(NUMERADO) + ts.count(CP),
            "dist_hora": f - fh if fh else -1,
            "dist_dia": f - fd if fd else -1,
            "hora_encima": int(bool(fh) and fh < f and tipos.get((fh, c)) == HORA),
            "hora_debajo": int(tipos.get((f + 1, c)) == HORA),
        }
        for nombre, (df, dc) in {"arriba": (-1, 0), "abajo": (1, 0), "izq": (0, -1), "der": (0, 1)}.items():
            r[nombre] = tipos.get((f + df, c + dc), VACIA)
        salida.append((f, c, v, r))
    return salida
