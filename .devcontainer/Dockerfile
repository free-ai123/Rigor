FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git bash less vim jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY pyproject.toml setup.py requirements.txt README.md /workspace/
COPY src/ /workspace/src/
RUN python -m pip install --upgrade pip \
    && pip install -e ".[dev]"

COPY scripts/ /workspace/scripts/
RUN chmod +x /workspace/scripts/*.sh

ENV PATH="/workspace/scripts:${PATH}"

CMD ["bash"]
