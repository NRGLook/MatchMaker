FROM python:3.12

WORKDIR /app

RUN pip install flake8==7.1.0 flake8-import-order==0.18.2 \
    flake8-polyfill==1.0.2 pep8-naming==0.14.1

COPY ./ /app/

CMD flake8 .