#!/usr/bin/env python3
"""Generate all 8 Tokyo Night Zed themes in themes/tokyo-night.json from official VS Code sources.

Usage: python3 scripts/build.py [path/to/source]

Reads the official VS Code themes from tokyo-night/tokyo-night-vscode-theme in source/
(Tokyo Night, Tokyo Night Storm, Tokyo Night Light) plus an all-black variant, and
generates both bordered and unbordered variants for each in a single themes/tokyo-night.json
file with harmonized crisp git diff colors, clean file selector highlight, and white cursor.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = ROOT / "source"
OUT = ROOT / "themes"
SCHEMA = "https://zed.dev/schema/themes/v0.2.0.json"
AUTHOR = "Dallas Gere"
TRANSPARENT = "#00000000"
GIT_DIM = 0.92

# (source file, display name, appearance, all_black, folke)
VARIANTS = [
    ("tokyo-night-color-theme.json", "Tokyo Night", "dark", False, False),
    ("tokyo-night-storm-color-theme.json", "Tokyo Night Storm", "dark", False, False),
    ("tokyo-night-light-color-theme.json", "Tokyo Night Light", "light", False, False),
    ("tokyo-night-color-theme.json", "Tokyo Night Black", "dark", True, False),
    ("tokyo-night-color-theme.json", "Tokyo Night (Nvim)", "dark", False, True),
    ("tokyo-night-color-theme.json", "Tokyo Night (Nvim) Black", "dark", True, True),
]

# folke/tokyonight.nvim "moon" palette (preserved alongside the official VS Code variants).
FOLKE = {
    "fg": "#c2ccf0",
    "fg_dark": "#828bb8",
    "comment": "#636da6",
    "blue": "#82aaff",
    "blue1": "#65bcff",
    "blue5": "#89ddff",
    "blue6": "#98dedd",
    "cyan": "#86e1fc",
    "green": "#b8de82",
    "green1": "#4fd6be",
    "magenta": "#c099ff",
    "purple": "#fca7ea",
    "orange": "#ff966c",
    "yellow": "#f2be72",
    "red": "#ff757f",
    "bg": "#222436",
}

# Crisp, theme-harmonized git palettes for dark & light Tokyo Night.
GIT_PALETTES = {
    "dark": {
        "added": "#9ece6a",
        "modified": "#e0af68",
        "deleted": "#f7768e",
        "conflict": "#ff9e64",
        "ignored": "#565f89",
        "gutter_added": "#9ece6a",
        "gutter_modified": "#7aa2f7",
        "gutter_deleted": "#f7768e",
    },
    "light": {
        "added": "#485e30",
        "modified": "#8f5e15",
        "deleted": "#8c4351",
        "conflict": "#965027",
        "ignored": "#707280",
        "gutter_added": "#485e30",
        "gutter_modified": "#34548a",
        "gutter_deleted": "#8c4351",
    },
}

SYNTAX_SCOPES = {
    "attribute": [["meta.tag", "entity.other.attribute-name"]],
    "boolean": [["constant.language.boolean.true"], ["constant.language"]],
    "comment": [["comment.line.double-slash"], ["comment"]],
    "comment.doc": [["comment.block.documentation"], ["comment"]],
    "constant": [["variable.other.constant"], ["constant"]],
    "constant.builtin": [["constant.language.null"], ["constant.language"]],
    "constructor": [["entity.name.type.class"], ["entity.name.class"], ["support.class"]],
    "diff.minus": [["markup.deleted"]],
    "diff.plus": [["markup.inserted"]],
    "embedded": [["meta.embedded"]],
    "emphasis": [["markup.italic"]],
    "emphasis.strong": [["markup.bold"]],
    "enum": [["entity.name.type.enum"], ["entity.name.type"]],
    "function": [["entity.name.function"]],
    "function.builtin": [["support.function"], ["entity.name.function"]],
    "function.call": [["meta.function-call", "entity.name.function"], ["entity.name.function"]],
    "function.definition": [["entity.name.function"]],
    "function.method": [["entity.name.function.member"], ["entity.name.function"]],
    "function.method.call": [["meta.function-call", "entity.name.function"], ["entity.name.function"]],
    "function.special": [["support.function.macro"], ["entity.name.function"]],
    "keyword": [["keyword"]],
    "keyword.conditional": [["keyword.control.conditional"], ["keyword.control"], ["keyword"]],
    "keyword.control": [["keyword.control"], ["keyword"]],
    "keyword.coroutine": [["keyword.control.flow"], ["storage.modifier.async"], ["keyword"]],
    "keyword.directive": [["meta.preprocessor"], ["keyword.control.directive"], ["keyword"]],
    "keyword.exception": [["keyword.control.trycatch"], ["keyword.control"], ["keyword"]],
    "keyword.export": [["keyword.control.export"], ["keyword.control"], ["keyword"]],
    "keyword.function": [["storage.type.function"], ["storage.type"], ["keyword"]],
    "keyword.import": [["keyword.control.import"], ["keyword.control"], ["keyword"]],
    "keyword.modifier": [["storage.modifier"], ["keyword"]],
    "keyword.operator": [["keyword.operator"], ["keyword"]],
    "keyword.repeat": [["keyword.control.loop"], ["keyword.control"], ["keyword"]],
    "keyword.return": [["keyword.control.flow"], ["keyword.control"], ["keyword"]],
    "keyword.storage": [["storage.type"], ["storage"]],
    "keyword.type": [["storage.type"], ["keyword"]],
    "label": [["entity.name.label"], ["variable"]],
    "link_text": [["markup.underline.link"], ["string.other.link"]],
    "link_uri": [["markup.underline.link"], ["constant.other.reference.link"]],
    "namespace": [["entity.name.namespace"], ["entity.name.type"]],
    "number": [["constant.numeric"]],
    "operator": [["keyword.operator"]],
    "preproc": [["meta.preprocessor"], ["keyword"]],
    "primary": [["source"]],
    "property": [["variable.other.property"], ["support.type.property-name"], ["variable.other.object.property"]],
    "property.json_key": [["support.type.property-name.json"], ["entity.name.tag"]],
    "punctuation": [["punctuation"]],
    "punctuation.bracket": [["meta.brace.round"], ["punctuation.section"], ["punctuation"]],
    "punctuation.delimiter": [["punctuation.separator"], ["punctuation"]],
    "punctuation.list_marker": [["punctuation.definition.list.begin.markdown"], ["markup.list"]],
    "punctuation.markup": [["punctuation.definition.heading.markdown"], ["punctuation"]],
    "punctuation.special": [["punctuation.definition.template-expression.begin"], ["punctuation"]],
    "selector": [["entity.name.tag.css"], ["entity.other.attribute-name.class.css"]],
    "selector.pseudo": [["entity.other.attribute-name.pseudo-class.css"], ["entity.name.tag"]],
    "string": [["string.quoted.double"], ["string"]],
    "string.doc": [["string.quoted.docstring"], ["string"]],
    "string.escape": [["constant.character.escape"], ["string"]],
    "string.regex": [["string.regexp"], ["source.regexp"]],
    "string.special": [["string.template"], ["string"]],
    "string.special.symbol": [["constant.other.symbol"], ["constant"]],
    "tag": [["entity.name.tag"]],
    "tag.doctype": [["meta.tag.sgml.doctype"], ["entity.name.tag"]],
    "text.literal": [["markup.inline.raw"], ["string"]],
    "title": [["markup.heading"], ["entity.name.section"]],
    "type": [["entity.name.type"], ["support.type"]],
    "type.builtin": [["support.type.primitive"], ["support.type"], ["storage.type"]],
    "type.interface": [["entity.name.type.interface"], ["entity.name.type"]],
    "type.parameter": [["entity.name.type.parameter"], ["entity.name.type"]],
    "variable": [["variable.other.readwrite"], ["variable"]],
    "variable.member": [["variable.other.property"], ["variable.other.object.property"], ["variable"]],
    "variable.parameter": [["variable.parameter"], ["variable"]],
    "variable.special": [["variable.language.this"], ["variable.language"]],
    "variant": [["variable.other.enummember"], ["constant"]],
}


def norm_color(val):
    if not val or not isinstance(val, str) or not val.startswith("#"):
        return None
    h = val[1:].lower()
    if len(h) in (3, 4):
        h = "".join(c * 2 for c in h)
    if len(h) not in (6, 8) or not re.fullmatch(r"[0-9a-f]+", h):
        return None
    return "#" + h


def with_alpha(val, alpha):
    c = norm_color(val)
    return (c[:7] + alpha) if c else None


def blend(fg, alpha, bg):
    """Straight sRGB mix: alpha of fg over bg."""
    a = [int(fg[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(bg[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x * alpha + y * (1 - alpha)):02x}" for x, y in zip(a, b))


def parse_rules(theme):
    rules = []
    for idx, rule in enumerate(theme.get("tokenColors", [])):
        settings = rule.get("settings", {})
        fg = norm_color(settings.get("foreground"))
        fs = settings.get("fontStyle")
        if not fg and not fs:
            continue
        scopes = rule.get("scope", [])
        if isinstance(scopes, str):
            scopes = [s.strip() for s in scopes.split(",") if s.strip()]
        for sel in scopes:
            parts = [p for p in sel.split() if p]
            if parts:
                rules.append((parts, idx, fg, fs))
    return rules


def scope_matches(prefix, scope):
    return scope == prefix or scope.startswith(prefix + ".")


def match_selector(parts, stack):
    if not parts or not stack or not scope_matches(parts[-1], stack[-1]):
        return None
    si = len(stack) - 2
    for pi in range(len(parts) - 2, -1, -1):
        while si >= 0 and not scope_matches(parts[pi], stack[si]):
            si -= 1
        if si < 0:
            return None
        si -= 1
    return (len(parts[-1].split(".")), len(parts), sum(len(p) for p in parts))


def resolve_token(rules, stacks, fallback_fg):
    best_fg = best_fg_key = best_fs = best_fs_key = None
    for stack in stacks:
        for parts, idx, fg, fs in rules:
            spec = match_selector(parts, stack)
            if spec is None:
                continue
            key = (spec, idx)
            if fg and (best_fg_key is None or key > best_fg_key):
                best_fg, best_fg_key = fg, key
            if fs is not None and (best_fs_key is None or key > best_fs_key):
                best_fs, best_fs_key = fs, key
        if best_fg is not None:
            break
    font_style = "italic" if (best_fs and "italic" in best_fs) else "normal"
    font_weight = 700 if (best_fs and "bold" in best_fs) else 400
    return {"color": best_fg or fallback_fg, "font_style": font_style, "font_weight": font_weight}


def build_syntax(theme, c, git):
    rules = parse_rules(theme)
    fallback = norm_color(c.get("editor.foreground")) or norm_color(c.get("foreground"))
    syntax = {name: resolve_token(rules, stacks, fallback) for name, stacks in SYNTAX_SCOPES.items()}
    syntax["diff.plus"]["color"] = git["added"]
    syntax["diff.minus"]["color"] = git["deleted"]
    hint_col = norm_color(c.get("editorInlayHint.foreground")) or norm_color(c.get("editorLineNumber.foreground"))
    pred_col = norm_color(c.get("editorGhostText.foreground")) or norm_color(c.get("editorLineNumber.foreground"))
    if hint_col:
        syntax["hint"] = {"color": hint_col, "font_style": "normal", "font_weight": 400}
    if pred_col:
        syntax["predictive"] = {"color": pred_col, "font_style": "normal", "font_weight": 400}
    return dict(sorted(syntax.items()))


def build_folke_syntax(git):
    groups = [
        (FOLKE["comment"], "italic", ("comment", "comment.doc")),
        (FOLKE["purple"], "normal", (
            "keyword", "keyword.coroutine", "keyword.return", "keyword.modifier",
            "keyword.type", "keyword.control",
        )),
        (FOLKE["magenta"], "normal", (
            "keyword.conditional", "keyword.repeat", "keyword.exception",
            "keyword.function", "constructor", "string.escape",
        )),
        (FOLKE["cyan"], "normal", (
            "keyword.import", "keyword.export", "keyword.directive", "preproc",
            "function.special", "attribute", "namespace",
        )),
        (FOLKE["blue1"], "normal", (
            "keyword.storage", "type", "type.parameter", "enum", "constant.builtin",
            "function.builtin", "string.special", "string.special.symbol",
        )),
        (FOLKE["blue5"], "normal", (
            "operator", "keyword.operator", "punctuation.delimiter",
            "punctuation.special", "punctuation.list_marker",
        )),
        (FOLKE["blue"], "normal", (
            "function", "function.call", "function.definition", "function.method",
            "function.method.call", "label", "title", "link_uri",
        )),
        (FOLKE["fg_dark"], "normal", ("punctuation", "punctuation.bracket", "hint", "predictive")),
        (FOLKE["green"], "normal", ("string", "text.literal")),
        (FOLKE["green1"], "normal", ("property", "variable.member", "property.json_key", "link_text")),
        (FOLKE["orange"], "normal", ("constant", "boolean", "number", "variant", "punctuation.markup")),
        (FOLKE["yellow"], "normal", ("variable.parameter", "string.doc")),
        (FOLKE["red"], "normal", ("variable.special", "tag", "tag.doctype", "selector", "selector.pseudo")),
        (FOLKE["fg"], "normal", ("variable", "embedded", "primary", "emphasis", "emphasis.strong")),
        (FOLKE["blue6"], "normal", ("string.regex",)),
        (blend(FOLKE["blue1"], 0.8, FOLKE["bg"]), "normal", ("type.builtin",)),
        (blend(FOLKE["blue1"], 0.7, FOLKE["fg"]), "normal", ("type.interface",)),
        (git["added"], "normal", ("diff.plus",)),
        (git["deleted"], "normal", ("diff.minus",)),
    ]
    syntax = {}
    for col, fs, keys in groups:
        for k in keys:
            syntax[k] = {"color": col, "font_style": fs, "font_weight": 400}
    return dict(sorted(syntax.items()))



def visible_invisible(fg, selection, editor_bg):
    """Compute editor.invisible so whitespace dots stay clearly legible over selected text."""
    def _mix(a, t, b):
        ca = [int(a[i : i + 2], 16) for i in (1, 3, 5)]
        cb = [int(b[i : i + 2], 16) for i in (1, 3, 5)]
        return "#" + "".join(f"{round(x * t + y * (1 - t)):02x}" for x, y in zip(ca, cb))
    sel = selection or editor_bg
    if len(sel) == 9:
        sel = _mix(sel[:7], int(sel[7:9], 16) / 255, editor_bg[:7])
    return _mix(fg[:7], 0.42, sel[:7])


def build_style(theme, appearance, unbordered=False, all_black=False, folke=False):
    c = {k: norm_color(v) for k, v in theme.get("colors", {}).items()}
    g = lambda *keys: next((c[k] for k in keys if c.get(k)), None)
    git = GIT_PALETTES[appearance]

    if all_black:
        editor_bg = "#000000"
        shell_bg = "#000000"
        elevated_bg = "#13151c"
        line_bg = "#0e0f14"
        border = TRANSPARENT if unbordered else "#222533"
        border_variant = TRANSPARENT if unbordered else "#171924"
    elif folke:
        editor_bg = "#1c1e29"
        shell_bg = editor_bg if unbordered else "#181921"
        elevated_bg = "#252838"
        line_bg = "#232635"
        border = TRANSPARENT if unbordered else "#2f334a"
        border_variant = TRANSPARENT if unbordered else "#25283a"
    else:
        editor_bg = g("editor.background")
        shell_bg = editor_bg if unbordered else g("sideBar.background", "titleBar.activeBackground", "editor.background")
        # Crisp navy elevation (avoid milky white-blend haze on dark backgrounds).
        if appearance == "dark":
            elevated_bg = blend("#292e42", 0.55, editor_bg)
            subtle_border = blend("#3b4261", 0.70, editor_bg)
            subtle_variant = blend("#3b4261", 0.42, editor_bg)
        else:
            elevated_bg = "#dfe1e8"
            subtle_border = "#c0c3ce"
            subtle_variant = "#cfd2dc"
        line_bg = g("editor.lineHighlightBackground")
        border = TRANSPARENT if unbordered else subtle_border
        border_variant = TRANSPARENT if unbordered else subtle_variant

    accent = g("textLink.foreground", "terminal.ansiBlue", "focusBorder") or "#7aa2f7"
    fg = FOLKE["fg"] if folke else g("editor.foreground", "foreground")
    # Crisp, readable UI text in file explorer & popovers.
    ui_text = fg
    muted_text = "#787c99" if appearance == "dark" else "#616885"
    disabled_text = "#515670" if appearance == "dark" else "#8e93a8"
    # Translucent, understated hover & selection rows so file explorer & popovers stay crisp without an opaque slab.
    hover = with_alpha(accent, "12" if appearance == "dark" else "14")
    selected = with_alpha(accent, "22" if appearance == "dark" else "24")
    cursor = "#ffffff" if appearance == "dark" else fg[:7]
    selection = g("editor.selectionBackground") or with_alpha(accent, "3d")

    g_add = blend(git["gutter_added"], GIT_DIM, editor_bg)
    g_mod = blend(git["gutter_modified"], GIT_DIM, editor_bg)
    g_del = blend(git["gutter_deleted"], GIT_DIM, editor_bg)
    g_con = blend(git["conflict"], GIT_DIM, editor_bg)

    style = {
        "background.appearance": "opaque",
        "background": shell_bg,
        "border": border,
        "border.variant": border_variant,
        "border.focused": TRANSPARENT,
        "border.selected": TRANSPARENT,
        "border.transparent": TRANSPARENT,
        "border.disabled": border,
        "elevated_surface.background": elevated_bg,
        "surface.background": shell_bg,
        "element.background": elevated_bg,
        "element.hover": hover,
        "element.active": selected,
        "element.selected": selected,
        "element.disabled": elevated_bg,
        "drop_target.background": with_alpha(accent, "2b"),
        "ghost_element.background": TRANSPARENT,
        "ghost_element.hover": hover,
        "ghost_element.active": selected,
        "ghost_element.selected": selected,
        "ghost_element.disabled": TRANSPARENT,
        "text": ui_text,
        "text.muted": muted_text,
        "text.placeholder": g("input.placeholderForeground") or muted_text,
        "text.disabled": disabled_text,
        "text.accent": accent,
        "icon": g("icon.foreground") or ui_text,
        "icon.muted": g("activityBar.inactiveForeground") or muted_text,
        "icon.disabled": disabled_text,
        "icon.placeholder": muted_text,
        "icon.accent": accent,
        "status_bar.background": shell_bg,
        "title_bar.background": shell_bg,
        "title_bar.inactive_background": shell_bg,
        "toolbar.background": editor_bg,
        "tab_bar.background": shell_bg,
        "tab.inactive_background": shell_bg,
        "tab.active_background": elevated_bg if unbordered else editor_bg,
        "search.match_background": g("editor.findMatchHighlightBackground"),
        "search.active_match_background": g("editor.findMatchBackground"),
        "panel.background": shell_bg,
        "panel.focused_border": TRANSPARENT,
        "panel.indent_guide": g("tree.indentGuidesStroke", "editorIndentGuide.background"),
        "panel.indent_guide_active": g("editorIndentGuide.activeBackground", "tree.indentGuidesStroke"),
        "panel.indent_guide_hover": g("editorIndentGuide.activeBackground", "tree.indentGuidesStroke"),
        "pane.focused_border": TRANSPARENT,
        "pane_group.border": border,
        "scrollbar.thumb.background": g("scrollbarSlider.background"),
        "scrollbar.thumb.hover_background": g("scrollbarSlider.hoverBackground"),
        "scrollbar.thumb.active_background": g("scrollbarSlider.activeBackground"),
        "scrollbar.thumb.border": TRANSPARENT,
        "scrollbar.track.background": TRANSPARENT,
        "scrollbar.track.border": TRANSPARENT,
        "minimap.thumb.background": g("scrollbarSlider.background"),
        "minimap.thumb.hover_background": g("scrollbarSlider.hoverBackground"),
        "minimap.thumb.active_background": g("scrollbarSlider.activeBackground"),
        "minimap.thumb.border": TRANSPARENT,
        "editor.foreground": fg,
        "editor.background": editor_bg,
        "editor.gutter.background": editor_bg,
        "editor.subheader.background": elevated_bg,
        "editor.active_line.background": line_bg,
        "editor.highlighted_line.background": line_bg,
        "editor.line_number": g("editorLineNumber.foreground"),
        "editor.active_line_number": g("editorLineNumber.activeForeground") or fg,
        "editor.hover_line_number": g("editorLineNumber.activeForeground") or fg,
        "editor.invisible": g("editorWhitespace.foreground"),
        "editor.wrap_guide": g("editorIndentGuide.background"),
        "editor.active_wrap_guide": g("editorIndentGuide.activeBackground"),
        "editor.indent_guide": g("editorIndentGuide.background"),
        "editor.indent_guide_active": g("editorIndentGuide.activeBackground"),
        "editor.document_highlight.read_background": g("editor.wordHighlightBackground"),
        "editor.document_highlight.write_background": g("editor.wordHighlightStrongBackground"),
        "editor.document_highlight.bracket_background": g("editorBracketMatch.background"),
        "link_text.hover": g("textLink.activeForeground", "textLink.foreground"),
        "terminal.background": editor_bg,
        "terminal.foreground": g("terminal.foreground") or fg,
        "terminal.ansi.background": editor_bg,
        "terminal.bright_foreground": g("terminal.ansiBrightWhite") or fg,
        "terminal.dim_foreground": muted_text,
    }

    for name in ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white"):
        t = name.capitalize()
        style[f"terminal.ansi.{name}"] = g(f"terminal.ansi{t}")
        style[f"terminal.ansi.bright_{name}"] = g(f"terminal.ansiBright{t}")

    statuses = {
        "error": g("editorError.foreground", "errorForeground") or git["deleted"],
        "warning": g("editorWarning.foreground") or git["modified"],
        "info": g("editorInfo.foreground") or accent,
        "hint": g("editorHint.foreground", "editorInlayHint.foreground") or muted_text,
        "success": git["added"],
        "created": git["added"],
        "modified": git["modified"],
        "deleted": git["deleted"],
        "renamed": git["added"],
        "conflict": git["conflict"],
        "ignored": git["ignored"],
        "hidden": disabled_text,
        "unreachable": muted_text,
        "predictive": g("editorGhostText.foreground") or muted_text,
    }
    for name, val in statuses.items():
        if not val:
            continue
        style[name] = val
        alpha = "2e" if name in ("created", "deleted", "modified") else "1f"
        style[f"{name}.background"] = with_alpha(val, alpha)
        style[f"{name}.border"] = with_alpha(val, "66")
    style["hint.background"] = elevated_bg

    style["version_control.added"] = g_add
    style["version_control.modified"] = g_mod
    style["version_control.deleted"] = g_del
    style["version_control.renamed"] = g_mod
    style["version_control.conflict"] = g_con
    style["version_control.ignored"] = git["ignored"]
    style["version_control.word_added"] = g_add + "5c"
    style["version_control.word_deleted"] = g_del + "5c"

    player_colors = [accent] + [
        g(f"terminal.ansi{n}") for n in ("Blue", "Magenta", "Yellow", "Green", "Cyan", "Red")
    ]
    style["players"] = [
        {
            "cursor": cursor if i == 0 else p,
            "background": p,
            "selection": selection if i == 0 else with_alpha(p, "3d"),
        }
        for i, p in enumerate(player_colors)
        if p
    ]
    style["accents"] = [
        c[f"editorBracketHighlight.foreground{i}"]
        for i in range(1, 7)
        if c.get(f"editorBracketHighlight.foreground{i}")
    ] or [p for p in player_colors[:6] if p]

    style["editor.invisible"] = visible_invisible(fg, selection, editor_bg)
    style["syntax"] = build_folke_syntax(git) if folke else build_syntax(theme, c, git)
    return {k: v for k, v in style.items() if v is not None}


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    OUT.mkdir(exist_ok=True)
    themes = []
    for fname, label, appearance, all_black, folke in VARIANTS:
        raw = json.loads((source / fname).read_text())
        for unbordered in (False, True):
            name = f"{label} Unbordered" if unbordered else label
            themes.append({
                "name": name,
                "appearance": appearance,
                "style": build_style(raw, appearance, unbordered=unbordered, all_black=all_black, folke=folke),
            })

    family = {"$schema": SCHEMA, "name": "Tokyo Night", "author": AUTHOR, "themes": themes}
    (OUT / "tokyo-night.json").write_text(json.dumps(family, indent=2, ensure_ascii=False) + "\n")
    for t in themes:
        print(f"themes/tokyo-night.json: {t['name']} ({t['appearance']})")


if __name__ == "__main__":
    main()
