FROM python:3.10-slim-buster as build
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH="${PATH}:/root/.poetry/bin"

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Install Poetry
COPY pyproject.toml ./
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
  cd /usr/local/bin && \
  ln -s /opt/poetry/bin/poetry && \
  poetry config virtualenvs.create false

# Install App; Allow installing dev dependencies to run tests
WORKDIR /fullfeedfilter
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"
RUN poetry run python -m nltk.downloader punkt brown maxent_treebank_pos_tagger movie_reviews wordnet stopwords







FROM python:3.10-alpine  as main

COPY --from=build /fullfeedfilter /fullfeedfilter

# Start Entrypoint
ENV DJANGO_SUPERUSER_PASSWORD:-"admin" \
  DJANGO_SUPERUSER_EMAIL:-"example@example.com" \
  DJANGO_SUPERUSER_USERNAME:-"admin"
EXPOSE 8002
CMD ["/bin/sh", "-c", "./start.sh"]