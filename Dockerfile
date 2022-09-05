FROM python:3.6.8
WORKDIR /Project/apitest
COPY . .
RUN pip install -r requirements.txt

