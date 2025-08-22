FROM python:3.12-alpine

# apparently streamlit can't run from root directory
WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY app_v2.py utils_v2.py dueling_quibblers_v3.py ./
COPY pics/ pics/

ARG ECS_PORT=80
ENV ECS_PORT=${ECS_PORT}
EXPOSE $ECS_PORT

# CMD streamlit run app_v2.py
ENTRYPOINT streamlit run app_v2.py --server.port=$ECS_PORT --server.address=0.0.0.0