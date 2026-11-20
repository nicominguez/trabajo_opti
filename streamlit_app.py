from pathlib import Path
import sys

import pandas as pd
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

with st.container(border=True):
    budget = st.number_input(
        "Presupuesto",
        min_value=0.0,
        value=float(params["presupuesto"]),
        step=100.0,
    )
    w_a = st.slider(
        "Peso de asistencia",
        0.0,
        1.0,
        float(params["w_A"]),
        0.1,
    )
    w_v = st.slider(
        "Peso de valoracion",
        0.0,
        1.0,
        float(params["w_V"]),
        0.1,
    )
    w_n = st.slider(
        "Peso de numero de actividades",
        0.0,
        1.0,
        float(params["w_N"]),
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

            st.subheader("Calendario")
            horizon = int(params["num_franjas"])
            slots_per_day = int(params["franjas_por_dia"])
            calendar = pd.DataFrame(
                [[[] for _ in range(slots_per_day)]
                 for _ in range(horizon // slots_per_day)],
                index=pd.Index(
                    [f"Dia {day}" for day in range(1, horizon // slots_per_day + 1)]
                ),
                columns=pd.Index([
                    f"Franja {slot}"
                    for slot in range(1, slots_per_day + 1)
                ]),
            )
            for _, assignment in result["assignments"].iterrows():
                day = (int(assignment["inicio"]) - 1) // slots_per_day + 1
                for slot in range(
                    int(assignment["inicio"]),
                    int(assignment["fin"]) + 1,
                ):
                    slot_in_day = slot - (day - 1) * slots_per_day
                    entry = (
                        f"{assignment['nombre']} "
                        f"[{assignment['espacio']}]"
                    )
                    calendar.loc[
                        f"Dia {day}", f"Franja {slot_in_day}"
                    ].append(entry)

            calendar_options = [
                f"{assignment['nombre']} [{assignment['espacio']}]"
                for _, assignment in result["assignments"].iterrows()
            ]
            calendar_config = {
                column: st.column_config.MultiselectColumn(
                    column,
                    options=calendar_options,
                    color="primary",
                )
                for column in calendar.columns
            }
            st.dataframe(
                calendar,
                column_config=calendar_config,
            )

            st.subheader("Actividades seleccionadas")
            activity_details = instance["actividades"].set_index("id")
            selected_rows = []
            for _, assignment in result["assignments"].iterrows():
                activity_id = int(assignment["actividad"])
                details = activity_details.loc[activity_id]
                selected_rows.append({
                    "ID": activity_id,
                    "Actividad": assignment["nombre"],
                    "Categoria": [str(details["categoria"])],
                    "Duracion": int(details["duracion"]),
                    "Asistencia": int(details["asistencia"]),
                    "Valoracion": float(details["valoracion"]),
                    "Coste": float(details["coste"]),
                    "Espacio ID": assignment["espacio"],
                    "Espacio": assignment["nombre_espacio"],
                    "Franja inicio": int(assignment["inicio"]),
                    "Franja fin": int(assignment["fin"]),
                })
            st.dataframe(
                pd.DataFrame(selected_rows),
                hide_index=True,
                column_config={
                    "Categoria": st.column_config.MultiselectColumn(
                        "Categoria",
                        options=["ML", "Estadistica", "Ingenieria"],
                        color="primary",
                    )
                },
            )
