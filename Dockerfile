FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV PORT=8080

# 1. Install Python dan Curl
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Unduh ttyd
RUN curl -sLo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 && \
    chmod +x /usr/local/bin/ttyd

WORKDIR /app
COPY . /app

# 3. BYPASS: Install modul langsung tanpa mencari file requirements.txt
RUN pip3 install --no-cache-dir --break-system-packages requests python-dotenv

EXPOSE 8080

# 4. Jalankan Web Terminal
CMD ["sh", "-c", "ttyd -p $PORT -c admin:admin123 bash"]
