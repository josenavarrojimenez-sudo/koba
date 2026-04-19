# Koba Skills - Habilidades y Procedimientos

Este directorio contiene las **skills** de Koba — procedimientos reutilizables, guías especializadas y scripts para tareas específicas.

## ¿Qué son las Skills?

Las skills son **memoria procedural** de Koba — documentación de cómo realizar tareas complejas que hemos dominado. Cada skill incluye:
- **Cuándo usarla** — trigger conditions
- **Pasos numerados** — instrucciones exactas
- **Comandos específicos** — copy-paste ready
- **Pitfalls** — errores comunes y cómo evitarlos
- **Ejemplos** — casos de uso reales

## Skills Disponibles

### 🎙️ Creative

| Skill | Descripción |
|-------|-------------|
| [`elevenlabs-expressive-tts`](./elevenlabs-expressive-tts/SKILL.md) | Agregar etiquetas expresivas `[warm]`, `[excited]`, etc. para TTS de ElevenLabs v3 — hace la voz más natural y emocional |

### 🔍 Research

| Skill | Descripción |
|-------|-------------|
| [`web-content-extractor`](./web-content-extractor/SKILL.md) | Extraer contenido de páginas con Cloudflare/paywalls usando Jina.ai Reader — bypass de bot protection |

## Estructura de una Skill

```
skills/
├── <category>/
│   ├── <skill-name>/
│   │   ├── SKILL.md           # Guía principal (YAML frontmatter + markdown)
│   │   ├── scripts/           # Scripts ejecutables (opcional)
│   │   ├── templates/         # Plantillas reutilizables (opcional)
│   │   └── references/        # Documentación de referencia (opcional)
```

## Cómo Agregar una Nueva Skill

1. **Crear carpeta** con nombre descriptivo:
   ```bash
   mkdir -p skills/<category>/<skill-name>
   ```

2. **Crear SKILL.md** con esta estructura:
   ```markdown
   ---
   name: skill-name
   description: Breve descripción de lo que hace
   category: category-name
   ---
   
   # Título de la Skill
   
   ## When to Use
   
   ## Steps
   
   ## Examples
   
   ## Pitfalls
   ```

3. **Agregar scripts** si aplica en `scripts/`

4. **Commit y push**:
   ```bash
   git add skills/<skill-name>
   git commit -m "Add skill: <skill-name>"
   git push
   ```

## Cómo Usar una Skill

### Desde Hermes Agent

```
/load <skill-name>
```

### Desde Terminal

```bash
python3 skills/<category>/<skill-name>/scripts/<script>.py
```

### Como Referencia

Leer el `SKILL.md` directamente para consultar procedimientos.

## Skills Prioritarias para Crear

- [ ] `telegram-gateway-troubleshooting` — Diagnosticar bots conectados pero no responden
- [ ] `elevenlabs-direct-pipeline` — Pipeline completo TTS + sendVoice a Telegram
- [ ] `github-auth` — Configurar autenticación con gh CLI
- [ ] `session-search` — Buscar en sesiones pasadas eficientemente

## Reglas de Oro

1. **Skills son inmutables** — No editar después de crear (crear nueva versión si necesita cambios)
2. **Nombres descriptivos** — lowercase con guiones: `my-skill-name`
3. **Incluir ejemplos** — Al menos 2 ejemplos de uso real
4. **Documentar pitfalls** — Los errores que superaste son oro para el futuro
5. **Scripts ejecutables** — Si incluye scripts, hacerlos `chmod +x`

## Related

- [SOUL.md](../SOUL.md) — Identidad y comportamiento de Koba
- [docs/](../docs/) — Documentación técnica
- [scripts/](../scripts/) — Scripts utilitarios

---

*Última actualización: Abril 2026*
*Keep this updated as new skills are added!*
