FROM jupyterhub/jupyterhub:1.3

COPY jupyterhub_config.py .

RUN pip install --upgrade pip
RUN pip install dockerspawner==12.* psycopg2-binary==2.* requests==2.*