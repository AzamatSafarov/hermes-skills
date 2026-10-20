#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render_schema.py — движок скилла concept-schema-visualizer.

JSON-спека → HTML-страница с SVG-схемами (+ опциональный экспорт в
Obsidian Canvas и Excalidraw). Только stdlib, кроссплатформенно.

Спека (все поля необязательны, кроме schemas):

{
  "title": "...", "subtitle": "...", "footer": "...",
  "matrix": {"columns": ["..."], "rows": [{"label": "...", "cells": ["..."]}]},
  "schemas": [
    {"kind": "graph", "title": "...", "note": "...",
     "nodes": [{"id": "...", "grapheme": "object", "label": "...", "note": "...",
                "layer": 0, "slot": 0, "emphasis": false, "epistemic": "source",
                "marker": null, "badge": "A"}],
     "edges": [{"from": "...", "to": "...", "type": "action", "label": "...",
                "basis": "...", "dashed": false}],
     "frames": [{"id": "...", "kind": "context", "label": "...", "members": ["..."]}]},
    {"kind": "map", "title": "...", "xLabel": "...", "yLabel": "...",
     "items": [{"label": "...", "x": -0.8, "y": 0.2, "emphasis": false}]},
    {"kind": "timeline", "title": "...", "points": [{"label": "...", "t": 0.3}]}
  ]
}

Графемы (nodes): object, place, position, condition, event, process, plane, focus, term
Типы связей (edges): action, link, control, shift, tension
Рамки (frames): context (L-рамка), constraint (П-рамка), group (пунктир), boundary (линия)
Эпистемика: source | reconstruction | interpretation | norm
"""

import argparse
import html
import json
import math
import random
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ----------------------------------------------------------------------------
# Константы визуального языка
# ----------------------------------------------------------------------------

ACCENT = "#8b5cf6"

GRAPHEMES = {"object", "place", "position", "condition", "event",
             "process", "plane", "focus", "term"}
EDGE_TYPES = {"action", "link", "control", "shift", "tension"}
FRAME_KINDS = {"context", "constraint", "group", "boundary"}
EPISTEMIC = {"source", "reconstruction", "interpretation", "norm"}

GLYPH_NAMES = {
    "object": ("Объект", "сущность, понятие, документ, тезис"),
    "place": ("Место", "среда, поле, состояние, локус"),
    "position": ("Позиция", "агент, участник, точка зрения"),
    "condition": ("Условие", "«если/то», проверка, развилка"),
    "event": ("Событие", "значимый факт, инцидент, решение"),
    "process": ("Процесс", "процедура, механизм, цикл"),
    "plane": ("Плоскость", "уровень или слой анализа"),
    "focus": ("Смысловой фокус", "ядро смысла, центральная идея"),
    "term": ("Имя графемы", "термин, условное обозначение"),
    "action": ("Действие", "переход, влияние, порождение"),
    "link": ("Связь", "отношение без направления"),
    "control": ("Управляющее действие", "команда, регулирование, контроль"),
    "shift": ("Сдвижка", "перенос, смещение точки отсчёта"),
    "tension": ("Напряжение", "конфликт, спорность, несводимость"),
    "context": ("Контекст", "фон, среда, рамка обсуждения"),
    "constraint": ("Ограничение", "предел применимости, запрет"),
    "group": ("Группа", "объединение элементов"),
    "boundary": ("Граница", "раздел пространств"),
    "source": ("Утверждение источника", "прямая фиксация текста"),
    "reconstruction": ("Реконструкция", "восстановление смысла текста"),
    "interpretation": ("Интерпретация", "прочтение PNS, не буквальное"),
    "norm": ("Нормативное утверждение", "рекомендация, долженствование"),
}

CSS = """
.csv-root{font-family:inherit;color:var(--foreground,#2a2338);max-width:1060px}
.csv-title{font-size:20px;font-weight:650;margin:2px 0 2px 0;letter-spacing:.2px}
.csv-subtitle{font-size:13px;color:var(--muted-foreground,#6e6683);margin:0 0 18px 0}
.csv-schema{margin:0 0 26px 0}
.csv-schema h3{font-size:15px;font-weight:650;margin:0 0 4px 0}
.csv-schema .csv-note{font-size:12px;color:var(--muted-foreground,#6e6683);margin:0 0 10px 0}
.csv-schema svg{display:block;max-width:100%;height:auto}
.csv-root text{font-family:inherit}
.t-lab{font-size:13px;fill:var(--foreground,#2a2338);font-weight:500}
.t-note{font-size:11px;fill:var(--muted-foreground,#6e6683);font-weight:400}
.t-tiny{font-size:11px;fill:var(--muted-foreground,#6e6683)}
.t-ax{font-size:12px;fill:var(--muted-foreground,#6e6683)}
.t-chip{font-size:11px;fill:var(--muted-foreground,#5d5570)}
.t-frame{font-size:12px;fill:var(--muted-foreground,#6e6683);font-weight:600}
.n-shape{fill:rgba(139,92,246,0.10);stroke:var(--accent,#8b5cf6);stroke-width:1.6}
.n-emph{fill:rgba(139,92,246,0.22);stroke:var(--accent,#8b5cf6);stroke-width:2.2}
.e-line{fill:none;stroke:var(--accent,#8b5cf6);stroke-width:1.6}
.e-muted{fill:none;stroke:var(--muted-foreground,#6e6683);stroke-width:1.6}
.e-dash{stroke-dasharray:5 4}
.ep-interpretation{stroke-dasharray:5 4}
.ep-norm{stroke-width:2.4}
.ep-reconstruction{opacity:0.88}
.f-line{fill:none;stroke:var(--accent,#8b5cf6);stroke-width:1.4;opacity:0.75}
.f-dash{stroke-dasharray:6 5}
.chip-bg{fill:var(--card,#fbfaff);stroke:var(--border,#ddd5ee);stroke-width:1}
.csv-matrix{border-collapse:collapse;font-size:12px;margin:6px 0 24px 0;max-width:100%}
.csv-matrix th,.csv-matrix td{border:1px solid var(--border,#ddd5ee);padding:6px 10px;text-align:left;vertical-align:top}
.csv-matrix th{background:rgba(139,92,246,0.08);font-weight:600}
.csv-matrix td:first-child{font-weight:600}
.csv-legend{display:flex;flex-wrap:wrap;gap:8px 18px;margin:4px 0 8px 0;
  padding:10px 12px;border:1px solid var(--border,#ddd5ee);border-radius:10px;max-width:1060px}
.csv-legend .li{display:flex;align-items:center;gap:7px;font-size:11.5px;color:var(--muted-foreground,#6e6683)}
.csv-legend .li b{color:var(--foreground,#2a2338);font-weight:600}
.csv-footer{font-size:11px;color:var(--muted-foreground,#6e6683);margin-top:14px}
.csv-page{background:#faf9fe;padding:28px;min-height:100vh}
.csv-page .csv-root{margin:0 auto}
"""


def esc(s):
    return html.escape(str(s), quote=True)


def wrap_lines(text, max_px, fs):
    """Перенос по словам под расчётную ширину."""
    if text is None:
        return []
    text = str(text).strip()
    if not text:
        return []
    cw = 0.58 * fs
    max_chars = max(6, int(max_px / cw))
    lines = []
    for raw in text.split("\n"):
        words = raw.split()
        if not words:
            lines.append("")
            continue
        cur = words[0]
        for w in words[1:]:
            if len(cur) + 1 + len(w) <= max_chars:
                cur += " " + w
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_px(line, fs):
    return len(line) * 0.58 * fs


# ----------------------------------------------------------------------------
# Спека: загрузка и валидация
# ----------------------------------------------------------------------------

class SpecError(Exception):
    pass


class Checker:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def report(self, strict=False):
        for w in self.warnings:
            print("WARN: " + w, file=sys.stderr)
        for e in self.errors:
            print("ERROR: " + e, file=sys.stderr)
        if self.errors:
            return 2
        if strict and self.warnings:
            return 1
        return 0


def load_spec(path, chk):
    with open(path, "r", encoding="utf-8") as f:
        spec = json.load(f)
    if not isinstance(spec.get("schemas"), list) or not spec["schemas"]:
        raise SpecError("в спеке нет массива schemas")
    for si, sc in enumerate(spec["schemas"]):
        kind = sc.get("kind", "graph")
        prefix = f"schema[{si}]"
        if kind not in ("graph", "map", "timeline"):
            chk.error(f"{prefix}: неизвестный kind {kind!r}")
        if not sc.get("title"):
            chk.warn(f"{prefix}: нет title")
        if kind == "graph":
            ids = set()
            nodes = sc.get("nodes", [])
            edges = sc.get("edges", [])
            frames = sc.get("frames", [])
            if len(nodes) > 15:
                chk.warn(f"{prefix}: {len(nodes)} узлов > 15 — разбейте на пакет схем")
            for n in nodes:
                nid = n.get("id")
                if not nid:
                    chk.error(f"{prefix}: узел без id")
                    continue
                if nid in ids:
                    chk.error(f"{prefix}: повтор id {nid!r}")
                ids.add(nid)
                if n.get("grapheme") not in GRAPHEMES:
                    chk.error(f"{prefix}/{nid}: неизвестная графема {n.get('grapheme')!r}")
                if not n.get("label"):
                    chk.warn(f"{prefix}/{nid}: пустой label")
                if n.get("epistemic") and n["epistemic"] not in EPISTEMIC:
                    chk.error(f"{prefix}/{nid}: epistemic={n['epistemic']!r}")
            for e in edges:
                for end in ("from", "to"):
                    if e.get(end) not in ids and not any(
                            fr.get("id") == e.get(end) for fr in frames):
                        chk.error(f"{prefix}: ребро {e.get('from')}->{e.get('to')}: "
                                  f"{end} не существует")
                if e.get("type") not in EDGE_TYPES:
                    chk.error(f"{prefix}: тип связи {e.get('type')!r} неизвестен")
                if e.get("type") in ("action", "control", "shift") and not e.get("basis"):
                    chk.warn(f"{prefix}: причинная связь «{e.get('label') or e['type']}» "
                             f"без grounding-поля basis")
            for fr in frames:
                if fr.get("kind") not in FRAME_KINDS:
                    chk.error(f"{prefix}: рамка {fr.get('id')}: kind={fr.get('kind')!r}")
                for m in fr.get("members", []):
                    if m not in ids:
                        chk.error(f"{prefix}: рамка {fr.get('id')}: член {m!r} не существует")
                if not fr.get("members"):
                    chk.warn(f"{prefix}: рамка {fr.get('id')} без членов")
        elif kind == "map":
            if not sc.get("items"):
                chk.warn(f"{prefix}: карта без items")
            for it in sc.get("items", []):
                x, y = it.get("x", 0), it.get("y", 0)
                if not (-1 <= x <= 1 and -1 <= y <= 1):
                    chk.warn(f"{prefix}: item «{it.get('label')}» вне диапазона [-1,1]")
        elif kind == "timeline":
            if not sc.get("points"):
                chk.warn(f"{prefix}: ось времени без points")
    return spec


# ----------------------------------------------------------------------------
# Layout графа
# ----------------------------------------------------------------------------

LH_LABEL = 17
LH_NOTE = 14
GAPX = 96
GAPY = 26
MARGIN = 26
FRAME_PAD = 22


def measure_node(node):
    g = node["grapheme"]
    lab = wrap_lines(node.get("label"), 170, 13)
    note = wrap_lines(node.get("note"), 170, 11) if node.get("note") else []
    tw = max((text_px(l, 13) for l in lab), default=20)
    th = len(lab) * LH_LABEL + len(note) * LH_NOTE
    if g == "object":
        w, h = tw + 38, th + 26
    elif g == "place":
        w, h = tw * 1.18 + 34, th + 32
    elif g == "condition":
        w, h = (tw + 52) * 1.9, (th + 26) * 1.55
    elif g == "event":
        w, h = tw + 46, th + 32
    elif g == "process":
        w, h = tw * 1.45 + 42, th + 30
    elif g == "plane":
        w, h = tw + 50, th + 26
    elif g == "position":
        w, h = tw + 40, th + 56
    elif g == "focus":
        w, h = tw + 44, 30
    elif g == "term":
        w, h = tw + 52, 32
    else:
        w, h = tw + 38, th + 26
    return max(w, 92), max(h, 44), lab, note


def topo_layers(nodes, edges):
    """Явные layer из спеки — жёсткие; недостающие выводим из топологии."""
    known = {n["id"]: n["layer"] for n in nodes if n.get("layer") is not None}
    layer = dict(known)
    changed = True
    guard = 0
    while changed and guard < 200:
        changed = False
        guard += 1
        for e in edges:
            a, b = e.get("from"), e.get("to")
            la, lb = layer.get(a), layer.get(b)
            if la is not None and lb is None and b not in known:
                layer[b] = la + 1
                changed = True
            elif lb is not None and la is None and a not in known:
                layer[a] = max(lb - 1, 0)
                changed = True
    for n in nodes:
        if n["id"] not in layer:
            layer[n["id"]] = 0
    return layer


def layout_graph(sc):
    nodes = sc.get("nodes", [])
    edges = sc.get("edges", [])
    frames = sc.get("frames", [])
    layer_of = topo_layers(nodes, edges)
    cols = defaultdict(list)
    for i, n in enumerate(nodes):
        n2 = dict(n)
        n2["_i"] = i
        n2["_layer"] = layer_of[n["id"]]
        cols[n2["_layer"]].append(n2)
    flat = []
    for key in sorted(cols):
        col = sorted(cols[key], key=lambda n: (n.get("slot", 10**6), n["_i"]))
        flat.extend(col)
    nodes = flat

    boxes = {}
    maxw = {}
    for n in nodes:
        w, h, lab, note = measure_node(n)
        n["_w"], n["_h"], n["_lab"], n["_note"] = w, h, lab, note
        maxw[n["_layer"]] = max(maxw.get(n["_layer"], 0), w)
    x = MARGIN
    for key in sorted(maxw):
        for n in nodes:
            if n["_layer"] == key:
                n["_x"] = x + (maxw[key] - n["_w"]) / 2
        x += maxw[key] + GAPX
    W = x - GAPX + MARGIN

    # Вертикаль: колонки выравниваем по верху; H = max высота колонки.
    H = MARGIN
    for key in sorted(maxw):
        colh = sum(n["_h"] + GAPY for n in nodes if n["_layer"] == key) - GAPY + MARGIN
        H = max(H, colh)
    for key in sorted(maxw):
        yy = MARGIN
        for n in nodes:
            if n["_layer"] == key:
                n["_y"] = yy
                yy += n["_h"] + GAPY

    fb = {}
    for fr in frames:
        members = [n for n in nodes if n["id"] in fr.get("members", [])]
        if members:
            x0 = min(m["_x"] for m in members) - FRAME_PAD
            y0 = min(m["_y"] for m in members) - FRAME_PAD
            x1 = max(m["_x"] + m["_w"] for m in members) + FRAME_PAD
            y1 = max(m["_y"] + m["_h"] for m in members) + FRAME_PAD
            fb[fr["id"]] = (x0, y0, x1 - x0, y1 - y0)
            W = max(W, x1 + MARGIN)
            H = max(H, y1 + MARGIN)
    return nodes, edges, frames, fb, W, H


# ----------------------------------------------------------------------------
# Рисование графем
# ----------------------------------------------------------------------------

def ep_class(n):
    e = n.get("epistemic", "source")
    if e == "interpretation":
        return " n-shape ep-interpretation"
    if e == "norm":
        return " n-shape ep-norm"
    if e == "reconstruction":
        return " n-shape ep-reconstruction"
    return " n-shape"


def cls_for(n):
    base = ep_class(n)
    if n.get("emphasis"):
        return "n-emph" + (" ep-interpretation" if n.get("epistemic") == "interpretation" else "")
    return base


def text_block(cx, cy, lab, note):
    total = len(lab) * LH_LABEL + len(note) * LH_NOTE
    y0 = cy - total / 2 + LH_LABEL * 0.78
    out = []
    for l in lab:
        out.append(f'<text class="t-lab" x="{cx:.1f}" y="{y0:.1f}" text-anchor="middle">{esc(l)}</text>')
        y0 += LH_LABEL
    for l in note:
        out.append(f'<text class="t-note" x="{cx:.1f}" y="{y0:.1f}" text-anchor="middle">{esc(l)}</text>')
        y0 += LH_NOTE
    return "".join(out)


def marker_glyph(n, x, y, w):
    m = n.get("marker")
    if not m:
        return ""
    mx, my = x + w - 2, y + 4
    if m == "star":
        return (f'<text x="{mx}" y="{my}" font-size="13" fill="{ACCENT}" '
                f'text-anchor="middle">&#10033;</text>')
    if m == "hash":
        return (f'<text x="{mx}" y="{my}" font-size="12" font-weight="700" fill="{ACCENT}" '
                f'text-anchor="middle">#</text>')
    return ""


def draw_node(n, sid):
    g = n["grapheme"]
    x, y, w, h = n["_x"], n["_y"], n["_w"], n["_h"]
    cx, cy = x + w / 2, y + h / 2
    c = cls_for(n)
    out = []
    if g == "object":
        out.append(f'<rect class="{c}" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="8"/>')
        out.append(text_block(cx, cy, n["_lab"], n["_note"]))
    elif g == "place":
        out.append(f'<ellipse class="{c}" cx="{cx:.1f}" cy="{cy:.1f}" rx="{w/2:.1f}" ry="{h/2:.1f}"/>')
        out.append(text_block(cx, cy, n["_lab"], n["_note"]))
    elif g == "condition":
        pts = f"{cx:.1f},{y:.1f} {x+w:.1f},{cy:.1f} {cx:.1f},{y+h:.1f} {x:.1f},{cy:.1f}"
        out.append(f'<polygon class="{c}" points="{pts}"/>')
        out.append(text_block(cx, cy, n["_lab"], n["_note"]))
    elif g == "event":
        p = [(x + w * 0.14, y), (x + w * 0.86, y), (x + w, y + h * 0.32),
             (cx, y + h), (x, y + h * 0.32)]
        pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in p)
        out.append(f'<polygon class="{c}" points="{pts}"/>')
        out.append(text_block(cx, cy + 2, n["_lab"], n["_note"]))
    elif g == "process":
        b = h * 0.22
        aw = w * 0.30
        p = [(x, y + b), (x + w - aw, y + b), (x + w - aw, y), (x + w, cy),
             (x + w - aw, y + h), (x + w - aw, y + h - b), (x, y + h - b)]
        pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in p)
        out.append(f'<polygon class="{c}" points="{pts}"/>')
        out.append(text_block(x + (w - aw) / 2, cy, n["_lab"], n["_note"]))
    elif g == "plane":
        sk = w * 0.14
        p = [(x + sk, y), (x + w, y), (x + w - sk, y + h), (x, y + h)]
        pts = " ".join(f"{px:.1f},{py:.1f}" for px, py in p)
        out.append(f'<polygon class="{c}" points="{pts}"/>')
        out.append(text_block(cx, cy, n["_lab"], n["_note"]))
    elif g == "position":
        r = h * 0.16
        hy = y + 6 + r
        out.append(f'<circle class="{c}" cx="{cx:.1f}" cy="{hy:.1f}" r="{r:.1f}"/>')
        tw = w * 0.26
        out.append(f'<path class="{c}" d="M {cx-tw:.1f} {y+h-6:.1f} Q {cx-tw:.1f} {hy+r+8:.1f} '
                   f'{cx:.1f} {hy+r+6:.1f} Q {cx+tw:.1f} {hy+r+8:.1f} {cx+tw:.1f} {y+h-6:.1f}" '
                   f'fill="rgba(139,92,246,0.10)"/>')
        ty = y + 6 + 2 * r + 8 + 4
        for l in n["_lab"]:
            out.append(f'<text class="t-lab" x="{cx:.1f}" y="{ty:.1f}" text-anchor="middle">{esc(l)}</text>')
            ty += LH_LABEL
        for l in n["_note"]:
            out.append(f'<text class="t-note" x="{cx:.1f}" y="{ty:.1f}" text-anchor="middle">{esc(l)}</text>')
            ty += LH_NOTE
    elif g == "focus":
        out.append(f'<circle class="{c}" cx="{x+12:.1f}" cy="{cy:.1f}" r="8"/>')
        tx = x + 28
        ty = cy + 4
        for l in n["_lab"]:
            out.append(f'<text class="t-lab" x="{tx:.1f}" y="{ty:.1f}">{esc(l)}</text>')
            ty += LH_LABEL
    elif g == "term":
        out.append(f'<rect class="{c}" x="{x:.1f}" y="{cy-11:.1f}" width="22" height="22" rx="5"/>')
        out.append(f'<text class="t-lab" x="{x+11:.1f}" y="{cy+4:.1f}" text-anchor="middle">'
                   f'{esc(n.get("badge") or n["_lab"][0][:1])}</text>')
        tx = x + 30
        ty = cy + 4
        for l in n["_lab"]:
            out.append(f'<text class="t-lab" x="{tx:.1f}" y="{ty:.1f}">{esc(l)}</text>')
            ty += LH_LABEL
    out.append(marker_glyph(n, x, y, w))
    return "".join(out)


def draw_frame(fr, box):
    x, y, w, h = box
    k = fr.get("kind", "group")
    lab = esc(fr.get("label", ""))
    out = []
    if k == "context":
        out.append(f'<path class="f-line" d="M {x:.1f} {y+h:.1f} L {x:.1f} {y:.1f} L {x+w:.1f} {y:.1f}"/>')
        out.append(f'<text class="t-frame" x="{x+8:.1f}" y="{y-7:.1f}">{lab}</text>')
    elif k == "constraint":
        out.append(f'<path class="f-line" d="M {x:.1f} {y+h:.1f} L {x:.1f} {y:.1f} '
                   f'L {x+w:.1f} {y:.1f} L {x+w:.1f} {y+h:.1f}"/>')
        out.append(f'<text class="t-frame" x="{x+8:.1f}" y="{y+15:.1f}">{lab}</text>')
    elif k == "group":
        out.append(f'<rect class="f-line f-dash" x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" '
                   f'height="{h:.1f}" rx="12"/>')
        out.append(f'<text class="t-frame" x="{x+10:.1f}" y="{y+16:.1f}">{lab}</text>')
    elif k == "boundary":
        out.append(f'<line class="f-line" x1="{x:.1f}" y1="{y:.1f}" x2="{x+w:.1f}" y2="{y:.1f}"/>')
        out.append(f'<text class="t-frame" x="{x+w+8:.1f}" y="{y+4:.1f}">{lab}</text>')
    return "".join(out)


def anchor_point(n_or_box, side, is_frame=False):
    if is_frame:
        x, y, w, h = n_or_box
    else:
        x, y, w, h = n_or_box["_x"], n_or_box["_y"], n_or_box["_w"], n_or_box["_h"]
    if side == "right":
        return (x + w, y + h / 2)
    if side == "left":
        return (x, y + h / 2)
    if side == "top":
        return (x + w / 2, y)
    return (x + w / 2, y + h)


def draw_graph_svg(sc, sid, used):
    nodes, edges, frames, fb, W, H = layout_graph(sc)
    H = max(H, 120)
    node_by_id = {n["id"]: n for n in nodes}

    pair_count = defaultdict(int)
    pair_seen = defaultdict(int)
    for e in edges:
        pair_count[(e["from"], e["to"])] += 1

    edge_parts = []
    max_x, max_y = W, H
    for e in edges:
        frm, to = e["from"], e["to"]
        t = e.get("type", "action")
        used.add(t)
        src = node_by_id.get(frm)
        dst = node_by_id.get(to)
        s_is_f, d_is_f = src is None, dst is None
        sbox = fb.get(frm) if s_is_f else src
        dbox = fb.get(to) if d_is_f else dst
        if sbox is None or dbox is None:
            continue
        sx, sy = anchor_point(sbox, "right", s_is_f)
        dx, dy = anchor_point(dbox, "left", d_is_f)
        key = (frm, to)
        idx = pair_seen[key]
        pair_seen[key] += 1
        n_par = pair_count[key]
        same_or_back = (not s_is_f and not d_is_f and
                        (dst["_layer"] <= src["_layer"] or abs(sy - dy) > 140))
        if same_or_back:
            bend = 52 + 16 * idx
            if dy < sy:
                ctrl = ((sx + dx) / 2, min(sy, dy) - bend)
            else:
                ctrl = ((sx + dx) / 2, max(sy, dy) + bend)
            mx, my = qpoint((sx, sy), ctrl, (dx, dy), 0.5)
            path = f'M {sx:.1f} {sy:.1f} Q {ctrl[0]:.1f} {ctrl[1]:.1f} {dx:.1f} {dy:.1f}'
        else:
            if n_par > 1:
                off = (idx - (n_par - 1) / 2) * 34
                mx, my = (sx + dx) / 2, (sy + dy) / 2 + off
                path = f'M {sx:.1f} {sy:.1f} Q {mx:.1f} {my:.1f} {dx:.1f} {dy:.1f}'
            else:
                mx, my = (sx + dx) / 2, (sy + dy) / 2
                path = f'M {sx:.1f} {sy:.1f} L {dx:.1f} {dy:.1f}'
        max_x = max(max_x, mx + 90)
        max_y = max(max_y, my + 30)
        ecls = "e-line"
        if t in ("link", "tension"):
            ecls = "e-muted"
        if e.get("dashed") or t == "tension":
            ecls += " e-dash"
        marker = ""
        if t == "link":
            marker = f' marker-start="url(#dot{sid})" marker-end="url(#dot{sid})"'
        elif t in ("action", "control", "shift"):
            marker = f' marker-end="url(#arw{sid})"'
        edge_parts.append(f'<path class="{ecls}" d="{path}"{marker}/>')
        if t == "control":
            nx = -(dy - sy)
            ny = (dx - sx)
            ln = math.hypot(nx, ny) or 1
            nx, ny = nx / ln * 6, ny / ln * 6
            edge_parts.append(f'<line x1="{sx-nx:.1f}" y1="{sy-ny:.1f}" x2="{sx+nx:.1f}" '
                              f'y2="{sy+ny:.1f}" stroke="{ACCENT}" stroke-width="1.8"/>')
        if t == "shift":
            edge_parts.append(f'<line x1="{sx:.1f}" y1="{sy-6:.1f}" x2="{sx:.1f}" '
                              f'y2="{sy+6:.1f}" stroke="{ACCENT}" stroke-width="1.8"/>')
        if e.get("label"):
            lab = wrap_lines(e["label"], 130, 11)
            cw = max((text_px(l, 11) for l in lab), default=0) + 14
            chh = len(lab) * 14 + 8
            edge_parts.append(f'<rect class="chip-bg" x="{mx-cw/2:.1f}" y="{my-chh/2:.1f}" '
                              f'width="{cw:.1f}" height="{chh:.1f}" rx="5"/>')
            ty = my - chh / 2 + 11
            for l in lab:
                edge_parts.append(f'<text class="t-chip" x="{mx:.1f}" y="{ty:.1f}" '
                                  f'text-anchor="middle">{esc(l)}</text>')
                ty += 14
    W = max_x
    H = max(max_y, H)

    parts = [f'<svg viewBox="0 0 {W:.0f} {H:.0f}" xmlns="http://www.w3.org/2000/svg" '
             f'role="img" style="max-width:{max(W, 640):.0f}px">']
    parts.append(
        f'<defs>'
        f'<marker id="arw{sid}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" '
        f'markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker>'
        f'<marker id="dot{sid}" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" '
        f'markerHeight="6"><circle cx="5" cy="5" r="3" fill="#6e6683"/></marker>'
        f'</defs>')
    for fr in frames:
        if fr["id"] in fb:
            parts.append(draw_frame(fr, fb[fr["id"]]))
            used.add(fr.get("kind", "group"))
    parts.extend(edge_parts)
    for n in nodes:
        parts.append(draw_node(n, sid))
        used.add(n["grapheme"])
        if n.get("epistemic") and n["epistemic"] != "source":
            used.add(n["epistemic"])
        if n.get("marker"):
            used.add("marker-" + n["marker"])
        if n.get("emphasis"):
            used.add("emphasis")
    parts.append("</svg>")
    return "".join(parts), used


def qpoint(p0, p1, p2, t):
    mt = 1 - t
    return (mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0],
            mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1])


# ----------------------------------------------------------------------------
# Карта (две оси) и ось времени
# ----------------------------------------------------------------------------

def draw_map_svg(sc, sid, used):
    used.add("map")
    items = sc.get("items", [])
    W, H = 660, 470
    ox, oy = W / 2, H / 2
    ax = 250
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
             f'style="max-width:{W}px">']
    parts.append(f'<defs><marker id="arw{sid}" viewBox="0 0 10 10" refX="9" refY="5" '
                 f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                 f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker></defs>')
    parts.append(f'<line class="e-line e-dash" x1="{ox-ax}" y1="{oy}" x2="{ox+ax}" y2="{oy}" opacity="0.35"/>')
    parts.append(f'<line class="e-line e-dash" x1="{ox}" y1="{oy-ax}" x2="{ox}" y2="{oy+ax}" opacity="0.35"/>')
    parts.append(f'<line class="e-line" x1="{ox-ax-16}" y1="{oy}" x2="{ox+ax+14}" y2="{oy}" marker-end="url(#arw{sid})" opacity="0.6"/>')
    parts.append(f'<line class="e-line" x1="{ox}" y1="{oy+ax+14}" x2="{ox}" y2="{oy-ax-16}" marker-end="url(#arw{sid})" opacity="0.6"/>')
    parts.append(f'<text class="t-ax" x="{ox+ax+6}" y="{oy+16}">{esc(sc.get("xLabel",""))}</text>')
    parts.append(f'<text class="t-ax" x="{ox-8}" y="{oy-ax-6}" text-anchor="end">{esc(sc.get("yLabel",""))}</text>')
    for it in items:
        px = ox + float(it.get("x", 0)) * ax
        py = oy - float(it.get("y", 0)) * ax
        r = 9 if it.get("emphasis") else 7
        c = "n-emph" if it.get("emphasis") else "n-shape"
        parts.append(f'<circle class="{c}" cx="{px:.1f}" cy="{py:.1f}" r="{r}"/>')
        anchor = "start" if float(it.get("x", 0)) >= 0 else "end"
        parts.append(f'<text class="t-lab" x="{px + (12 if anchor == "start" else -12):.1f}" '
                     f'y="{py + 4:.1f}" text-anchor="{anchor}">{esc(it.get("label",""))}</text>')
    parts.append("</svg>")
    return "".join(parts), used


def draw_timeline_svg(sc, sid, used):
    used.add("timeline")
    pts = sc.get("points", [])
    if not pts:
        return "", used
    wrap = max((len(p.get("label", "")) for p in pts), default=10)
    W = max(560, 60 + len(pts) * (wrap * 8 + 40))
    H = 130
    ax_y = 78
    x0, x1 = 34, W - 40
    parts = [f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" role="img" '
             f'style="max-width:{W}px">']
    parts.append(f'<defs><marker id="arw{sid}" viewBox="0 0 10 10" refX="9" refY="5" '
                 f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
                 f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{ACCENT}"/></marker></defs>')
    parts.append(f'<line class="e-line" x1="{x0}" y1="{ax_y}" x2="{x1}" y2="{ax_y}" '
                 f'marker-end="url(#arw{sid})"/>')
    span = max(1e-9, max((float(p.get("t", 0)) for p in pts), default=1.0))
    for p in pts:
        t = float(p.get("t", 0)) / span
        px = x0 + t * (x1 - x0 - 10)
        parts.append(f'<line x1="{px:.1f}" y1="{ax_y-5}" x2="{px:.1f}" y2="{ax_y+5}" '
                     f'stroke="{ACCENT}" stroke-width="1.6"/>')
        parts.append(f'<circle cx="{px:.1f}" cy="{ax_y}" r="3.4" fill="{ACCENT}"/>')
        for li, l in enumerate(wrap_lines(p.get("label", ""), 150, 11)):
            parts.append(f'<text class="t-chip" x="{px:.1f}" y="{ax_y-14-li*13:.1f}" '
                         f'text-anchor="middle">{esc(l)}</text>')
    parts.append(f'<text class="t-ax" x="{x1+4}" y="{ax_y+18}">время</text>')
    parts.append("</svg>")
    return "".join(parts), used


# ----------------------------------------------------------------------------
# Легенда
# ----------------------------------------------------------------------------

def mini_icon(key):
    a = f'stroke="{ACCENT}" fill="rgba(139,92,246,0.14)" stroke-width="1.5"'
    if key == "object":
        return f'<svg width="26" height="18"><rect x="2" y="3" width="22" height="12" rx="3" {a}/></svg>'
    if key == "place":
        return f'<svg width="26" height="18"><ellipse cx="13" cy="9" rx="10" ry="6.5" {a}/></svg>'
    if key == "position":
        return (f'<svg width="26" height="18"><circle cx="13" cy="5.5" r="2.6" {a}/>'
                f'<path d="M 9.5 14 Q 9.5 8.5 13 8.7 Q 16.5 8.5 16.5 14" {a}/></svg>')
    if key == "condition":
        return f'<svg width="26" height="18"><polygon points="13,1.5 24,9 13,16.5 2,9" {a}/></svg>'
    if key == "event":
        return (f'<svg width="26" height="18"><polygon points="5,2 21,2 24,7 13,16.5 2,7" {a}/></svg>')
    if key == "process":
        return (f'<svg width="26" height="18"><polygon points="2,5.5 17,5.5 17,2 24,9 '
                f'17,16 17,12.5 2,12.5" {a}/></svg>')
    if key == "plane":
        return f'<svg width="26" height="18"><polygon points="6,2 24,2 20,16 2,16" {a}/></svg>'
    if key == "focus":
        return f'<svg width="26" height="18"><circle cx="13" cy="9" r="5.5" {a}/></svg>'
    if key == "term":
        return (f'<svg width="26" height="18"><rect x="3" y="3" width="12" height="12" rx="3" {a}/>'
                f'<text x="9" y="12.5" font-size="9" text-anchor="middle" fill="{ACCENT}" font-weight="700">A</text></svg>')
    if key == "action":
        return (f'<svg width="30" height="18"><line x1="2" y1="9" x2="23" y2="9" stroke="{ACCENT}" '
                f'stroke-width="1.6"/><polygon points="23,5 29,9 23,13" fill="{ACCENT}"/></svg>')
    if key == "link":
        return (f'<svg width="30" height="18"><line x1="3" y1="9" x2="27" y2="9" '
                f'stroke="#6e6683" stroke-width="1.6"/><circle cx="3" cy="9" r="2.4" fill="#6e6683"/>'
                f'<circle cx="27" cy="9" r="2.4" fill="#6e6683"/></svg>')
    if key == "control":
        return (f'<svg width="30" height="18"><line x1="4" y1="9" x2="4" y2="9" stroke="{ACCENT}"/>'
                f'<line x1="4" y1="4" x2="4" y2="14" stroke="{ACCENT}" stroke-width="1.8"/>'
                f'<line x1="4" y1="9" x2="23" y2="9" stroke="{ACCENT}" stroke-width="1.6"/>'
                f'<polygon points="23,5 29,9 23,13" fill="{ACCENT}"/></svg>')
    if key == "shift":
        return (f'<svg width="30" height="18"><line x1="5" y1="4" x2="5" y2="14" stroke="{ACCENT}" stroke-width="1.8"/>'
                f'<line x1="5" y1="9" x2="23" y2="9" stroke="{ACCENT}" stroke-width="1.6"/>'
                f'<polygon points="23,5 29,9 23,13" fill="{ACCENT}"/></svg>')
    if key == "tension":
        return (f'<svg width="30" height="18"><line x1="2" y1="9" x2="27" y2="9" '
                f'stroke="#6e6683" stroke-width="1.6" stroke-dasharray="4 3"/></svg>')
    if key == "context":
        return ('<svg width="26" height="18"><path d="M 3 15 L 3 3 L 23 3" '
                f'stroke="{ACCENT}" fill="none" stroke-width="1.5"/></svg>')
    if key == "constraint":
        return ('<svg width="26" height="18"><path d="M 3 15 L 3 3 L 23 3 L 23 15" '
                f'stroke="{ACCENT}" fill="none" stroke-width="1.5"/></svg>')
    if key == "group":
        return (f'<svg width="26" height="18"><rect x="2" y="2" width="22" height="14" rx="4" '
                f'stroke="{ACCENT}" fill="none" stroke-dasharray="4 3" stroke-width="1.4"/></svg>')
    if key == "boundary":
        return f'<svg width="26" height="18"><line x1="2" y1="9" x2="24" y2="9" stroke="{ACCENT}" stroke-width="1.6"/></svg>'
    if key == "map":
        return (f'<svg width="26" height="18"><line x1="2" y1="9" x2="24" y2="9" stroke="{ACCENT}" stroke-width="1.2"/>'
                f'<line x1="13" y1="2" x2="13" y2="16" stroke="{ACCENT}" stroke-width="1.2"/></svg>')
    if key == "timeline":
        return (f'<svg width="26" height="18"><line x1="2" y1="9" x2="22" y2="9" stroke="{ACCENT}" stroke-width="1.4"/>'
                f'<polygon points="22,6 26,9 22,12" fill="{ACCENT}"/>'
                f'<line x1="8" y1="6" x2="8" y2="12" stroke="{ACCENT}" stroke-width="1.4"/></svg>')
    if key == "source":
        return f'<svg width="26" height="18"><rect x="3" y="3" width="20" height="12" rx="3" {a}/></svg>'
    if key == "reconstruction":
        return f'<svg width="26" height="18"><rect x="3" y="3" width="20" height="12" rx="3" {a} opacity="0.65"/></svg>'
    if key == "interpretation":
        return (f'<svg width="26" height="18"><rect x="3" y="3" width="20" height="12" rx="3" '
                f'stroke="{ACCENT}" fill="rgba(139,92,246,0.10)" stroke-dasharray="4 3" stroke-width="1.5"/></svg>')
    if key == "norm":
        return f'<svg width="26" height="18"><rect x="3" y="3" width="20" height="12" rx="3" stroke="{ACCENT}" fill="rgba(139,92,246,0.10)" stroke-width="2.4"/></svg>'
    if key == "emphasis":
        return f'<svg width="26" height="18"><rect x="3" y="3" width="20" height="12" rx="3" fill="rgba(139,92,246,0.22)" stroke="{ACCENT}" stroke-width="2.2"/></svg>'
    if key == "marker-star":
        return f'<svg width="26" height="18"><text x="13" y="14" font-size="13" text-anchor="middle" fill="{ACCENT}">&#10033;</text></svg>'
    if key == "marker-hash":
        return f'<svg width="26" height="18"><text x="13" y="14" font-size="12" font-weight="700" text-anchor="middle" fill="{ACCENT}">#</text></svg>'
    return ""


LEGEND_ORDER = ["object", "place", "position", "condition", "event", "process",
                "plane", "focus", "term", "action", "link", "control", "shift",
                "tension", "context", "constraint", "group", "boundary", "map",
                "timeline", "source", "reconstruction", "interpretation", "norm",
                "emphasis", "marker-star", "marker-hash"]


def legend_html(used):
    keys = [k for k in LEGEND_ORDER if k in used]
    if not keys:
        return ""
    items = []
    for k in keys:
        name, hint = GLYPH_NAMES.get(k, (k, ""))
        if k.startswith("marker-"):
            name = "Знак отличия"
            hint = "особый статус элемента"
        if k == "emphasis":
            name, hint = "Акцент", "ключевой элемент схемы"
        if k == "map":
            name, hint = "Карта", "позиции на двух осях"
        if k == "timeline":
            name, hint = "Ось времени", "хронология, последовательность"
        items.append(f'<span class="li">{mini_icon(k)}<span><b>{esc(name)}</b> — {esc(hint)}</span></span>')
    return f'<div class="csv-legend">{"".join(items)}</div>'


def matrix_html(mx):
    if not mx:
        return ""
    cols = mx.get("columns", [])
    out = ['<table class="csv-matrix"><thead><tr>']
    for c in cols:
        out.append(f"<th>{esc(c)}</th>")
    out.append("</tr></thead><tbody>")
    for row in mx.get("rows", []):
        out.append("<tr>")
        out.append(f'<td>{esc(row.get("label",""))}</td>')
        for cell in row.get("cells", []):
            out.append(f"<td>{esc(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")
    return "".join(out)


def render_html(spec, page=False):
    used = set()
    sections = []
    for i, sc in enumerate(spec.get("schemas", [])):
        kind = sc.get("kind", "graph")
        sec = [f'<section class="csv-schema">']
        if sc.get("title"):
            sec.append(f"<h3>{esc(sc['title'])}</h3>")
        if sc.get("note"):
            sec.append(f'<p class="csv-note">{esc(sc["note"])}</p>')
        if kind == "map":
            svg, used = draw_map_svg(sc, i, used)
        elif kind == "timeline":
            svg, used = draw_timeline_svg(sc, i, used)
        else:
            svg, used = draw_graph_svg(sc, i, used)
        sec.append(svg)
        sec.append("</section>")
        sections.append("".join(sec))
    body = [f'<div class="csv-root">']
    if spec.get("title"):
        body.append(f'<h2 class="csv-title">{esc(spec["title"])}</h2>')
    if spec.get("subtitle"):
        body.append(f'<p class="csv-subtitle">{esc(spec["subtitle"])}</p>')
    body.extend(sections)
    body.append(matrix_html(spec.get("matrix")))
    body.append(legend_html(used))
    if spec.get("footer"):
        body.append(f'<p class="csv-footer">{esc(spec["footer"])}</p>')
    body.append("</div>")
    inner = "".join(body)
    style = f"<style>{CSS}</style>"
    if page:
        return ("<!DOCTYPE html><html lang=\"ru\"><head><meta charset=\"utf-8\">"
                "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">"
                f"<title>{esc(spec.get('title', 'Схема'))}</title>{style}</head>"
                f'<body class="csv-page">{inner}</body></html>')
    return f'<!DOCTYPE html><html lang="ru"><head><meta charset="utf-8">{style}</head><body>{inner}</body></html>'


# ----------------------------------------------------------------------------
# Экспорт: Obsidian Canvas
# ----------------------------------------------------------------------------

def export_canvas(spec, path, chk):
    nodes_out, edges_out = [], []
    en, eid = 0, 0
    for sc in spec.get("schemas", []):
        if sc.get("kind", "graph") != "graph":
            chk.warn("canvas: экспортируются только graph-схемы, остальные пропущены")
            continue
        nodes, edges, frames, fb, W, H = layout_graph(sc)
        ox = 0
        oy = 0
        id_map = {}
        for n in nodes:
            en += 1
            cid = f"n{en}"
            id_map[n["id"]] = cid
            text = n.get("label", "")
            if n.get("note"):
                text += "\n\n" + n["note"]
            nodes_out.append({
                "id": cid, "type": "text", "x": int(ox + n["_x"]),
                "y": int(oy + n["_y"]), "width": int(n["_w"]),
                "height": int(n["_h"] + 8), "text": text, "color": "6" if n.get("emphasis") else None,
            })
        for e in edges:
            eid += 1
            backward = False
            edges_out.append({
                "id": f"e{eid}", "fromNode": id_map[e["from"]], "toNode": id_map[e["to"]],
                "fromSide": "right", "toSide": "left", "label": e.get("label", ""),
                "color": "6",
            })
        if frames:
            chk.warn("canvas: рамки не переносятся в Obsidian Canvas")
    data = {"nodes": nodes_out, "edges": edges_out}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return len(nodes_out), len(edges_out)


# ----------------------------------------------------------------------------
# Экспорт: Excalidraw
# ----------------------------------------------------------------------------

def export_excalidraw(spec, path, chk):
    rnd = random.Random(42)
    elements = []
    ec = [0]

    def nid():
        ec[0] += 1
        return f"el{ec[0]}"

    approx_warned = set()
    for sc in spec.get("schemas", []):
        if sc.get("kind", "graph") != "graph":
            chk.warn("excalidraw: экспортируются только graph-схемы")
            continue
        nodes, edges, frames, fb, W, H = layout_graph(sc)
        id_map = {}
        for n in nodes:
            g = n["grapheme"]
            if g in ("position", "process", "event", "plane", "term"):
                if g not in approx_warned:
                    chk.warn(f"excalidraw: графема {g!r} приближена прямоугольником")
                    approx_warned.add(g)
                etype = "rectangle"
            elif g == "place":
                etype = "ellipse"
            elif g == "condition":
                etype = "diamond"
            elif g == "focus":
                etype = "ellipse"
            else:
                etype = "rectangle"
            sid = nid()
            tid = nid()
            id_map[n["id"]] = sid
            text = n.get("label", "")
            if n.get("note"):
                text += "\n" + n["note"]
            lines = text.count("\n") + 1
            el = {
                "type": etype, "id": sid, "x": n["_x"], "y": n["_y"],
                "width": n["_w"], "height": n["_h"], "angle": 0,
                "strokeColor": "#1e1e1e",
                "backgroundColor": "#d0bfff" if n.get("emphasis") else "#e6ddff",
                "fillStyle": "solid", "strokeWidth": 2, "roughness": 1,
                "opacity": 100, "groupIds": [],
                "roundness": {"type": 3} if etype == "rectangle" else None,
                "seed": rnd.randint(1, 10 ** 6),
                "version": 1, "versionNonce": rnd.randint(1, 10 ** 6),
                "isDeleted": False,
                "boundElements": [{"id": tid, "type": "text"}],
                "link": None, "locked": False,
            }
            elements.append(el)
            elements.append({
                "type": "text", "id": tid, "x": n["_x"] + 4, "y": n["_y"] + n["_h"] / 2 - lines * 11,
                "width": n["_w"] - 8, "height": lines * 22, "text": text,
                "fontSize": 16, "fontFamily": 1, "strokeColor": "#1e1e1e",
                "backgroundColor": "transparent", "fillStyle": "solid",
                "strokeWidth": 1, "roughness": 1, "opacity": 100,
                "groupIds": [], "roundness": None,
                "seed": rnd.randint(1, 10 ** 6), "version": 1,
                "versionNonce": rnd.randint(1, 10 ** 6), "isDeleted": False,
                "boundElements": None, "containerId": sid,
                "originalText": text, "autoResize": True,
                "textAlign": "center", "verticalAlign": "middle",
                "link": None, "locked": False,
            })
        for e in edges:
            src = next((n for n in nodes if n["id"] == e["from"]), None)
            dst = next((n for n in nodes if n["id"] == e["to"]), None)
            if not src or not dst:
                continue
            sx, sy = src["_x"] + src["_w"], src["_y"] + src["_h"] / 2
            dx, dy = dst["_x"] - sx, dst["_y"] + dst["_h"] / 2 - sy
            aid = nid()
            head = "arrow" if e.get("type") in ("action", "control", "shift") else "dot"
            bound = [{"id": aid, "type": "arrow"}]
            elements.append({
                "type": "arrow", "id": aid, "x": sx, "y": sy, "width": abs(dx),
                "height": abs(dy), "angle": 0, "strokeColor": "#1e1e1e",
                "backgroundColor": "transparent", "fillStyle": "solid",
                "strokeWidth": 2, "roughness": 1, "opacity": 100,
                "groupIds": [], "roundness": {"type": 2},
                "seed": rnd.randint(1, 10 ** 6), "version": 1,
                "versionNonce": rnd.randint(1, 10 ** 6), "isDeleted": False,
                "points": [[0, 0], [dx, dy]],
                "lastCommittedPoint": None,
                "startBinding": {"elementId": id_map[e["from"]], "focus": 0, "gap": 4,
                                  "fixedPoint": [1, 0.5]},
                "endBinding": {"elementId": id_map[e["to"]], "focus": 0, "gap": 4,
                               "fixedPoint": [0, 0.5]},
                "endArrowhead": head, "startArrowhead": None,
                "boundElements": None, "link": None, "locked": False,
            })
            if e.get("label"):
                tid = nid()
                elements.append({
                    "type": "text", "id": tid, "x": (sx + sx + dx) / 2 - 30,
                    "y": (sy + sy + dy) / 2 - 22, "width": 60, "height": 20,
                    "text": e["label"], "fontSize": 16, "fontFamily": 1,
                    "strokeColor": "#1e1e1e", "backgroundColor": "transparent",
                    "fillStyle": "solid", "strokeWidth": 1, "roughness": 1,
                    "opacity": 100, "groupIds": [], "roundness": None,
                    "seed": rnd.randint(1, 10 ** 6), "version": 1,
                    "versionNonce": rnd.randint(1, 10 ** 6), "isDeleted": False,
                    "boundElements": None, "containerId": None,
                    "originalText": e["label"], "autoResize": True,
                    "textAlign": "center", "verticalAlign": "middle",
                    "link": None, "locked": False,
                })
    data = {"type": "excalidraw", "version": 2, "source": "concept-schema-visualizer",
            "elements": elements, "appState": {"viewBackgroundColor": "#ffffff"},
            "files": {}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return len(elements)


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="JSON-спека → HTML/SVG-схема")
    ap.add_argument("spec", help="путь к spec.json")
    ap.add_argument("-o", "--out", default="schema.html", help="выходной HTML")
    ap.add_argument("--page", action="store_true", help="автономная страница (с фоном)")
    ap.add_argument("--canvas", help="доп. экспорт в Obsidian Canvas (.canvas)")
    ap.add_argument("--excalidraw", help="доп. экспорт в Excalidraw (.excalidraw)")
    ap.add_argument("--strict", action="store_true", help="предупреждения = код 1")
    args = ap.parse_args()

    chk = Checker()
    try:
        spec = load_spec(args.spec, chk)
    except (SpecError, json.JSONDecodeError, OSError) as ex:
        print(f"ERROR: {ex}", file=sys.stderr)
        return 2

    if args.canvas:
        export_canvas(spec, args.canvas, chk)
    if args.excalidraw:
        export_excalidraw(spec, args.excalidraw, chk)

    html_out = render_html(spec, page=args.page)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html_out)

    code = chk.report(strict=args.strict)
    if code == 0:
        n = len(spec.get("schemas", []))
        print(f"OK: {args.out} ({n} схем)")
    return code


if __name__ == "__main__":
    sys.exit(main())