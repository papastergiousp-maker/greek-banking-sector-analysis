FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Rebuild the SQLite DB from processed CSVs so the container is self-contained
RUN python 02_Banking_Sector_Dashboard/rebuild_db.py

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "05_streamlit_app/app.py", \
            "--server.port=8501", "--server.address=0.0.0.0", \
            "--server.headless=true"]
