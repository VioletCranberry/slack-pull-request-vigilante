FROM python:3.9-slim-bullseye as compiler
ENV PYTHONUNBUFFERED 1
WORKDIR /app/

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./requirements.txt /app/requirements.txt
RUN pip install -Ur requirements.txt


FROM python:3.9-slim-bullseye as runner
ENV PYTHONUNBUFFERED 1
WORKDIR /app/

COPY --from=compiler /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY ./clients/ /app/clients/
COPY ./parsers/ /app/parsers/
COPY ./processors/ /app/processors/
COPY ./utils.py /app/utils.py
COPY ./main.py /app/main.py

ENTRYPOINT ["python", "main.py"]
