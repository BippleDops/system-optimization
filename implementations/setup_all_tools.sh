#!/bin/bash
# Complete Power Tools Setup Script for macOS

echo "🚀 Power Tools Installation Script"
echo "=================================="
echo ""

# Create necessary directories
mkdir -p ~/PowerTools/{configs,data,scripts}
mkdir -p ~/system-optimization/implementations/{scrapers,obsidian,ai,automation}

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install GUI Applications
echo "🖥️ Installing GUI Applications..."
brew install --cask lm-studio        # Local LLM GUI
brew install --cask warp             # AI-powered terminal
brew install --cask obsidian         # Note-taking
brew install --cask zed              # Fast editor

# Install CLI Tools
echo "⚡ Installing CLI Tools..."
brew install wget curl jq git python3 node docker docker-compose
brew install ffmpeg imagemagick pandoc
brew install ripgrep fzf bat exa    # Better unix tools

# Python Environment Setup
echo "🐍 Setting up Python environment..."
python3 -m venv ~/PowerTools/venv
source ~/PowerTools/venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install firecrawl-py            # Web scraping
pip install playwright               # Browser automation
pip install playwright-stealth       # Stealth browsing
pip install whisper                  # Audio transcription
pip install pandas numpy             # Data processing
pip install fastapi uvicorn         # API development
pip install langchain openai        # AI integration
pip install obsidiantools           # Obsidian integration

# Install Playwright browsers
playwright install chromium

# Node.js Global Packages
echo "📦 Installing Node packages..."
npm install -g n8n                  # Workflow automation
npm install -g @turborepo/turbo     # Monorepo management
npm install -g nx                   # Build system
npm install -g localtunnel          # Expose local servers

# Docker Services Setup
echo "🐳 Setting up Docker services..."

# Create docker-compose for all services
cat > ~/PowerTools/docker-compose.yml << 'EOF'
version: '3.8'

services:
  # LocalAI - Run LLMs locally
  localai:
    image: localai/localai:latest
    container_name: localai
    ports:
      - "8080:8080"
    volumes:
      - ./models:/models
      - ./data:/data
    environment:
      - MODELS_PATH=/models
      - THREADS=8
    restart: unless-stopped

  # n8n - Workflow automation
  n8n:
    image: n8nio/n8n
    container_name: n8n
    ports:
      - "5678:5678"
    volumes:
      - ./n8n:/home/node/.n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=changeme
    restart: unless-stopped

  # ChangeDetection - Website monitoring
  changedetection:
    image: dgtlmoon/changedetection.io
    container_name: changedetection
    ports:
      - "5000:5000"
    volumes:
      - ./changedetection:/datastore
    environment:
      - PUID=1000
      - PGID=1000
    restart: unless-stopped

  # OpenObserve - Monitoring
  openobserve:
    image: public.ecr.aws/zinclabs/openobserve:latest
    container_name: openobserve
    ports:
      - "5080:5080"
    volumes:
      - ./openobserve:/data
    environment:
      - ZO_ROOT_USER_EMAIL=admin@example.com
      - ZO_ROOT_USER_PASSWORD=changeme
    restart: unless-stopped

  # Windmill - Developer automation
  windmill:
    image: ghcr.io/windmill-labs/windmill:main
    container_name: windmill
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgres://postgres:changeme@windmill_db:5432/windmill
    depends_on:
      - windmill_db
    restart: unless-stopped

  windmill_db:
    image: postgres:14-alpine
    container_name: windmill_db
    volumes:
      - ./windmill_db:/var/lib/postgresql/data
    environment:
      - POSTGRES_PASSWORD=changeme
      - POSTGRES_DB=windmill
    restart: unless-stopped

networks:
  default:
    name: powertools
    driver: bridge

volumes:
  models:
  data:
  n8n:
  changedetection:
  openobserve:
  windmill_db:
EOF

# Create Obsidian plugins directory
echo "📝 Setting up Obsidian integrations..."
OBSIDIAN_VAULT=~/Documents/Obsidian
mkdir -p "$OBSIDIAN_VAULT/.obsidian/plugins"

# Download essential Obsidian plugins
cd "$OBSIDIAN_VAULT/.obsidian/plugins"
git clone https://github.com/denolehov/obsidian-git.git
git clone https://github.com/blacksmithgu/obsidian-dataview.git
git clone https://github.com/phibr0/obsidian-charts.git

# Create example scraper
echo "🕷️ Creating example web scraper..."
cat > ~/PowerTools/scripts/smart_scraper.py << 'EOF'
#!/usr/bin/env python3
"""
Smart Web Scraper with AI Enhancement
"""
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
import json
from datetime import datetime

def scrape_with_ai(url, selector=None):
    """Scrape website with stealth mode and AI extraction"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Apply stealth mode
        stealth_sync(page)
        
        # Navigate to URL
        page.goto(url, wait_until='networkidle')
        
        # Extract content
        if selector:
            content = page.query_selector(selector).inner_text()
        else:
            content = page.content()
        
        # Save screenshot
        page.screenshot(path=f'screenshot_{datetime.now():%Y%m%d_%H%M%S}.png')
        
        browser.close()
        
        return content

if __name__ == "__main__":
    # Example usage
    result = scrape_with_ai("https://example.com")
    print(json.dumps({"content": result[:500]}, indent=2))
EOF

chmod +x ~/PowerTools/scripts/smart_scraper.py

# Create n8n workflow example
echo "⚙️ Creating n8n workflow template..."
cat > ~/PowerTools/configs/n8n_workflow_example.json << 'EOF'
{
  "name": "Daily Automation",
  "nodes": [
    {
      "name": "Schedule",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300],
      "parameters": {
        "rule": {
          "interval": [{"field": "hours", "hoursInterval": 24}]
        }
      }
    },
    {
      "name": "Scrape Data",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "url": "https://api.example.com/data",
        "method": "GET"
      }
    },
    {
      "name": "Process with AI",
      "type": "n8n-nodes-base.code",
      "position": [650, 300],
      "parameters": {
        "code": "// Process data with LocalAI\nreturn items;"
      }
    },
    {
      "name": "Save to Obsidian",
      "type": "n8n-nodes-base.writeFile",
      "position": [850, 300],
      "parameters": {
        "fileName": "/path/to/obsidian/vault/{{$now}}.md"
      }
    }
  ]
}
EOF

# Create startup script
echo "🚀 Creating startup script..."
cat > ~/PowerTools/start_services.sh << 'EOF'
#!/bin/bash
echo "Starting Power Tools Services..."

# Start Docker services
cd ~/PowerTools
docker-compose up -d

# Wait for services to be ready
sleep 10

# Open service URLs
echo ""
echo "📊 Services Available:"
echo "  • LocalAI: http://localhost:8080"
echo "  • n8n: http://localhost:5678"
echo "  • ChangeDetection: http://localhost:5000"
echo "  • OpenObserve: http://localhost:5080"
echo "  • Windmill: http://localhost:8000"
echo ""
echo "Default credentials: admin / changeme"
EOF

chmod +x ~/PowerTools/start_services.sh

# Create Obsidian AI integration script
echo "🤖 Creating Obsidian AI assistant..."
cat > ~/PowerTools/scripts/obsidian_ai.py << 'EOF'
#!/usr/bin/env python3
"""
Obsidian AI Assistant - Integrates local LLMs with your vault
"""
import os
import json
from datetime import datetime
from pathlib import Path
import requests

class ObsidianAI:
    def __init__(self, vault_path, localai_url="http://localhost:8080"):
        self.vault = Path(vault_path)
        self.ai_url = localai_url
        
    def create_smart_note(self, prompt):
        """Generate a note using AI"""
        response = requests.post(
            f"{self.ai_url}/v1/completions",
            json={"prompt": prompt, "max_tokens": 500}
        )
        
        content = response.json()["choices"][0]["text"]
        
        # Save to Obsidian
        filename = f"{datetime.now():%Y%m%d_%H%M%S}_ai_note.md"
        filepath = self.vault / filename
        
        with open(filepath, "w") as f:
            f.write(f"# AI Generated Note\n\n")
            f.write(f"*Generated: {datetime.now()}*\n\n")
            f.write(content)
        
        return filepath

if __name__ == "__main__":
    ai = ObsidianAI("~/Documents/Obsidian")
    ai.create_smart_note("Write about productivity tips for developers")
EOF

# Final setup message
echo ""
echo "✅ Power Tools Installation Complete!"
echo "===================================="
echo ""
echo "🎯 Quick Start Commands:"
echo "  1. Start services: ~/PowerTools/start_services.sh"
echo "  2. Activate Python: source ~/PowerTools/venv/bin/activate"
echo "  3. Run scraper: python ~/PowerTools/scripts/smart_scraper.py"
echo "  4. Open n8n: http://localhost:5678"
echo "  5. Open Obsidian and enable plugins"
echo ""
echo "📚 Documentation:"
echo "  • LocalAI: https://localai.io/basics/getting_started/"
echo "  • n8n: https://docs.n8n.io/"
echo "  • Playwright: https://playwright.dev/python/"
echo ""
echo "🔥 Your development environment is now SUPERCHARGED!"
