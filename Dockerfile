FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

ENTRYPOINT ["bash", "-c", "\
if [ \"$APP_MODE\" = 'multi-process' ]; then \
    gunicorn -w ${APP_WORKERS:-4} -k aiohttp.GunicornWebWorker -b 0.0.0.0:8080 server:application; \
else \
    python server.py; \
fi"]