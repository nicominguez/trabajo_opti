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
            activity_palette = [
                "#2563EB", "#DC2626", "#059669", "#7C3AED",
                "#EA580C", "#0891B2", "#DB2777", "#65A30D",
                "#9333EA", "#CA8A04", "#0D9488", "#4F46E5",
                "#E11D48", "#0369A1", "#16A34A", "#C026D3",
                "#B45309", "#6D28D9",
            ]
            selected_activity_names = list(dict.fromkeys(
                assignment["nombre"]
                for _, assignment in result["assignments"].iterrows()
            ))
            activity_colors = {
                name: activity_palette[index % len(activity_palette)]
                for index, name in enumerate(selected_activity_names)
            }
            horizon = int(params["num_franjas"])
            slots_per_day = int(params["franjas_por_dia"])
            space_names = instance["espacios"].set_index("id")["nombre"].to_dict()
            calendar = pd.DataFrame(
                [[[] for _ in range(horizon)]
                 for _ in space_names],
                index=pd.Index(list(space_names.values())),
                columns=pd.Index([
                    f"D{((slot - 1) // slots_per_day) + 1}"
                    f"F{((slot - 1) % slots_per_day) + 1}"
                    for slot in range(1, horizon + 1)
                ]),
            )
            for _, assignment in result["assignments"].iterrows():
                for slot in range(int(assignment["inicio"]), int(assignment["fin"]) + 1):
                    day = (slot - 1) // slots_per_day + 1
                    slot_in_day = (slot - 1) % slots_per_day + 1
                    calendar.loc[
                        assignment["nombre_espacio"],
                        f"D{day}F{slot_in_day}",
                    ].append(assignment["nombre"])

            calendar_options = list(dict.fromkeys(
                entry
                for row in calendar.to_numpy().flatten()
                for entry in row
            ))
            calendar_colors = [
                activity_colors[name]
                for name in calendar_options
            ]
            calendar_config = {
                column: st.column_config.MultiselectColumn(
                    column,
                    options=calendar_options,
                    color=calendar_colors,
                    width="small",
                    disabled=True,
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
                    "Actividad": [str(assignment["nombre"])],
                    "Categoria": str(details["categoria"]),
                    "Duracion": int(details["duracion"]),
                    "Asistencia": int(details["asistencia"]),
                    "Valoracion": float(details["valoracion"]),
                    "Coste": float(details["coste"]),
                    "Espacio ID": assignment["espacio"],
                    "Espacio": assignment["nombre_espacio"],
                    "Franja inicio": int(assignment["inicio"]),
                    "Franja fin": int(assignment["fin"]),
                })
            selected_table_names = [
                str(name)
                for name in selected_activity_names
            ]
            st.dataframe(
                pd.DataFrame(selected_rows),
                hide_index=True,
                column_config={
                    "Actividad": st.column_config.MultiselectColumn(
                        "Actividad",
                        options=selected_table_names,
                        color=[
                            activity_colors[name]
                            for name in selected_table_names
                        ],
                        width="medium",
                        disabled=True,
                    ),
                },
            )