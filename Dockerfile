FROM python:3.11-alpine

WORKDIR /app

RUN apk add --update --no-cache \
    gcc libc-dev libffi-dev

# Install Python dependencies
COPY ./pyproject.toml .
RUN pip install --upgrade hatch pip
# Copy code and README into the container
COPY ./README.md .
COPY ./apricot apricot
# Initialise environment with hatch
RUN hatch run true

# Install executable files and set permissions
COPY ./docker/entrypoint.sh .
COPY ./run.py .
RUN chmod ugo+x ./entrypoint.sh

# Open appropriate ports
EXPOSE 1389, 1636

# Run the server
ENTRYPOINT ["./entrypoint.sh"]
