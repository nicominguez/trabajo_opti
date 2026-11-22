# Modelo de optimización para la planificación de eventos

**Trabajo de la asignatura Optimización I · Universidad Pública de Navarra (UPNA) · Curso 2026/27**

## Ejecución de la aplicación

Desde la raíz del repositorio, cree el entorno virtual, instale las
dependencias y ejecute Streamlit:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

Abra la dirección indicada por Streamlit, normalmente
`http://localhost:8501`. La aplicación carga y valida los archivos CSV
de `data/`.

## Compilación del informe en LaTeX

Instale una distribución de LaTeX que incluya `pdflatex` y, desde la raíz
del repositorio, ejecute:

```bash
cd informe
mkdir .build
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=.build informe.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory=.build informe.tex
mv .build/informe.pdf . && rm -r .build
cd ..
```

El informe se genera en `informe/informe.pdf`.