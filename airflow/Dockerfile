FROM apache/airflow:2.5.2

ENV AIRFLOW_HOME=/usr/local/airflow

USER root

RUN apt-get update \
    && apt-get install -y python3-pip \
    libcurl4-gnutls-dev \
    librtmp-dev \
    python3-dev \
    libpq-dev

RUN python3 -m pip install psycopg2-binary argcomplete pycurl

COPY ./config/* /

COPY ./dags/* ${AIRFLOW_HOME}/dags/

RUN chown -R airflow: ${AIRFLOW_HOME}

EXPOSE 8080

USER airflow

WORKDIR ${AIRFLOW_HOME}

# ENTRYPOINT ["/entrypoint.sh"]
