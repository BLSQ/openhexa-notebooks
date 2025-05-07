# The version here MUST match the z2jh chart version
# URL: https://hub.jupyter.org/helm-chart/
FROM jupyterhub/k8s-hub:4.1.0

COPY config/jupyterhub_config_base.py /usr/local/etc/jupyterhub/jupyterhub_config.d/jupyterhub_base_config.py
COPY config/jupyterhub_config_k8s.py /usr/local/etc/jupyterhub/jupyterhub_config.d/jupyterhub_config.py
