FROM ubuntu:22.04

RUN apt-get update
RUN apt-get install -y python3-pip
RUN apt-get install -y curl

RUN curl -LO https://freeshell.de/phd/chromium/jammy/pool/chromium_130.0.6723.58~linuxmint1+virginia/chromium_130.0.6723.58~linuxmint1+virginia_amd64.deb
RUN apt-get install -y ./chromium_130.0.6723.58~linuxmint1+virginia_amd64.deb
RUN apt-get install -y libasound2

RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

RUN apt-get install -y pkg-config libssl-dev
RUN apt-get install -y jq

WORKDIR /workdir
ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install -r requirements.txt

# Build just the dependencies (shorcut)
RUN mkdir client
COPY client/Cargo.lock client/Cargo.toml client/
WORKDIR client
RUN mkdir src && echo "fn main() {}" > src/main.rs
RUN cargo build --release
RUN rm -r src
WORKDIR /workdir

# Copy the real files
COPY client/ ./client/
COPY nousflash/agent/ ./agent/
COPY run.sh ./
COPY timerelease.sh ./

WORKDIR client/
RUN cargo build --release
WORKDIR /workdir

COPY scripts/ ./scripts/

RUN mkdir -p /data

ENTRYPOINT [ ]
CMD [ "bash", "run.sh" ]
