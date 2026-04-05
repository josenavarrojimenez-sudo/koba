---
name: apolo-plan-swift-automated
description: Automated construction estimating for Apolo - replicates AI cowork workflow with dynamic models, M.07 reference data, and Claude-style HTML dashboards.
category: koba-infra
---

# Apolo PlanSwift Automated

## Overview
Apolo replicates the AI construction automation workflow (estimating, contract management, scheduling) using our model stack. Inspired by Tim Fairley's "Claude Cowork for Construction" methodology.

## 3-Step Model Routing (Dynamic)
1. **Vision:** `google/gemini-2.5-flash` — Reads blueprints/PDFs, extracts areas/walls/openings
2. **Math:** `google/gemini-2.5-flash-thinking` — Calculates quantities using real data (FREE)
3. **Output:** `google/gemini-2.5-flash` or `qwen/qwen3.5-235b-a22b:free` — Generates Excel + HTML (FREE)

Total cost per execution: ~$0.012

## Data Sources (ALWAYS load before calculating)
- `/root/koba/agents/rendimientos_db.json` — Yields per m3/m2
- `/root/koba/agents/materiales_m07.json` — 343 material items with real prices
- `/root/koba/agents/obra_gris_acabados_format.json` — M.07 input format
- `/root/koba/agents/electrico_format.json` — Electrical quantities
- `/root/koba/agents/mecanico_format.json` — Mechanical/sanitary quantities
- `/root/koba/agents/costo_personal.json` — Crew costs with social charges
- `/root/koba/agents/equipos_precios.json` — Equipment and subcontractor prices

## CRITICAL RULE: "Global" Items
When a budget item says "Global" or has no unit quantities:
1. Use PRESUPUESTO_M.07.xlsx as reference for proportional weights
2. Scale by area: `new_value = m07_value * (new_area / m07_area)`
3. NEVER leave items at zero
4. Use the M.07 house as the baseline for all estimates

## Output Deliverables
### 1. Enhanced Excel (4 sheets, Claude-style formatting)
- **Detallado:** Master budget with ALL individual material line items (NOT just categories). Same structure as PRESUPUESTO_M.07.xlsx "Detallado" sheet: CODIGO, Descripcion, Cantidad, Unidad, Unit Mater, Unit MO, Unit Sub, Totals. Subtotals by category, grand totals.
- **Descompuesto:** Complete materials list from data sources
- **Resumen Presupuesto:** Business Central format (compact, upload-ready)
- **Cronograma:** Phased Gantt-style schedule with dependencies

### 2. HTML Dashboard (Claude UI style — clean, minimal, modern)
- Summary cards (Total, Directo, Indirectos, Costo/m2, Area, TC)
- Doughnut chart (cost distribution: Mat/MO/Sub/Ind)
- Stacked bar chart (Mat vs MO vs Sub by category)
- Category summary cards (Obra Gris, Acabados, Especialidades)
- **Detailed Table** with all line items, unit costs, totals, CRC/m2, USD
- **Filters:** by category dropdown + text search
- **Gantt chart** (weekly bars with costs)
- **Weekly cost chart** (costo por semana bar)
- **Cumulative cost** (line chart showing S-curve)
- **Monthly projection** (bar chart + monthly table with %)
- **Indirectos breakdown** (Admin 40%, Gastos 30%, Imprevistos 30%)
- Dark mode toggle
- Responsive design
- Uses Chart.js via CDN
- **Currency:** ₡ symbol with proper formatting, USD conversion

### 3. Markdown Workspace Files
- `00_WORKFLOW.md` — Pipeline and status
- `TASKS.md` — Checklist with checkboxes
- `OUTPUT.md` — Final summary with budget tables

## Workspace Structure
```
/root/koba/workspaces/{project}/
├── 00_WORKFLOW.md
├── TASKS.md
├── NOTES.md
├── OUTPUT.md
└── data/
    ├── {project}.pdf (copy of source)
    ├── presupuesto_{project}.xlsx
    ├── presupuesto_{project}_final.json
    └── reporte_{project}.html
```

## Validation Rule: Cost/m2 Comparison
After calculating, ALWAYS compare against M.07 reference:
- M.07 (182.38 m2): ~₡276,089/m2 (₡50.35M total)
- K-18 (85.27 m2): ~₡286,534/m2 (₡24.43M total) — 103.8% of M.07
- If ratio is 80-150%, it's valid. Outside that range, flag for review.

## Paperclip Workflow Rule
1. Koba creates workspace + assigns task
2. Apolo executes using model pipeline
3. If blocked: Agent creates issue in Paperclip, notifies Koba
4. Koba resolves or escalates to Jose
5. Apolo fills OUTPUT.md when done
6. Koba delivers results to Jose

**Agents report UP: Apolo → Koba → Jose. Never direct to Jose.**

## Pitfalls & Lessons Learned

### 1. openpyxl Colors Require ARGB Format
- Use `FF2563EB` NOT `#2563EB` — openpyxl on newer Python requires 8-char ARGB
- Helper: `def F(rgb): return "FF" + rgb[1:] if rgb.startswith("#") else rgb`

### 2. Bridge Payload Size Limits (~8KB max per request)
- Large scripts fail silently with HTTP 500
- ALWAYS split into chunks of 4-7KB using base64 encode/decode
- Pattern: `echo 'B64' > /tmp/x.b64` then `base64 -d /tmp/x.b64 > /tmp/x.py && python3 /tmp/x.py`
- If bridge returns 500, the payload was too large — try smaller chunks

### 3. Python f-string + JavaScript = Syntax Errors
- JS uses `{}` which Python f-strings consume as format specifiers
- Solution: Build JS as plain string concatenation, NOT f-strings
- For inline data: Pre-compute ALL values in Python, inject as pre-rendered strings
- Avoid: `h.append(f'...{D.indir*0.3}...')` — can produce JS syntax errors
- Use instead: Pre-compute `val = indir * 0.3` then `h.append(str(val))`

### 4. HTML Dashboard Must Be COMPLETE (no empty sections)
- Every chart canvas must have corresponding JS Chart initialization
- Every element id referenced in JS must exist in HTML — check with grep before deploying
- Test: `grep -c 'addEventListener' file.html` should match number of interactive elements
- Tabs need explicit event listeners OR onclick handlers — CSS alone won't show/hide panes

### 5. "Detallado" Tab Must Include Individual MATERIALS (not just activities)
- Like the original PRESUPUESTO_M.07.xlsx "Detallado" sheet
- Each material line item: CODIGO, CODIGO ACUMATICA, N, Descripcion, Cantidad, Unidad, Unit mater, Unit MO, Unit Sub, totals
- NOT just category summaries — every single material/line from the source

### 6. Currency Formatting (Spanish CRC)
- Use `₡` symbol (₡ not "CRC" or "$")
- Spanish format: `13983,45` NOT `13,983.45`
- Use `format(n, ',')` for Python output, or `toLocaleString('es-CR')` in JS
- Separate thousands with commas, decimals with periods is the Spanish Costa Rican convention

### 7. File Transfer to/from VPS
- To get files FROM VPS: `base64 -w 0 /path/to/file` via bridge, then decode locally
- To send files TO VPS: Write locally, base64 encode, send in chunks via bridge, decode on host
- Excel files stay intact through base64 transport
| Task | Model | Cost |
|---|---|---|
| Vision (10-50 pages) | gemini-2.5-flash | ~$0.010 |
| Math/Calculations | gemini-2.5-flash-thinking | FREE |
| Output/Excel | gemini-2.5-flash | ~$0.002 |
| **Total** | | **~$0.012** |
