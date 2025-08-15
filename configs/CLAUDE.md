# CLAUDE.md - Persistent Memory for Claude Code

## User Preferences & Coding Standards

### Personal Information
- **Primary Development Directory**: `~/Development/`
- **Preferred Language**: Python 3.12
- **Shell**: zsh
- **Platform**: macOS (Darwin 24.6.0, ARM64)

### Coding Style Preferences
- **Python Style**: Black formatter, type hints always
- **Indentation**: 4 spaces (Python), 2 spaces (JSON/YAML)
- **Line Length**: 88 characters (Black default)
- **Docstrings**: Google style with type annotations
- **Testing**: pytest with coverage reports
- **Version Control**: Git with descriptive commit messages

### Directory Structure
```
~/Development/
├── projects/       # Active coding projects
├── downloads/      # Downloaded resources
├── tools/          # Custom development tools
├── mcp-servers/    # MCP server implementations
├── scripts/        # Utility scripts
├── data/           # Data files for analysis
├── notebooks/      # Jupyter notebooks
├── configs/        # Configuration files
└── templates/      # Project templates
```

### Installed Tools & Versions
- Python 3.12.1
- pip 25.1.1
- Key packages:
  - pydantic 2.10.6
  - anthropic 0.54.0
  - pandas 2.3.0
  - numpy 1.26.4
  - fastapi 0.116.1
  - jupyter (latest)
  - black, flake8, mypy, pytest

### API Keys & Secrets Location
- **Environment Variables**: Check `~/.zshrc` and `.env` files
- **Local .env**: Per-project in `project_root/.env`
- **Global secrets**: `~/Development/configs/.env.global`
- **Never commit**: .env, .env.*, *_key.txt, secrets/

### Common Patterns & Templates

#### Python Project Structure
```python
project_name/
├── src/
│   └── project_name/
│       ├── __init__.py
│       ├── main.py
│       └── models.py
├── tests/
│   └── test_main.py
├── .env
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── README.md
```

#### Pydantic Model Template
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class StandardModel(BaseModel):
    id: str = Field(..., description="Unique identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
```

#### Error Handling Pattern
```python
from typing import Optional, Union
from pydantic import BaseModel

class Result(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    
def safe_operation() -> Result:
    try:
        # operation
        return Result(success=True, data=result)
    except Exception as e:
        return Result(success=False, error=str(e))
```

### MCP Server Configuration
- **Config Location**: `~/Development/configs/mcp_config.json`
- **Active Servers**:
  - data-analysis: Data processing with pandas
  - file-operations: File manipulation
  - code-intelligence: Code analysis and generation

### Database Connections
- **SQLite**: Default for local development
- **PostgreSQL**: Production preference
- **MongoDB**: For document storage
- **Redis**: Caching and sessions

### Testing Conventions
```python
# Test file naming: test_*.py or *_test.py
# Test function naming: test_*
# Use fixtures for common setup
# Aim for >80% coverage

import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_feature(sample_data):
    assert sample_data["key"] == "value"
```

### Git Workflow
```bash
# Feature branch workflow
git checkout -b feature/description
# Make changes
git add -A
git commit -m "type: description"
# Types: feat, fix, docs, test, refactor, style, chore
git push origin feature/description
```

### Performance Preferences
- Use generators for large datasets
- Prefer asyncio for I/O operations
- Cache expensive computations
- Profile before optimizing

### Security Practices
- Never hardcode secrets
- Use environment variables
- Validate all inputs with Pydantic
- Sanitize database queries
- Keep dependencies updated

### Documentation Standards
- README.md in every project
- Docstrings for all public functions
- Type hints for clarity
- Examples in documentation
- Keep CHANGELOG.md updated

### Debugging Tools
- **Debugger**: pdb/ipdb
- **Profiler**: cProfile
- **Memory**: memory_profiler
- **Logging**: Python logging module with rotation

### Common Commands Aliases
```bash
alias dev='cd ~/Development'
alias py='python3'
alias pip='pip3'
alias venv='python3 -m venv venv'
alias activate='source venv/bin/activate'
alias format='black .'
alias lint='flake8 .'
alias typecheck='mypy .'
alias test='pytest -v --cov'
```

### Project-Specific Notes
(This section updates per project)

### Recently Used Patterns
- Pydantic for Claude tool use structured outputs
- MCP servers for extended capabilities
- FastAPI for REST APIs
- SQLAlchemy for ORM

### TODO/Reminders
- Run black/flake8/mypy before commits
- Update requirements.txt when adding packages
- Check ~/Development/README.md for environment setup
- Use virtual environments for isolation

---
*This file helps Claude Code maintain consistency across sessions. Update as preferences change.*