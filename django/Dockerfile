FROM python:3.12.6

WORKDIR /django

RUN apt-get update -y && apt-get upgrade -y && \
	apt-get install -y postgresql-client wget unzip

COPY requirements.txt .
RUN pip install -r requirements.txt
	
COPY . .

RUN chmod +x /django/launch.sh

EXPOSE 8000

CMD [ "/bin/bash", "/django/launch.sh" ]
