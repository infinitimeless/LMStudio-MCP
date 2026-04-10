#!/bin/bash

# LMStudio-MCP Installation Script
# Supports multiple deployment methods

set -e

# Print a helpful message if something goes wrong
trap 'echo -e "\n\033[0;31m✗ Installation failed at line $LINENO. See error above.\033[0m"' ERR

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
INSTALL_METHOD=""
# Default to current directory rather than $HOME so tools like Pinokio
# that invoke the script from a specific working directory install in place.
INSTALL_DIR="$(pwd)"
PYTHON_CMD="python3"
VENV_NAME="venv"

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}    LMStudio-MCP Installer${NC}"
    echo -e "${BLUE}================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

# ---------------------------------------------------------------------------
# Detect the activate script path for the current or a named venv.
# On Linux/macOS venvs use bin/activate; on Windows (Git Bash / MSYS2) they
# use Scripts/activate.  Some tools (virtualenv, conda-based wrappers, etc.)
# may place it elsewhere, so we search rather than hard-code.
# Usage: get_activate_path [venv_dir]   (defaults to $VENV_NAME)
# ---------------------------------------------------------------------------
get_activate_path() {
    local venv_dir="${1:-$VENV_NAME}"
    for candidate in \
        "$venv_dir/bin/activate" \
        "$venv_dir/Scripts/activate" \
        "$venv_dir/scripts/activate"; do
        if [ -f "$candidate" ]; then
            echo "$candidate"
            return 0
        fi
    done
    return 1
}

# ---------------------------------------------------------------------------
# Check whether we are already inside an active virtual environment.
# Covers: venv, virtualenv, conda, pipenv, poetry, etc.
# ---------------------------------------------------------------------------
already_in_venv() {
    # $VIRTUAL_ENV is set by venv / virtualenv activate scripts and most wrappers
    if [ -n "$VIRTUAL_ENV" ]; then
        return 0
    fi
    # $CONDA_DEFAULT_ENV covers conda environments
    if [ -n "$CONDA_DEFAULT_ENV" ] && [ "$CONDA_DEFAULT_ENV" != "base" ]; then
        return 0
    fi
    return 1
}

# ---------------------------------------------------------------------------
# Find an existing venv under the given directory by looking for an activate
# script in common locations / sub-directories.
# Echoes the activate path if found, returns 1 otherwise.
# ---------------------------------------------------------------------------
find_existing_venv() {
    local search_dir="${1:-.}"
    # Check common venv directory names
    for name in venv .venv env .env virtualenv; do
        local candidate
        if candidate=$(get_activate_path "$search_dir/$name" 2>/dev/null); then
            echo "$candidate"
            return 0
        fi
    done
    # Also check if the search_dir itself is a venv root
    local candidate
    if candidate=$(get_activate_path "$search_dir" 2>/dev/null); then
        echo "$candidate"
        return 0
    fi
    return 1
}

check_requirements() {
    print_info "Checking system requirements..."

    # Check Python
    if ! command -v $PYTHON_CMD &> /dev/null; then
        if command -v python &> /dev/null; then
            PYTHON_CMD="python"
        else
            print_error "Python 3.7+ is required but not found"
            exit 1
        fi
    fi

    # Check Python version
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
        print_error "Python 3.7+ is required."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}')")
    print_success "Python $PYTHON_VERSION found"

    # Check Git
    if ! command -v git &> /dev/null; then
        print_error "Git is required but not found"
        exit 1
    fi
    print_success "Git found"

    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker found"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found (optional for containerized deployment)"
        DOCKER_AVAILABLE=false
    fi
}

show_menu() {
    echo ""
    print_info "Choose installation method:"
    echo "1) Local Python installation (recommended)"
    echo "2) Docker container"
    echo "3) Docker Compose"
    echo "4) Development setup"
    echo "5) Exit"
    echo ""
    read -p "Enter your choice (1-5): " choice

    case $choice in
        1) INSTALL_METHOD="local" ;;
        2) INSTALL_METHOD="docker" ;;
        3) INSTALL_METHOD="compose" ;;
        4) INSTALL_METHOD="dev" ;;
        5) exit 0 ;;
        *) print_error "Invalid choice"; show_menu ;;
    esac
}

# ---------------------------------------------------------------------------
# Setup virtual environment — shared by install_local and install_dev.
# Honours any already-active venv and searches for existing ones before
# creating a new one.  Works on Linux, macOS, and Windows (Git Bash/MSYS2).
# ---------------------------------------------------------------------------
setup_venv() {
    local install_dir="${1:-.}"

    if already_in_venv; then
        print_info "Already inside a virtual environment (${VIRTUAL_ENV:-$CONDA_DEFAULT_ENV}) — skipping venv creation."
        if ! command -v pip &> /dev/null; then
            print_warning "pip not found in the active venv. You may need to install it manually."
        fi
        ACTIVATE_PATH=""   # signal that activation is not needed
        return 0
    fi

    # Search for an existing venv inside the install directory
    local existing
    if existing=$(find_existing_venv "$install_dir"); then
        print_info "Found existing virtual environment at: $existing"
        print_info "Activating existing venv..."
        # shellcheck disable=SC1090
        source "$existing"
        ACTIVATE_PATH="$existing"
        return 0
    fi

    # No existing venv found — create one
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv "$install_dir/$VENV_NAME"

    local activate_path
    if activate_path=$(get_activate_path "$install_dir/$VENV_NAME"); then
        print_info "Activating virtual environment..."
        # shellcheck disable=SC1090
        source "$activate_path"
        ACTIVATE_PATH="$activate_path"
    else
        print_error "Could not find activate script after creating venv. Your platform may not be supported."
        exit 1
    fi
}

install_local() {
    print_info "Installing LMStudio-MCP locally..."

    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    # Clone repository (skip if already cloned)
    if [ -d ".git" ]; then
        print_info "Repository exists, pulling latest changes..."
        git pull
    else
        print_info "Cloning repository..."
        git clone https://github.com/infinitimeless/LMStudio-MCP.git .
    fi

    setup_venv "$INSTALL_DIR"

    print_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt

    # Generate a startup script using the detected (or relative) activate path.
    local rel_activate
    if [ -n "$ACTIVATE_PATH" ]; then
        rel_activate="${ACTIVATE_PATH#$INSTALL_DIR/}"
    else
        rel_activate=""
    fi

    if [ -n "$rel_activate" ]; then
        cat > start_lmstudio_mcp.sh << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "$rel_activate"
python lmstudio_bridge.py "\$@"
EOF
    else
        cat > start_lmstudio_mcp.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
python lmstudio_bridge.py "$@"
EOF
    fi
    chmod +x start_lmstudio_mcp.sh

    print_success "Local installation completed!"
    print_info "Installation directory: $INSTALL_DIR"
    print_info "To start: cd $INSTALL_DIR && ./start_lmstudio_mcp.sh"
}

install_docker() {
    if [ "$DOCKER_AVAILABLE" != "true" ]; then
        print_error "Docker is not available"
        exit 1
    fi

    print_info "Setting up Docker deployment..."

    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    print_info "Downloading Docker configuration..."
    curl -s https://raw.githubusercontent.com/infinitimeless/LMStudio-MCP/main/Dockerfile -o Dockerfile
    curl -s https://raw.githubusercontent.com/infinitimeless/LMStudio-MCP/main/.dockerignore -o .dockerignore

    print_info "Building Docker image..."
    docker build -t lmstudio-mcp .

    cat > run_docker.sh << 'EOF'
#!/bin/bash
docker run -it --rm --network host --name lmstudio-mcp-server lmstudio-mcp
EOF
    chmod +x run_docker.sh

    print_success "Docker installation completed!"
    print_info "To start: cd $INSTALL_DIR && ./run_docker.sh"
}

install_compose() {
    if [ "$DOCKER_AVAILABLE" != "true" ]; then
        print_error "Docker is not available"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is required but not found"
        exit 1
    fi

    print_info "Setting up Docker Compose deployment..."

    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    print_info "Downloading Docker Compose configuration..."
    curl -s https://raw.githubusercontent.com/infinitimeless/LMStudio-MCP/main/docker-compose.yml -o docker-compose.yml
    curl -s https://raw.githubusercontent.com/infinitimeless/LMStudio-MCP/main/Dockerfile -o Dockerfile
    curl -s https://raw.githubusercontent.com/infinitimeless/LMStudio-MCP/main/.dockerignore -o .dockerignore

    cat > start.sh << 'EOF'
#!/bin/bash
docker-compose up -d
EOF
    chmod +x start.sh

    cat > stop.sh << 'EOF'
#!/bin/bash
docker-compose down
EOF
    chmod +x stop.sh

    cat > logs.sh << 'EOF'
#!/bin/bash
docker-compose logs -f lmstudio-mcp
EOF
    chmod +x logs.sh

    print_success "Docker Compose installation completed!"
    print_info "Commands:"
    print_info "  Start: cd $INSTALL_DIR && ./start.sh"
    print_info "  Stop:  cd $INSTALL_DIR && ./stop.sh"
    print_info "  Logs:  cd $INSTALL_DIR && ./logs.sh"
}

install_dev() {
    print_info "Setting up development environment..."

    mkdir -p "$INSTALL_DIR"
    cd "$INSTALL_DIR"

    if [ -d ".git" ]; then
        print_info "Repository exists, pulling latest changes..."
        git pull
    else
        print_info "Cloning repository..."
        git clone https://github.com/infinitimeless/LMStudio-MCP.git .
    fi

    setup_venv "$INSTALL_DIR"

    print_info "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e .

    print_info "Installing development dependencies..."
    pip install pytest pytest-cov black flake8 mypy

    local rel_activate
    if [ -n "$ACTIVATE_PATH" ]; then
        rel_activate="${ACTIVATE_PATH#$INSTALL_DIR/}"
    else
        rel_activate=""
    fi

    if [ -n "$rel_activate" ]; then
        cat > dev_setup.sh << EOF
#!/bin/bash
cd "\$(dirname "\$0")"
source "$rel_activate"
echo "Development environment activated"
echo "Available commands:"
echo "  python lmstudio_bridge.py  - Run the bridge"
echo "  pytest                     - Run tests"
echo "  black .                    - Format code"
echo "  flake8 .                   - Lint code"
EOF
    else
        cat > dev_setup.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
echo "Development environment ready (using active venv)"
echo "Available commands:"
echo "  python lmstudio_bridge.py  - Run the bridge"
echo "  pytest                     - Run tests"
echo "  black .                    - Format code"
echo "  flake8 .                   - Lint code"
EOF
    fi
    chmod +x dev_setup.sh

    print_success "Development environment setup completed!"
    print_info "Installation directory: $INSTALL_DIR"
    print_info "To activate: cd $INSTALL_DIR && source dev_setup.sh"
}

create_mcp_config() {
    print_info "Creating MCP configuration example..."

    cat > mcp_config_example.json << EOF
{
  "lmstudio-mcp": {
    "command": "uvx",
    "args": [
      "https://github.com/infinitimeless/LMStudio-MCP"
    ]
  }
}
EOF

    if [ "$INSTALL_METHOD" = "local" ]; then
        local activate_snippet
        if [ -n "$ACTIVATE_PATH" ]; then
            activate_snippet="cd $INSTALL_DIR && source $ACTIVATE_PATH && python lmstudio_bridge.py"
        else
            activate_snippet="cd $INSTALL_DIR && python lmstudio_bridge.py"
        fi
        cat > mcp_config_local.json << EOF
{
  "lmstudio-mcp-local": {
    "command": "/bin/bash",
    "args": [
      "-c",
      "$activate_snippet"
    ]
  }
}
EOF
    fi

    if [ "$INSTALL_METHOD" = "docker" ]; then
        cat > mcp_config_docker.json << EOF
{
  "lmstudio-mcp-docker": {
    "command": "docker",
    "args": [
      "run",
      "-i",
      "--rm",
      "--network=host",
      "lmstudio-mcp"
    ]
  }
}
EOF
    fi

    print_success "MCP configuration examples created"
}

main() {
    print_header

    check_requirements
    show_menu

    case $INSTALL_METHOD in
        "local") install_local ;;
        "docker") install_docker ;;
        "compose") install_compose ;;
        "dev") install_dev ;;
    esac

    create_mcp_config

    echo ""
    print_success "Installation completed successfully!"
    print_info "Next steps:"
    print_info "1. Ensure LM Studio is running on localhost:1234"
    print_info "2. Configure Claude MCP with the provided configuration"
    print_info "3. Test the connection"
    echo ""
    print_info "For troubleshooting, see: https://github.com/infinitimeless/LMStudio-MCP/blob/main/TROUBLESHOOTING.md"
}

# Run main function
main "$@"
