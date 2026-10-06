FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive
# Railway menggunakan variabel PORT otomatis, kita default ke 8080
ENV PORT=8080

# 1. Install Python dan Curl
RUN apt-get update && apt-get install -y \
    python3 python3-pip curl \
    && rm -rf /var/lib/apt/lists/*

# 2. Unduh ttyd secara manual (Solusi untuk error E: Package 'ttyd' has no installation candidate)
RUN curl -sLo /usr/local/bin/ttyd https://github.com/tsl0922/ttyd/releases/download/1.7.3/ttyd.x86_64 && \
    chmod +x /usr/local/bin/ttyd

WORKDIR /app

# 3. Pindahkan semua file source code dari GitHub ke dalam container
COPY . /app

# 4. Install requirements Python
RUN pip3 install --no-cache-dir --break-system-packages -r /app/me-cli-sunset-main/requirements.txt

EXPOSE 8080

# 5. Jalankan Web Terminal dengan otentikasi (username: admin, password: password_bebas)
CMD ["sh", "-c", "ttyd -p $PORT -c admin:admin123 bash"]
