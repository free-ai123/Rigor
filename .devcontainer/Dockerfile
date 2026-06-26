FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git bash less vim jq \
    && rm -rf /var/lib/apt/lists/*

RUN pip install pyyaml

WORKDIR /workspace

COPY scripts/ /workspace/scripts/
RUN chmod +x /workspace/scripts/*.sh

ENV PATH="/workspace/scripts:${PATH}"

CMD ["bash"]
