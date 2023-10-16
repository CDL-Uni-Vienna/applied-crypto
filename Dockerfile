FROM python:slim

RUN apt update && apt install --yes git build-essential subversion flex bison wget subversion m4 python3 python3-dev python3-setuptools libgmp-dev libssl-dev

# install the notebook package
RUN pip install --no-cache --upgrade pip

# create user with a home directory
ARG NB_USER
ARG NB_UID
ENV USER ${NB_USER}
ENV HOME /home/${NB_USER}

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}
WORKDIR ${HOME}

COPY requirements.txt .
RUN pip install -r requirements.txt

USER ${USER}



RUN mkdir ${HOME}/notebooks && chown ${NB_USER} ${HOME}/notebooks

USER ${USER}
WORKDIR ${HOME}
WORKDIR notebooks
COPY --chown=${USER} notebooks .
