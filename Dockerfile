FROM python:3.11-alpine

WORKDIR /app

RUN apk add --update --no-cache \
    gcc libc-dev libffi-dev

# Upload and install Python package and dependencies
COPY ./apricot apricot
COPY ./pyproject.toml .
COPY ./README.md .
RUN pip install --upgrade hatch pip
# Initialise environment with hatch
RUN hatch run true

# Install executable files and set permissions
COPY ./docker/entrypoint.sh .
COPY ./run.py .
RUN chmod ugo+x ./entrypoint.sh

# Open appropriate ports
EXPOSE 1389

# Run the server
ENTRYPOINT ["./entrypoint.sh"]
