FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Update dan install paket dasar beserta OpenSSH
# (unzip dihapus karena kita akan menggunakan tar bawaan Ubuntu)
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    curl wget python3 python3-pip nodejs npm \
    vim nano htop net-tools openssh-server

# Konfigurasi OpenSSH 
RUN mkdir -p /var/run/sshd && \
    echo 'root:riski223' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Install Ngrok versi terbaru (v3) untuk Linux (menggunakan .tgz)
RUN curl -sSL https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz -o ngrok.tgz && \
    tar -xvzf ngrok.tgz -C /usr/local/bin && \
    rm ngrok.tgz

# Install PM2 untuk menjalankan multiple services di background
RUN npm install -g pm2

ENV PORT=8080
EXPOSE 8080

# Buat bash script untuk menjalankan SSH, PM2, dan Ngrok sekaligus
RUN echo "#!/bin/bash" > /start.sh && \
    echo "/usr/sbin/sshd" >> /start.sh && \
    echo "pm2 start \"python3 -m http.server \$PORT\" --name web_server" >> /start.sh && \
    echo "ngrok config add-authtoken \$NGROK_TOKEN" >> /start.sh && \
    echo "ngrok tcp 22" >> /start.sh && \
    chmod +x /start.sh

CMD ["/start.sh"]
