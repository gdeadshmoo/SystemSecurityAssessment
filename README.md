# System Security Assessment

An AI-enabled, repeatable program for assessing the security of whole systems. AI does the work;
humans own the judgment.

| What | Where |
|---|---|
| How-to guide | [`HOWTO.md`](HOWTO.md) |
| Claude skill | [`skills/assessing-system-security/SKILL.md`](skills/assessing-system-security/SKILL.md) |
| Presentation (PDF) | [`presentation/deck.pdf`](presentation/deck.pdf) |
| Presentation (browser, arrow keys to navigate) | [`presentation/deck.html`](presentation/deck.html) |
| Presentation source (Claude Slides files) | [`presentation/source/`](presentation/source/) |

*Assess Systems the Way You Build Them*: Bruce Potter, Jawncon 0x03.

## Rebuilding the deck

`deck.html` is generated from the slide sources:

```bash
python3 presentation/build_deck.py
```

To regenerate the PDF, print `deck.html` from Chrome or Chromium (background graphics on, no
margins), or run headless:

```bash
chromium --headless --no-pdf-header-footer --print-to-pdf=presentation/deck.pdf presentation/deck.html
```
