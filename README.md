# Clase 10 — AI Governance Harness

Harness educativo para integrar monitoreo, evaluación, recuperación de información, memoria conversacional separada, revisión humana y trazabilidad en un agente de IA.

## Objetivo

- vigilar cambios en las entradas sin confundirlos con una caída del rendimiento;
- comparar predicciones con resultados reales cuando estén disponibles;
- investigar alertas antes de cambiar el sistema;
- separar recuperación de fuentes confiables y memoria conversacional;
- pausar acciones con impacto para aprobación humana;
- registrar decisiones, fuentes, responsables y resultados;
- documentar versiones y un procedimiento de reversión.

## Proveedor LLM

Compatible con **Groq** (recomendado para una puesta en marcha rápida) o **Hugging Face Inference API**. El proyecto también tiene modo `mock` para ejecutar pruebas sin claves ni conexión.

Nunca guardes tokens en el código ni los subas a Git. Copiá `.env.example` como `.env` y completá solo el proveedor que vayas a usar.

## Instalación

### Windows 10/11
1. Descomprimí el ZIP en una carpeta local.
2. Abrí PowerShell dentro de la carpeta.
3. Ejecutá:
   ```powershell
   .\install.ps1
   ```
4. Editá `.env` y configurá `LLM_PROVIDER=groq` y `GROQ_API_KEY`, o `LLM_PROVIDER=huggingface` y `HF_TOKEN`.
5. Iniciá:
   ```powershell
   .\run.ps1
   ```
6. Abrí la URL local que muestra Streamlit (normalmente `http://localhost:8501`).
7. También puede instalarse mediante #install.bat

### Linux
1. Descomprimí el ZIP y entrá a la carpeta.
2. Ejecutá:
   ```bash
   chmod +x install.sh run.sh
   ./install.sh
   ```
3. Editá `.env` y configurá el proveedor/token.
4. Ejecutá `./run.sh`.

### Instalación manual
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env  # en PowerShell: Copy-Item .env.example .env
streamlit run app.py
```

## Uso

En la aplicación:
1. Consultá información del centro cultural desde la base local de conocimiento.
2. El contexto de conversación se conserva separado de las fuentes recuperadas.
3. Una solicitud de reserva se prepara como **propuesta**, no se ejecuta directamente.
4. Revisá la propuesta en la sección de aprobación humana y aprobá/rechazá.
5. Consultá eventos de auditoría y monitoreo.
6. Para el pronóstico, ingresá el valor predicho y luego el valor real cuando se conozca; el sistema registra el error.

## Seguridad y límites

- El prototipo no conecta con sistemas reales de reservas ni crea reservas reales.
- Las reservas son simuladas y requieren aprobación explícita.
- La aplicación está pensada para uso local/educativo; antes de producción se necesitan autenticación, autorización por roles, cifrado, gestión de secretos, retención definida, copias de seguridad y revisión de privacidad.
- Los logs evitan guardar el token y limitan el contexto guardado. No ingreses datos personales sensibles.
- Las métricas de cambio de datos son señales exploratorias, no evidencia automática de deterioro.
- La evaluación del modelo requiere resultados reales representativos.
- El sistema no garantiza cumplimiento normativo. ISO/IEC 42001 se usa como marco conceptual, no como certificación.

## Estructura

```text
app.py                  Interfaz Streamlit
governance_harness.py   Lógica de gobernanza, auditoría y monitoreo
llm_client.py           Adaptadores Groq / Hugging Face / mock
knowledge/               Fuentes aprobadas de demostración
data/                    Base SQLite creada automáticamente
tests/                   Pruebas unitarias
install.ps1 / install.sh Instaladores
run.ps1 / run.sh         Lanzadores
```

## Pruebas

```bash
python -m unittest discover -s tests -v
```
