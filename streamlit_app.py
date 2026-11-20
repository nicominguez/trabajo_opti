from pathlib import Path
import sys

import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "2_implementacion"))

from modelo import DataValidationError, load_instance, solve_instance  # ty: ignore[import-not-found]


st.set_page_config(page_title="Planificacion optima del evento", layout="wide")
st.title("Planificacion optima del evento")
st.caption("Seleccion y asignacion mediante programacion lineal entera")

try:
    instance = load_instance()
except DataValidationError as exc:
    st.error(f"Error de datos: {exc}")
    st.stop()

params = instance["parametros"]
scenarios = {
    "Personalizado": (params["w_A"], params["w_V"], params["w_N"]),
    "Asistencia": (1.0, 0.0, 0.0),
    "Valoracion": (0.0, 1.0, 0.0),
    "Numero de actividades": (0.1, 0.1, 0.8),
}

scenario = str(
    st.segmented_control("Escenario", list(scenarios), default="Personalizado")
    or "Personalizado"
)
defaults = scenarios[scenario]

with st.container(border=True):
    budget = st.number_input(
        "Presupuesto",
        min_value=0.0,
        value=float(params["presupuesto"]),
        step=100.0,
    )
    w_a = st.slider("Peso de asistencia", 0.0, 1.0, float(defaults[0]), 0.1)
    w_v = st.slider("Peso de valoracion", 0.0, 1.0, float(defaults[1]), 0.1)
    w_n = st.slider(
        "Peso de numero de actividades",
        0.0,
        1.0,
        float(defaults[2]),
        0.1,
    )

if st.button("Resolver modelo", type="primary", icon=":material/play_arrow:"):
    weights = (float(w_a), float(w_v), float(w_n))
    if sum(weights) == 0:
        st.error("Los tres pesos no pueden ser cero.")
    else:
        result = solve_instance(instance, float(budget), weights)
        if result["status"] == "SolverError":
            st.error(f"Error del solver: {result.get('error', 'error desconocido')}")
        elif result["status"] != "Optimal":
            st.warning(
                "Problema inviable: no existe una programacion valida "
                "con los parametros actuales."
            )
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Actividades", len(result["selected"]))
            c2.metric("Asistencia", f"{result['attendance']:,}".replace(",", "."))
            c3.metric("Valoracion", f"{result['rating']:.1f}")
            c4.metric("Coste", f"{result['cost']:,.0f}".replace(",", "."))
            c5.metric("Presupuesto", f"{budget:,.0f}".replace(",", "."))

            activities = instance["actividades"].copy()
            activities["estado"] = activities["id"].isin(result["selected"]).map(
                {True: "Seleccionada", False: "Descartada"}
            )

            st.subheader("Actividades seleccionadas")
            selected = activities[activities["estado"] == "Seleccionada"]
            st.dataframe(
                selected[
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
                ),
                hide_index=True,
            )

            st.subheader("Programacion por espacio y franja")
            if result["assignments"].empty:
                st.info("No hay actividades asignadas.")
            else:
                st.dataframe(
                    result["assignments"].rename(
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
                )

            st.subheader("Actividades descartadas")
            discarded = activities[activities["estado"] == "Descartada"]
            st.dataframe(
                discarded[["id", "nombre", "coste"]].rename(
                    columns={"id": "ID", "nombre": "Actividad", "coste": "Coste"}
                ),
                hide_index=True,
            )

            export = activities[
                [
                    "id",
                    "nombre",
                    "estado",
                    "duracion",
                    "asistencia",
                    "valoracion",
                    "coste",
                    "obligatoria",
                ]
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
