FROM jupyter/datascience-notebook:b9f6ce795cfc

USER root

# System libraries
RUN apt-get update

# s3fs
RUN sudo apt install -y s3fs

# Add locales
RUN locale-gen fr_FR fr_FR.UTF-8 es_ES es_ES.UTF-8 de_DE de_DE.UTF-8
RUN update-locale

# For rgdal (R)
RUN apt-get install -y libgdal-dev
# For sf (R)
RUN apt-get install -y libudunits2-dev

# Install AWS CLI tools
RUN mkdir -p /usr/local/src/awcli
WORKDIR /usr/local/src/awcli
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN ./aws/install
WORKDIR $HOME
RUN rm -rf /usr/local/src/awcli

# Use mamba instead of conda
RUN conda install --quiet --yes mamba -c conda-forge

# R packages, in multiple steps for Docker layering (mamba - preferred method)
RUN mamba install --quiet --yes \
    'r-aws.s3=0.*' \
    'r-geojsonio=0.*' \
    'r-getpass=0.*' \
    'r-ggmap=3.*' \
    'r-ggthemes=4.*' \
    'r-hmisc=4.*' \
    'r-maptools=1.*' \
    'r-plotly=4.*' \
    'r-raster=3.*' \
    'r-readxl=1.*' \
    'r-rcolorbrewer=1.*' \
    'r-rgdal=1.*' \
    'r-rgeos=0.*' \
    'r-rgooglemaps=1.*' \
    'r-rjava=0.*' \
    'r-rjson=0.*' \
    'r-rpostgres=1.*' \
    'r-sf=0.*' \
    'r-tidyverse=1.*' \
    'r-viridis=0.*' \
    && mamba clean --yes --all

# Python packages, in multiple steps for Docker layering (mamba preferred method)
# TODO: unpin s3contents, fsspec, gcsfs & s3fs once https://github.com/danielfrg/s3contents/issues/122 is fixed
RUN mamba install --quiet --yes \
    'dask-ml=1.*' \
    'descartes=1.*' \
    'fsspec=0.9.0' \
    'gcsfs=0.8.0' \
    'geoalchemy2=0.*' \
    'geopandas=0.*' \
    'hybridcontents=0.*' \
    'ipywidgets=7.*' \
    'lxml=4.*' \
    'mapclassify=2.*' \
    'nbresuse=0.*' \
    'plotly=4.*' \
    'psycopg2=2.*' \
    'rapidfuzz=0.*' \
    'rasterstats=0.*' \
    's3contents=0.6.0' \
    's3fs=0.4.2' \
    'papermill==2.3.3' \
    && mamba clean --yes --all

RUN mamba install --quiet --yes \
    'jupyter-resource-usage=0.*' \
    && mamba clean --yes --all

# Jupyter extensions
RUN mamba install --quiet --yes \
    'jupyter-dash=0.*' \
    'jupyter-server-proxy=1.*' \
    && mamba clean --yes --all

# Python packages (pip - for what is not available in mamba)
RUN pip install \
    'cowsay==3.*' \
    'fake-useragent==0.*' \
    'hdx-python-api==4.*' \
    'tabpy==2.*'

# R packages (cran - for what is not available in mamba)
RUN R -e "install.packages(c('GISTools', 'OpenStreetMap'), dependencies=TRUE, quiet=TRUE, repos='https://cran.r-project.org/')"
RUN R -e "install.packages('isotree', dependencies=TRUE, quiet=TRUE, repos='https://cran.r-project.org/')"

# Jupyterlab extensions - check if still necessary
RUN jupyter labextension install jupyterlab-plotly@4.* --no-build && \
    jupyter labextension install plotlywidget@4.* --no-build && \
    jupyter lab build -y && \
    jupyter lab clean -y && \
    npm cache clean --force && \
    rm -rf "/home/${NB_USER}/.cache/yarn"

# custom config
COPY jupyter_notebook_config.py /etc/jupyter/

# custom local (Python) modules
COPY local_python_modules /opt/local_python_modules
ENV PYTHONPATH /opt/local_python_modules/

# sample files
# k8s: stored in /tmp within the pod, then copied back in the home directory after the PVC has been mounted through
# a postStart hook defined in config.yaml
# (see https://zero-to-jupyterhub.readthedocs.io/en/latest/customizing/user-environment.html#about-user-storage-and-adding-files-to-it)
COPY sample_files/* /tmp/notebooks_sample_files/
# the next line is for the local docker-compose environment only
COPY sample_files/* /home/jovyan/

# TODO: move higher
COPY fuse/fuse.conf /etc/.
COPY fuse/fuse.sh /home/jovyan/fuse.sh
COPY fuse/fuse_mount.py /home/jovyan/fuse_mount.py