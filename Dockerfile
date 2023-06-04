FROM python:3.8-slim-buster

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

RUN mkdir -p /usr/share/fonts/truetype
RUN install -m644 ./*.ttf /usr/share/fonts/truetype/
RUN rm ./*.ttf

CMD [ "python3", "run.py"]