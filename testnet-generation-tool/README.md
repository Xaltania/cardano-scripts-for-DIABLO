# Testnet Genesis Generation Tool

## Index

- [About](#about)
- [Features](#features)
- [Requirements](#requirements)
- [Install](#install)

## About

A cli utility to generate, deploy and manage custom testnet environments.  
Compatible with cardano-node version 10.2.1 on Linux.


## Features

- [x] Custom Genesis Configs
- [x] Custom Key Matarial
- [x] Configure Multiple Pools
- [ ] Relays Nodes
- [x] P2P Topology
- [x] Prometheus 
- [x] Grafana 
- [ ] faucet
- [ ] db-sync
- [ ] cardano-wallet
- [ ] ogmios


## Requirements
python3     
[podman](https://docs.podman.io/)    
[uv](https://github.com/astral-sh/uv) 
    
`sudo apt-get -y install podman`                   
`curl -LsSf https://astral.sh/uv/install.sh | sh`     

## Install

```bash
git clone git@github.com:cardano-foundation/testnet-generation-tool.git ; cd testnet-generation-tool
uv sync
source .venv/bin/activate
```

## Generate a testnet environment

```bash
uv sync
source .venv/bin/activate
python3 genesis-cli.py example-config-testnet.yaml -o <your_testnet_dir> -c generate
```

## Deploy a testnet

Deploy a multinode node testnet:
```bash
cd <your_testnet_dir>
./deploy.sh
```
Deploy a single node testnet using batch credetials: 
```bash
cd <your_testnet_dir>
./deploy-batch.sh
```

## Destroy a testnet

```bash
cd <your_testnet_dir>
./destroy.sh
```

## Analyse, truncate & synthesize blocks
```bash
Documentation comming soon ...
```

