FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Update dan install paket dasar beserta OpenSSH
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y \
    curl wget python3 python3-pip nodejs npm \
    vim nano htop net-tools openssh-server unzip

# Konfigurasi OpenSSH (Ubah 'rahasia123' dengan password Anda)
RUN mkdir -p /var/run/sshd && \
    echo 'root:riski223' | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config

# Install Ngrok untuk TCP Tunneling
RUN curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.zip -o ngrok.zip && \
    unzip ngrok.zip -d /usr/local/bin && \
    rm ngrok.zip

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
