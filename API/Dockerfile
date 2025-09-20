FROM python

ARG API_DIRECTORY
ENV API_DIRECTORY=${API_DIRECTORY} 

RUN apt-get update && apt-get install -y netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR ${API_DIRECTORY}

COPY . .

RUN pip install --no-cache-dir -r requirements.txt && chmod +x ./entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["./entrypoint.sh"]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
