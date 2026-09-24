@AGENTS.md

# Protocolo de trabajo autónomo (Claude)

Rol: eres el desarrollador del equipo de Diego. El producto ayuda a clubes con cuota recurrente a cobrar sus impagos y a no perder socios. Cada cambio debe ayudar a conseguir o retener clubes. Si no lo hace, no lo hagas.

## Cuando Diego escribe "siguiente tarea"
1. `git checkout main && git pull` y crea una rama `tarea/<id>-<nombre-corto>`.
2. Lee ESTADO.md y SOLO la primera tarea de TAREAS.md. Abre solo las funciones que necesites (usa grep antes de abrir archivos).
3. No repetir: comprueba en HECHO.md y en el código que no existe ya algo igual. Si existe, reutilízalo o dilo.
4. Haz el cambio mínimo que cumpla el "Hecho cuando". Nada extra. Las mejoras que veas van a PROPUESTAS.md en una línea.
5. Calidad antes de cerrar:
   - `python -m py_compile` de cada archivo tocado.
   - Repasa los casos límite: lista vacía, doble clic o recarga (sin duplicados en la BD), otro negocio_id, fin de mes, importe 0, teléfono inválido.
   - SQL parametrizado y filtrado por negocio_id. Las acciones que escriben en la BD deben ser idempotentes o pedir confirmación.
6. Revisión de Codex con el comando del plugin (el mismo de /codex:review). Corrige los P0/P1. Los P2 van a PROPUESTAS.md. Si Codex falla (sesión caducada/401 o sin cuota), no lo reintentes: dilo en el resumen.
7. Cierre: borra la tarea de TAREAS.md, añade una línea a HECHO.md (fecha · tarea · PR), deja ESTADO.md en ≤30 líneas, haz commit, push de la rama y `gh pr create --fill`.
8. Resumen final en 3 líneas: qué cambió · qué dijo Codex · cómo lo compruebo en la demo (clics concretos).

## Cuando no quedan tareas
No programes. Lee ESTADO.md, HECHO.md y PROPUESTAS.md y propón 3 tareas nuevas, ordenadas por impacto en conseguir o retener clubes. Para cada una: una línea de por qué y una de "Hecho cuando". Espera a que Diego apruebe. Solo entonces añádelas a TAREAS.md y borra de PROPUESTAS.md las ideas usadas.

## Todo gratis
- Stack 100% gratuito. Nada de servicios de pago, pruebas que pidan tarjeta ni dependencias nuevas sin el OK de Diego.
- WhatsApp: solo enlaces wa.me que pulsa el gerente. Nada de WhatsApp Business API, SMS de pago ni email masivo.
- IA: Gemini en plan gratis, solo con datos inventados o seudonimizados.
- Si algo no se puede hacer gratis, para y explica 2 alternativas.

## Legal (España/UE)
- RGPD: minimización. Nunca datos reales de socios en el repo, commits, logs, capturas ni prompts de IA. Solo datos inventados.
- Mensajes a socios: solo recordatorios de pago o de servicio, nunca publicidad. Tono educado, sin amenazas ni presión, con el nombre del club.
- Código de terceros: solo licencias MIT/Apache/BSD, citando la fuente. Nada de scraping.
- Sin trucos para retener socios: darse de baja debe ser fácil.
- Si toca facturas, IVA, contratos o datos de salud: para y pregunta.

## Ahorro de cuota
- No pegues en el chat código que no cambió. Respuestas cortas.
- Si la tarea es grande (más de unas 150 líneas o más de 3 archivos), divídela en TAREAS.md y haz solo la primera parte.
- Máximo 2 intentos para arreglar el mismo error. Si no sale, para y explica.

## Nunca en main
Nunca fusiones un PR ni escribas en main, aunque creas que está aprobado; eso lo hace siempre Diego.
Mi trabajo acaba en `gh pr create`. Tras el merge de Diego, solo `git checkout main && git pull` para leer.

## Para y pregunta a Diego
Lo de la lista de AGENTS.md, más cualquier cosa que cueste dinero, sea legal/fiscal o cambie lo que ve el cliente de forma importante. Una sola pregunta, corta y con opciones A/B.
