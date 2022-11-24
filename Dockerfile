FROM python:3.8
WORKDIR /Project/apitest
COPY . .
RUN pip install -r requirements.txt

