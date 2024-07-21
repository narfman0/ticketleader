FROM python:3.12-slim
WORKDIR /app
RUN pip install poetry
COPY . .
EXPOSE 8000
COPY ./start.sh /start.sh
RUN chmod +x /start.sh
CMD ["/start.sh"]