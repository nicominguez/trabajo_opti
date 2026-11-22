from pathlib import Path
import sys

import pandas as pd
import streamlit as st


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "2_implementacion"))

from modelo import DataValidationError, load_instance, solve_instance


st.set_page_config(page_title="Planificacion optima del evento", layout="wide")
st.title("Planificacion optima del evento")

try:
    instance = load_instance()
except DataValidationError as exc:
    st.error(f"Error de datos: {exc}")
    st.stop()

params = instance["parametros"]

max_budget = max(10000, int(params["presupuesto"] * 2))
budget = st.slider(
    "Presupuesto",
    min_value=0,
    max_value=max_budget,
    value=int(params["presupuesto"]),
    step=100,
)
w_a = st.slider("Peso de asistencia", 0.0, 1.0, float(params["w_A"]), 0.1)
w_v = st.slider("Peso de valoracion", 0.0, 1.0, float(params["w_V"]), 0.1)
w_n = 1.0 - w_a - w_v
if w_n >= 0:
    st.caption(f"Pesos efectivos: ({w_a:.1f}, {w_v:.1f}, {w_n:.1f}); suma = 1.0")

if st.button("Resolver", type="primary"):
    if w_a + w_v > 1:
        st.error("La suma de asistencia y valoracion no puede superar 1.")
    else:
        result = solve_instance(instance, float(budget), (w_a, w_v, w_n))

        if result["status"] == "SolverError":
            st.error(f"Error del solver: {result.get('error', 'error desconocido')}")
        elif result["status"] != "Optimal":
            st.warning("Problema inviable: no existe una programacion valida.")
        else:
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Actividades", len(result["selected"]))
            c2.metric("Asistencia", result["attendance"])
            c3.metric("Valoracion", f"{result['rating']:.1f}")
            c4.metric("Coste", f"{result['cost']:,.0f}".replace(",", "."))
            c5.metric("Presupuesto", f"{budget:,.0f}".replace(",", "."))

            horizon = int(params["num_franjas"])
            slots_per_day = int(params["franjas_por_dia"])
            space_names = instance["espacios"].set_index("id")["nombre"].to_dict()
            columns = [
                f"D{((slot - 1) // slots_per_day) + 1}"
                f"F{((slot - 1) % slots_per_day) + 1}"
                for slot in range(1, horizon + 1)
            ]
            calendar = pd.DataFrame(
                [[[] for _ in columns] for _ in space_names],
                index=list(space_names.values()),
                columns=columns,
            )

            activity_details = instance["actividades"].set_index("id")
            activity_palette = [
                "#2563EB", "#DC2626", "#059669", "#7C3AED",
                "#EA580C", "#0891B2", "#DB2777", "#65A30D",
                "#9333EA", "#CA8A04", "#0D9488", "#4F46E5",
                "#E11D48", "#0369A1", "#16A34A", "#C026D3",
                "#B45309", "#6D28D9",
            ]
            activity_colors = {
                int(activity_id): activity_palette[index % len(activity_palette)]
                for index, activity_id in enumerate(instance["actividades"]["id"])
            }
            activity_ids_by_name = {
                str(row.nombre): int(row.id)
                for row in instance["actividades"].itertuples()
            }
            selected_rows = []
            for _, assignment in result["assignments"].iterrows():
                activity_id = int(assignment["actividad"])
                details = activity_details.loc[activity_id]
                selected_rows.append({
                    "ID": activity_id,
                    "Actividad": [str(assignment["nombre"])],
                    "Categoria": details["categoria"],
                    "Duracion": int(details["duracion"]),
                    "Asistencia": int(details["asistencia"]),
                    "Valoracion": float(details["valoracion"]),
                    "Coste": int(details["coste"]),
                    "Espacio": assignment["nombre_espacio"],
                    "Franja inicio": int(assignment["inicio"]),
                    "Franja fin": int(assignment["fin"]),
                })
                for slot in range(int(assignment["inicio"]), int(assignment["fin"]) + 1):
                    day = (slot - 1) // slots_per_day + 1
                    slot_in_day = (slot - 1) % slots_per_day + 1
                    column = f"D{day}F{slot_in_day}"
                    current = calendar.loc[assignment["nombre_espacio"], column]
                    if assignment["nombre"] not in current:
                        current.append(str(assignment["nombre"]))

            st.subheader("Calendario")
            calendar_config = {}
            calendar_options = list(dict.fromkeys(
                name
                for row in calendar.to_numpy().flatten()
                for name in row
            ))
            for column in calendar.columns:
                calendar_config[column] = st.column_config.MultiselectColumn(
                    column,
                    options=calendar_options,
                    color=[
                        activity_colors[activity_ids_by_name[name]]
                        for name in calendar_options
                    ],
                    width="small",
                )
            st.dataframe(
                calendar,
                hide_index=False,
                use_container_width=True,
                column_config=calendar_config,
            )

            table = pd.DataFrame(selected_rows)
            st.subheader("Actividades seleccionadas")
            table_options = list(dict.fromkeys(
                name
                for names in table["Actividad"]
                for name in names
            ))
            st.dataframe(
                table,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Actividad": st.column_config.MultiselectColumn(
                        "Actividad",
                        options=table_options,
                        color=[
                            activity_colors[activity_ids_by_name[name]]
                            for name in table_options
                        ],
                        width="medium",
                    ),
                },
            )
            st.download_button(
                "Descargar tabla CSV",
                table.to_csv(index=False).encode("utf-8"),
                file_name="actividades_seleccionadas.csv",
                mime="text/csv",
            )

            discarded = instance["actividades"][
                ~instance["actividades"]["id"].isin(result["selected"])
            ][
                ["id", "nombre", "categoria", "duracion", "asistencia",
                 "valoracion", "coste"]
            ].rename(columns={
                "id": "ID",
                "nombre": "Actividad",
                "categoria": "Categoria",
                "duracion": "Duracion",
                "asistencia": "Asistencia",
                "valoracion": "Valoracion",
                "coste": "Coste",
            })
            with st.expander("Actividades descartadas"):
                st.dataframe(
                    discarded,
                    hide_index=True,
                    use_container_width=True,
                )
