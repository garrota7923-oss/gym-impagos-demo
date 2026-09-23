@AGENTS.md

## Solo para Claude
- Usa Sonnet para el día a día; Opus solo si Diego lo pide o para diseñar algo grande.
- Antes de programar algo de más de ~30 líneas, enseña un plan de 3–5 puntos y espera el OK de Diego.
- Tras cada cambio importante, propón a Diego pasar `/codex:review` (no lo lances tú sin preguntar: gasta su cuota de Codex).

## Modo automatico: "siguiente tarea"
Cuando Diego escriba "siguiente tarea" (esto manda sobre los puntos de arriba de plan+OK y de no lanzar Codex):
1. `git switch main && git pull`, y crea una rama nueva desde main (`git switch -c <nombre-corto-de-la-tarea>`).
2. Coge la primera tarea sin marcar (`- [ ]`) de TAREAS.md y hazla entera sin pedir OK al plan, siguiendo AGENTS.md. Solo pregunta si toca algo de la lista "PARA y pregunta" (excepto push de la rama nueva y el PR, que ya estan permitidos aqui).
3. Al acabar:
   - `python -m py_compile` de cada archivo tocado.
   - Revision de Codex (el mismo comando que usa `/codex:review`), en primer plano:
     `node "$(ls -d ~/.claude/plugins/cache/openai-codex/codex/*/ | tail -1)scripts/codex-companion.mjs" review --wait --base main`
   - Corrige lo P0/P1 que encuentre Codex (lo demas, solo anotalo).
   - Marca `[x]` en TAREAS.md y actualiza ESTADO.md.
   - Commit en la rama, `git push -u origin <rama>` y `gh pr create` contra main. Nunca push a main ni `gh pr merge`.
4. Termina con un resumen de 3 lineas: que cambio, que dijo Codex y como lo compruebo en la demo.
