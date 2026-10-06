FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install paket dasar tanpa ttyd
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    curl wget python3 python3-pip python3-venv nodejs npm \
    vim nano htop net-tools git

# Unduh dan pasang ttyd secara manual dari rilis resminya
RUN curl -sLo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 && \
    chmod +x /usr/local/bin/ttyd

RUN npm install -g pm2

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "ttyd -p $PORT -c root:riski223 bash"]
