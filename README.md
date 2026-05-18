# LLM RTL Simulation-Repair Study

## Quickstart

### 1) Clone the repo

```bash
git clone <this-repository-url> cvdp-ap
cd cvdp-ap
```

### 2) Install dependencies (Docker and Python needed)

On Ubuntu/WSL:

```bash
sudo apt-get update
sudo apt-get install -y git python3 python3-venv python3-pip
```

Start Docker and verify it works:

```bash
sudo systemctl enable --now docker
docker run --rm hello-world
```

If you get a permission error, add your user to the Docker group and re-login:

```bash
sudo usermod -aG docker $USER
```

### 3) Build the CVDP simulator Docker image and verify

```bash
cd ..
git clone https://github.com/NVlabs/cvdp_benchmark.git
cd cvdp_benchmark
docker build -f docker/Dockerfile.sim -t nvidia/cvdp-sim:v1.0.0 .
docker image ls nvidia/cvdp-sim
cd ../cvdp-ap
```

### 4) Set up `.env`

```bash
cp .env.example .env
```

Edit `.env` and set at least:

```bash
OPENROUTER_API_KEY=your_key_here
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct
CVDP_SIM_IMAGE=nvidia/cvdp-sim:v1.0.0
```

### 5) Run baseline

```bash
PYTHONPATH=src python3 scripts/run_experiment.py configs/final_baseline.yaml
```

### 6) Run repair

```bash
PYTHONPATH=src python3 scripts/run_experiment.py configs/final_sim_repair.yaml
```
