# Arquitectura y trazabilidad

## Componentes
- **Interfaz Streamlit:** chat y vistas de revisión, monitoreo y auditoría.
- **Agente:** decide entre consulta informativa y propuesta de reserva.
- **Recuperación:** carga archivos Markdown de `knowledge/` como fuentes aprobadas.
- **Memoria conversacional:** contexto de sesión en memoria de Streamlit; no se usa como fuente autoritativa.
- **Harness:** SQLite para eventos, propuestas, predicciones y observaciones.
- **Adaptadores LLM:** Groq, Hugging Face Inference API y modo mock.

## Flujo de reserva
Solicitud → propuesta pendiente → revisión humana → decisión registrada. La aprobación solo simula una confirmación y no invoca un sistema externo.

## Flujo de monitoreo
Definición de métricas → línea base conceptual → registro de predicción → resultado real → cálculo de error → investigación → evaluación independiente → aprobación y versionado → monitoreo posterior.

## Registro de ejemplo
```json
{
  "session_id": "local-session",
  "event": "reservation_human_review",
  "source_ref": "agenda_centro_cultural.md",
  "tool": "reservation_simulator",
  "decision": "approved",
  "human_review": "approved",
  "result": "simulated_reservation_confirmed"
}
```

## Límites conocidos
- La detección de cambio es una señal categórica exploratoria simple, no una prueba estadística formal.
- El ejemplo no implementa autenticación ni RBAC.
- La memoria vive en la sesión y no persiste entre sesiones.
- La fuente local es de demostración.
- No es un sistema de producción ni una certificación de conformidad.
