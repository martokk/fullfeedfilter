FROM python:3.10-slim-buster
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1 \
  LANG=C.UTF-8 \
  LC_ALL=C.UTF-8 \
  PATH="${PATH}:/root/.poetry/bin"

RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
  cd /usr/local/bin && \
  ln -s /opt/poetry/bin/poetry && \
  poetry config virtualenvs.create false

# Copy App Folder
COPY ./fullfeedfilter /fullfeedfilter
WORKDIR /fullfeedfilter

# Install App; Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi" && \
  poetry run python manage.py makemigrations && \
  poetry run python manage.py migrate --noinput && \
  poetry run python -m nltk.downloader punkt


# Start Entrypoint
ENV DJANGO_SUPERUSER_PASSWORD:-"admin" \
  DJANGO_SUPERUSER_EMAIL:-"example@example.com" \
  DJANGO_SUPERUSER_USERNAME:-"admin"
EXPOSE 8002
CMD ["sh", "start.sh"]