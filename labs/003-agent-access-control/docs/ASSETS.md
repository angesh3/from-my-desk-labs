# Lab 003 visual assets

## Teaching diagrams

| Diagram | Teaches | Repo path | Public URL |
| --- | --- | --- | --- |
| NAC comparison | Traditional NAC vs agent access control | `static/nac-comparison.svg` | `/static/labs/003/nac-comparison.svg` |
| Live authority evaluation | Canonical evaluation groups and decision flow | `static/live-authority-evaluation.svg` | `/static/labs/003/live-authority-evaluation.svg` |
| Management plane | Registry, inventory, profiles → gateway | `static/management-plane.svg` | `/static/labs/003/management-plane.svg` |
| Restricted mode | Restricted recovery without executing protected action | `static/restricted-mode.svg` | `/static/labs/003/restricted-mode.svg` |
| Re-evaluation after change | Step-up and fresh evaluation after material change | `static/reevaluation-change.svg` | `/static/labs/003/reevaluation-change.svg` |

## Runtime JavaScript

| File | Public URL |
| --- | --- |
| `static/lab.js` | `/static/labs/003/lab.js` |

## Inkscape PNG export

From the repository root, export presentation-quality PNGs for slides or newsletters:

```bash
inkscape labs/003-agent-access-control/static/nac-comparison.svg \
  --export-type=png --export-filename=labs/003-agent-access-control/static/nac-comparison.png \
  --export-width=1920

inkscape labs/003-agent-access-control/static/live-authority-evaluation.svg \
  --export-type=png --export-filename=labs/003-agent-access-control/static/live-authority-evaluation.png \
  --export-width=1920

inkscape labs/003-agent-access-control/static/management-plane.svg \
  --export-type=png --export-filename=labs/003-agent-access-control/static/management-plane.png \
  --export-width=1920

inkscape labs/003-agent-access-control/static/restricted-mode.svg \
  --export-type=png --export-filename=labs/003-agent-access-control/static/restricted-mode.png \
  --export-width=1920

inkscape labs/003-agent-access-control/static/reevaluation-change.svg \
  --export-type=png --export-filename=labs/003-agent-access-control/static/reevaluation-change.png \
  --export-width=1920
```

PNG exports are optional and not required for website startup validation.
