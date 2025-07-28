FROM python:3.12-alpine

# apparently streamlit can't run from root directory
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY utils.py app.py app.py dueling_quibblers_v3.py ./

EXPOSE 8501

# CMD streamlit run app.py
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
