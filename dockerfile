FROM ubuntu:22.04

RUN apt-get update && apt-get upgrade -y
RUN apt-get install -y \
    curl \
    wget \
    python3 \
    python3-pip \
    nodejs \
    npm \
    vim \
    nano \
    htop \
    net-tools

EXPOSE 22 80 443 8080

CMD ["python3", "-m", "http.server", "8080"]
