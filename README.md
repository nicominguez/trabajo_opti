# Planificacion optima de un evento

Proyecto minimo de programacion lineal entera para seleccionar y programar actividades.

## Sitio de la aplicacion

Desde la raíz del repositorio, crear el entorno virtual, instalar las
dependencias y ejecutar Streamlit:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Abrir la dirección indicada por Streamlit, normalmente
`http://localhost:8501`. La aplicación utiliza los CSV de `data/`.

## Crear el PDF del informe

Instalar primero una distribución LaTeX compatible con `pdflatex`, como
MacTeX/TeX Live en macOS o TeX Live/MiKTeX en Linux y Windows. Después,
compilar dos veces desde la raíz del repositorio:

```bash
cd informe
pdflatex -interaction=nonstopmode -halt-on-error informe.tex
pdflatex -interaction=nonstopmode -halt-on-error informe.tex
```

El segundo pase resuelve referencias cruzadas e índices. El PDF generado
se guarda como `informe/informe.pdf`.
