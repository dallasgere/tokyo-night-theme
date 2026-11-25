# Tokyo Night Theme

Tokyo Night dark themes for [Zed](https://zed.dev) (`Tokyo Night` and `Tokyo Night Black`), generated from the [Vine](https://github.com/dallasgere/vine) VS Code themes with syntax colors from `folke/tokyonight.nvim` (moon).

## Install locally

1. In Zed, open the command palette and run `zed: install dev extension`.
2. Select this folder.
3. Run `theme selector: toggle` and pick `Tokyo Night` or `Tokyo Night Black`.

Or copy the files in `themes/` into `~/.config/zed/themes/`.

## Regenerating

The theme files are generated from the Tokyo Night VS Code themes in the [Vine](https://github.com/dallasgere/vine) repo:

```bash
python3 scripts/build.py ../vine/themes
```

The script maps each VS Code workbench color to its closest Zed equivalent, resolves every Zed syntax capture against the VS Code `tokenColors` and `semanticTokenColors` rules, and runs a contrast pass so surfaces, dividers, and syntax stay crisp and readable.

## Differences from VS Code

- Zed highlights with tree-sitter rather than TextMate grammars, so some language-specific distinctions collapse to one color per capture.
- Zed theme syntax styles cannot underline or strike through text, so invalid and deprecated code use color only.
