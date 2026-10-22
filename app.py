import os, glob
import streamlit as st
from dotenv import load_dotenv
from governance_harness import GovernanceHarness
from llm_client import generate, LLMError

load_dotenv()
st.set_page_config(page_title="Clase 10 | AI Governance Harness", page_icon="🧭", layout="wide")
h = GovernanceHarness()
st.title("Clase 10 — AI Governance Harness")
st.caption("Monitoreo · recuperación y memoria · revisión humana · trazabilidad")
st.info("Prototipo educativo: las reservas son simuladas. No se ejecutan acciones externas.")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "memory" not in st.session_state:
    st.session_state.memory = []

tabs = st.tabs(["Agente", "Revisión humana", "Monitoreo", "Auditoría"])

with tabs[0]:
    st.subheader("Agente del centro cultural")
    st.write("Consulta la agenda aprobada o prepara una propuesta de reserva.")
    files = glob.glob(os.path.join(os.getenv("KNOWLEDGE_DIR", "knowledge"), "*.md"))
    knowledge = "\n\n".join(open(p, encoding="utf-8").read() for p in files) if files else "No hay fuentes cargadas."
    with st.expander("Fuentes recuperables"):
        st.markdown(knowledge)
    for msg in st.session_state.chat_history[-12:]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ej.: ¿Qué actividades hay el jueves? / Quiero reservar la sala 2")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        h.audit("user_request_received", session_id="local-session", decision=prompt[:250],
                result="received", metadata={"memory_turns": min(len(st.session_state.memory), 8)})
        low = prompt.lower()
        if any(x in low for x in ["reserv", "sala", "booking"]):
            proposal = "Propuesta pendiente de revisión: " + prompt
            pid = h.propose_reservation(prompt, proposal)
            answer = f"Preparé una propuesta, pero no ejecutaré la reserva sin revisión humana. ID de propuesta: `{pid}`. Abrí la pestaña **Revisión humana** para evaluarla."
        else:
            system = (
                "Sos un asistente informativo de un centro cultural. Respondé en español, con claridad. "
                "Usá únicamente la fuente aprobada incluida en el mensaje para horarios y condiciones. "
                "Si la fuente no contiene la respuesta, decilo. No inventes datos ni confirmes reservas. "
                "La memoria conversacional es contexto, no una fuente institucional vigente."
            )
            context = "\n".join(f"- {m['role']}: {m['content']}" for m in st.session_state.memory[-8:])
            user_content = f"FUENTE APROBADA:\n{knowledge}\n\nCONTEXTO CONVERSACIONAL (no autoritativo):\n{context or '(vacío)'}\n\nCONSULTA:\n{prompt}"
            try:
                answer = generate([{"role":"system","content":system},
                                   {"role":"user","content":user_content}])
            except LLMError as e:
                answer = f"Error del proveedor: {e}. Verificá la configuración de .env."
        st.session_state.chat_history.append({"role":"assistant","content":answer})
        st.session_state.memory.extend([{"role":"user","content":prompt},{"role":"assistant","content":answer}])
        st.session_state.memory = st.session_state.memory[-int(os.getenv("MAX_MEMORY_TURNS", "8"))*2:]
        h.audit("assistant_response", session_id="local-session", source_ref="knowledge/*.md",
                tool="llm_or_reservation_proposal", decision=answer[:250], result="response_prepared")
        st.rerun()

with tabs[1]:
    st.subheader("Bandeja de revisión humana")
    pending = h.get_proposals("pending")
    if not pending:
        st.success("No hay propuestas pendientes.")
    for p in pending:
        with st.container(border=True):
            st.write(f"**ID:** `{p['id']}`")
            st.write(f"**Solicitud:** {p['request']}")
            st.write(f"**Propuesta:** {p['proposal']}")
            with st.form("review_"+p["id"]):
                reviewer = st.text_input("Responsable que revisa", key="reviewer_"+p["id"])
                note = st.text_area("Observación / fundamento", key="note_"+p["id"])
                c1, c2 = st.columns(2)
                approve = c1.form_submit_button("Aprobar (simulado)")
                reject = c2.form_submit_button("Rechazar")
                if approve or reject:
                    if not reviewer.strip():
                        st.error("Indicá quién revisa la propuesta.")
                    else:
                        try:
                            h.review_proposal(p["id"], bool(approve), reviewer, note)
                            st.success("Revisión registrada. No se realizó ninguna acción externa.")
                            st.rerun()
                        except ValueError as e:
                            st.error(str(e))
    with st.expander("Historial de propuestas"):
        st.dataframe(h.get_proposals(), use_container_width=True)

with tabs[2]:
    st.subheader("Monitoreo de predicciones")
    c1, c2, c3 = st.columns(3)
    with c1:
        predicted = st.number_input("Asistencia predicha", min_value=0.0, value=30.0, step=1.0)
        model_version = st.text_input("Versión del modelo", "demo-v1")
        segment = st.text_input("Grupo de casos", "general")
        if st.button("Registrar predicción"):
            pid = h.record_prediction(predicted, model_version, segment)
            st.session_state.last_prediction_id = pid
            st.success(f"Predicción registrada: {pid}")
    with c2:
        st.write("**Agregar resultado real**")
        predictions = [p for p in h.predictions(100) if p["actual"] is None]
        if predictions:
            opts = {f"{p['timestamp']} · predicción {p['predicted']} · {p['model_version']}": p["id"] for p in predictions}
            selected = st.selectbox("Predicción pendiente", list(opts.keys()))
            actual = st.number_input("Asistencia real observada", min_value=0.0, value=28.0, step=1.0)
            if st.button("Registrar resultado real"):
                try:
                    err = h.attach_actual(opts[selected], actual)
                    st.success(f"Resultado registrado. Error firmado: {err:.2f}")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
        else:
            st.caption("No hay predicciones pendientes.")
    with c3:
        st.write("**Señal de cambio en entradas**")
        feature = st.text_input("Nombre de característica", "tipo_actividad")
        value = st.text_input("Valor/categoría observada", "taller")
        if st.button("Guardar observación"):
            h.observe(feature, value)
            st.success("Observación guardada.")
        if st.button("Evaluar señal de cambio"):
            report = h.drift_report(feature)
            st.json(report)
    summary = h.performance_summary()
    st.metric("Predicciones con resultado real", summary["n"])
    if summary["mae"] is not None:
        a, b = st.columns(2)
        a.metric("MAE (error absoluto medio)", f"{summary['mae']:.2f}")
        b.metric("RMSE (raíz del error cuadrático medio)", f"{summary['rmse']:.2f}")
    st.caption("La señal de cambio de datos no equivale a deterioro del rendimiento. Las métricas se calculan solo cuando se registra el resultado real.")

with tabs[3]:
    st.subheader("Registro de auditoría")
    events = h.audit_events()
    if events:
        st.dataframe(events, use_container_width=True, hide_index=True)
    else:
        st.caption("Todavía no hay eventos.")
    st.caption("SQLite local. Para producción: autenticación, control de acceso, política de retención y protección de logs.")
