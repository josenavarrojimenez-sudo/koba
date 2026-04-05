---
name: apolo-m07-reference-and-validation
description: Reference budget structure, Global items rule, and M.07 validation for Apolo construction estimating.
category: koba-infra
---

# Apolo M.07 Reference & Validation

## M.07 Reference Budget (Casa Santorini Azotea)
- **Area:** 182.38 m²
- **Total Directo:** ₡45,775,546
- **Con Indirectos (10%):** ₡50,353,100
- **Costo/m²:** ₡276,089
- **USD (TC 515):** $97,773
- **Category breakdown:**
  - Obra Gris: ₡21.4M / $41,569
  - Acabados: ₡12.9M / $25,141
  - Electrico: ₡3.0M / $5,805
  - Mecanico: ₡1.2M / $2,339

## Global Items Rule (CRITICAL)
When a budget item says "Global" or has no unitary quantities:
1. Use the M.07 reference budget as the weight source
2. Scale proportionally to the new house area:
   ```
   new_value = m07_value * (new_area / 182.38)
   ```
3. Apply the same category distribution weights
4. **NEVER** leave an item at zero or skip it

## Validation Rule
After calculating ANY budget:
1. Compute costo/m² of the new project
2. Compare against M.07 baseline (₡276,089/m²)
3. If ratio is between 80% and 150% → VALID
4. If ratio > 150% → REVIEW, something is overestimated
5. If ratio < 80% → REVIEW, something is missing
6. **Example:** K-18 at ₡286,534/m² = 103.8% of M.07 → ✅ VALID

## Data Sources
- `/root/koba/agents/rendimientos_db.json`
- `/root/koba/agents/materiales_m07.json`
- `/root/koba/agents/mano_obra_precios.json`
- `/root/koba/agents/equipos_precios.json`
- `/root/koba/agents/costo_personal.json`
- `/root/koba/agents/resumen_presupuesto_format.json`
- `/root/koba/agents/detallado_format.json`

## Output Formats
1. **Excel (4 sheets):** Detallado, Descompuesto, Resumen Presupuesto, Cronograma
2. **HTML Dashboard:** Filterable table + Pie/Bar/Gantt charts + Dark mode (Claude-style UI)
3. **Markdown summary:** Total, breakdown by category, recomendaciones

## Technical Pitfalls
- openpyxl colors need FF prefix: `"FF059669"` not `"#059669"`. Use `F(c): return "FF"+c[1:] if c.startswith("#") else c`
- Bridge payload limit: >6KB scripts need base64 chunking (7000 char intervals)
- f-strings + JavaScript `{}` = SyntaxError. Use string concatenation for HTML with JS
