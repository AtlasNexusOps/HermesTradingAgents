#!/bin/bash
# ── HermesTradingAgents — Setup Script (Ubuntu 24.04) ─────────────
# Usage: bash setup.sh
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🧠 HermesTradingAgents — Setup${NC}\n"

# ── 1. Check Docker ───────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    echo -e "${YELLOW}Docker non trouvé. Installation...${NC}"
    sudo apt-get update
    sudo apt-get install -y ca-certificates curl
    sudo install -m 0755 -d /etc/apt/keyrings
    sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
    sudo chmod a+r /etc/apt/keyrings/docker.asc
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker $USER
    echo -e "${YELLOW}⚠️  Re-login required for Docker group. Run: newgrp docker${NC}"
fi

# ── 2. Clone repo ─────────────────────────────────────────────────
REPO_DIR="$HOME/HermesTradingAgents"
if [ ! -d "$REPO_DIR" ]; then
    echo -e "${GREEN}📦 Cloning repo...${NC}"
    git clone https://github.com/AtlasNexusOps/HermesTradingAgents.git "$REPO_DIR"
else
    echo -e "${GREEN}📦 Repo déjà présent, pull...${NC}"
    cd "$REPO_DIR" && git pull origin main
fi

cd "$REPO_DIR"

# ── 3. Configure .env ─────────────────────────────────────────────
if [ ! -f ".env" ]; then
    cp .env.hermes .env
    echo -e "${YELLOW}⚠️  Édite .env pour ajouter ta DEEPSEEK_API_KEY${NC}"
    echo -e "${YELLOW}   nano $REPO_DIR/.env${NC}"
else
    echo -e "${GREEN}✅ .env déjà présent${NC}"
fi

# ── 4. Pull Ollama models (optional) ──────────────────────────────
echo ""
read -p "Pull Ollama models for local mode? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker pull ollama/ollama:latest
    echo -e "${GREEN}Ollama image pulled. Run 'docker compose -f docker-compose.hermes.yml --profile ollama up -d' then 'docker exec -it hermes-trading-ollama ollama pull qwen3'${NC}"
fi

# ── 5. Build & Run ────────────────────────────────────────────────
echo ""
echo -e "${GREEN}🐳 Building Docker image...${NC}"
docker compose -f docker-compose.hermes.yml build

echo ""
echo -e "${GREEN}🚀 Starting container...${NC}"
docker compose -f docker-compose.hermes.yml up -d

echo ""
echo -e "${GREEN}✅ Setup terminé !${NC}"
echo ""
echo "  Container : docker ps"
echo "  Shell     : docker exec -it hermes-trading-agents bash"
echo "  Analyse   : docker exec -it hermes-trading-agents python main.py"
echo "  MCP mode  : docker run -i --env-file .env hermes-trading-agents python mcp/hermes_trading_tool.py"
