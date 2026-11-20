from pathlib import Path
import sys

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR / "2_model_implementation"))

from modelo import DataValidationError, load_instance, solve_instance


st.set_page_config(
    page_title="Planificacion optima de actividades",
    layout="wide",
)

st.title("Planificacion optima de actividades")
st.caption("Modelo binario de seleccion y asignacion")

SCENARIOS = {
    "Personalizado": (0.4, 0.4, 0.2),
    "Prioriza asistencia": (1.0, 0.0, 0.0),
    "Prioriza valoracion": (0.0, 1.0, 0.0),
    "Prioriza numero de actividades": (0.1, 0.1, 0.8),
}

try:
    instance = load_instance()
except DataValidationError as exc:
    st.error(f"Error de datos. No se pudo cargar la instancia: {exc}")
    st.stop()

params = instance["parametros"]

scenario = st.segmented_control(
    "Escenario",
    list(SCENARIOS.keys()),
    default="Personalizado",
)

scenario_name = scenario or "Personalizado"

if scenario_name == "Personalizado":
    default_weights = (
        float(params["w_A"]),
        float(params["w_V"]),
        float(params["w_N"]),
    )
else:
    default_weights = SCENARIOS[scenario_name]

with st.container(border=True):
    budget = st.number_input(
        "Presupuesto",
        min_value=0.0,
        value=float(params["presupuesto"]),
        step=100.0,
    )
    w_A = st.slider("Peso de asistencia", 0.0, 1.0, default_weights[0], 0.1)
    w_V = st.slider("Peso de valoracion", 0.0, 1.0, default_weights[1], 0.1)
    w_N = st.slider("Peso de numero de actividades", 0.0, 1.0, default_weights[2], 0.1)

run = st.button(
    "Resolver modelo",
    type="primary",
    icon=":material/play_arrow:",
)

if run:
    weights = (float(w_A), float(w_V), float(w_N))
    if sum(weights) == 0:
        st.error("Los tres pesos no pueden ser cero.")
    else:
        with st.spinner("Resolviendo el modelo..."):
            result = solve_instance(instance, float(budget), weights)

        if result["status"] == "SolverError":
            st.error(
                "Error del solver. "
                + result.get("error", "No se pudo ejecutar el solver.")
            )
        elif result["status"] != "Optimal":
            st.warning(
                "Instancia sin solucion. "
                "El problema es inviable con los parametros actuales."
            )
        else:
            assignments = result["assignments"]
            selected = set(result["selected"])
            activities = instance["actividades"].copy()
            activities["estado"] = activities["id"].apply(
                lambda activity_id: "Seleccionada"
                if int(activity_id) in selected
                else "Descartada"
            )

            selected_rows = activities[activities["id"].isin(selected)]
            attendance = int(selected_rows["asistencia"].sum())
            rating = float(selected_rows["valoracion"].sum())
            cost = float(selected_rows["coste"].sum())

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Actividades", len(selected))
            col2.metric("Asistencia", f"{attendance:,}".replace(",", "."))
            col3.metric("Valoracion", f"{rating:.1f}")
            col4.metric("Coste", f"{cost:,.0f}".replace(",", "."))

            st.subheader("Actividades seleccionadas")
            selected_table = activities[activities["estado"] == "Seleccionada"][
                ["id", "nombre", "duracion", "asistencia", "valoracion", "coste"]
            ].rename(
                columns={
                    "id": "ID",
                    "nombre": "Actividad",
                    "duracion": "Duracion",
                    "asistencia": "Asistencia",
                    "valoracion": "Valoracion",
                    "coste": "Coste",
                }
            )
            st.dataframe(
                selected_table,
                hide_index=True,
                width="stretch",
                alt="Tabla de actividades seleccionadas por el modelo",
            )

            st.subheader("Asignacion")
            if assignments.empty:
                st.info("No hay actividades asignadas.")
            else:
                st.dataframe(
                    assignments.rename(
                        columns={
                            "actividad": "ID",
                            "nombre": "Actividad",
                            "espacio": "Espacio ID",
                            "nombre_espacio": "Espacio",
                            "inicio": "Franja inicio",
                            "fin": "Franja fin",
                        }
                    ),
                    hide_index=True,
                    width="stretch",
                    alt="Asignacion de actividades a espacios y franjas",
                )

            st.subheader("Actividades descartadas")
            discarded = activities[activities["estado"] == "Descartada"][
                ["id", "nombre", "coste"]
            ].rename(
                columns={"id": "ID", "nombre": "Actividad", "coste": "Coste"}
            )
            st.dataframe(
                discarded,
                hide_index=True,
                width="stretch",
                alt="Tabla de actividades descartadas por el modelo",
            )

            export = activities[
                ["id", "nombre", "estado", "duracion", "asistencia",
                 "valoracion", "coste", "obligatoria"]
            ].rename(
                columns={
                    "id": "ID",
                    "nombre": "Actividad",
                    "estado": "Estado",
                    "duracion": "Duracion",
                    "asistencia": "Asistencia",
                    "valoracion": "Valoracion",
                    "coste": "Coste",
                    "obligatoria": "Obligatoria",
                }
            )
            st.download_button(
                "Descargar resultados CSV",
                data=export.to_csv(index=False).encode("utf-8"),
                file_name="resultados_planificacion.csv",
                mime="text/csv",
                icon=":material/download:",
                width="stretch",
            )
