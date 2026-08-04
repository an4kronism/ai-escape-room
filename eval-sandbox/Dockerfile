FROM python:3.11-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl vim \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir h5py numpy requests pyjwt cryptography pymongo

COPY briefing.md /app/BRIEFING.md
COPY hints/hints.txt /opt/lab/hints.txt

RUN echo 'cat /app/BRIEFING.md' >> /etc/bash.bashrc \
    && echo 'alias hint="cat /opt/lab/hints.txt"' >> /etc/bash.bashrc

WORKDIR /app

CMD ["bash", "-c", "printf '\\n[+] Welcome to AI Escape Lab — eval sandbox\\n    Type hint to see hints\\n\\n' && exec tail -f /dev/null"]
