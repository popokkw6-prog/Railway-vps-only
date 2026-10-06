FROM debian:bookworm-slim

# Mencegah interaksi manual saat instalasi paket
ENV DEBIAN_FRONTEND=noninteractive

# Update sistem dan install paket yang dibutuhkan untuk Bot Telegram & Terminal
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    curl wget python3 python3-pip python3-venv nodejs npm \
    vim nano htop net-tools git ttyd

# Install PM2 untuk menjalankan bot Telegram di background
RUN npm install -g pm2

# Konfigurasi port untuk Railway
ENV PORT=8080
EXPOSE 8080

# Jalankan Web Terminal (ttyd)
# Username: root | Password: riski223
CMD ["sh", "-c", "ttyd -p $PORT -c root:riski223 bash"]
