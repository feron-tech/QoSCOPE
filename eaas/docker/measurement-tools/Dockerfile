FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    g++ \
    cmake \
    libboost-program-options-dev \
    iperf3 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

RUN curl -s https://downloads.perfsonar.net/install | sh -s - tools && \
    apt-get update && apt-get install -y \
    perfsonar-tools \
    owamp-server \
    owamp-client \
    twamp-server \
    twamp-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /opt
RUN git clone https://github.com/EricssonResearch/udp-ping.git
WORKDIR /opt/udp-ping
RUN g++ -o udpServer udpServer.cpp -lboost_program_options && \
    g++ -o udpClient udpClient.cpp -lboost_program_options

COPY supervisord.conf /etc/supervisor/conf.d/qoscope.conf

EXPOSE 5201/tcp
EXPOSE 5201/udp
EXPOSE 1234/udp
EXPOSE 861/tcp
EXPOSE 862/tcp
EXPOSE 8760/tcp

CMD ["/usr/bin/supervisord", "-n"]
