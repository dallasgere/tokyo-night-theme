# Tokyo Night Theme

Faithful [Zed](https://zed.dev) port of [tokyo-night/tokyo-night-vscode-theme](https://github.com/tokyo-night/tokyo-night-vscode-theme) (Tokyo Night, Storm, Light, and an all-black variant — each with bordered and unbordered styles) packaged in a single `themes/tokyo-night.json` file, with harmonized crisp git diff colors, clean file selection, and a `#ffffff` cursor on dark themes.

## Variants (12 total)

- **Tokyo Night** / **Tokyo Night Unbordered**
- **Tokyo Night Storm** / **Tokyo Night Storm Unbordered**
- **Tokyo Night Light** / **Tokyo Night Light Unbordered**
- **Tokyo Night Black** / **Tokyo Night Black Unbordered**
- **Tokyo Night (Folke)** / **Tokyo Night (Folke) Unbordered**
- **Tokyo Night (Folke) Black** / **Tokyo Night (Folke) Black Unbordered**

## Install locally

1. In Zed, open the command palette and run `zed: install dev extension`.
2. Select this folder.
3. Run `theme selector: toggle` and pick any `Tokyo Night` variant.

Or copy `themes/tokyo-night.json` into `~/.config/zed/themes/`.

## Regenerating

```bash
python3 scripts/build.py
```
