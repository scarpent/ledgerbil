FROM python:3.9

RUN apt-get update && apt-get install -y ledger

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY . /code/

# set up to use sample data
RUN rm -f /code/ledgerbil/settings.py
COPY ledgerbil/settings.py.example /code/ledgerbil/settings.py
RUN mkdir /root/some
RUN ln -s /code/sample/ /root/some/place

RUN echo 'alias ll="ls -l"' >> ~/.bashrc
RUN echo 'alias ledgerbil="python /code/main.py"' >> ~/.bashrc
RUN echo 'alias lbil=ledgerbil' >> ~/.bashrc
