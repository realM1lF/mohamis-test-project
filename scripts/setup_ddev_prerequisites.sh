#!/bin/bash
# Setup script for DDEV prerequisites
# Run this script to prepare your system for DDEV-based development

set -e

echo "========================================"
echo "Mohami DDEV Prerequisites Setup"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to print status
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check OS
print_status "Detecting operating system..."
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    if command_exists apt-get; then
        DISTRO="ubuntu"
    elif command_exists yum; then
        DISTRO="rhel"
    elif command_exists pacman; then
        DISTRO="arch"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    print_error "Unsupported operating system: $OSTYPE"
    exit 1
fi
print_success "Detected: $OS"

# Check Docker
print_status "Checking Docker..."
if command_exists docker; then
    DOCKER_VERSION=$(docker --version)
    print_success "Docker found: $DOCKER_VERSION"
    
    # Check if Docker is running
    if docker info >/dev/null 2>&1; then
        print_success "Docker is running"
    else
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
else
    print_error "Docker not found. Please install Docker:"
    echo "  Linux: https://docs.docker.com/engine/install/"
    echo "  Mac: https://docs.docker.com/desktop/install/mac-install/"
    exit 1
fi

# Check Docker Compose
print_status "Checking Docker Compose..."
if command_exists docker-compose || docker compose version >/dev/null 2>&1; then
    print_success "Docker Compose found"
else
    print_error "Docker Compose not found. Please install Docker Compose."
    exit 1
fi

# Check DDEV
print_status "Checking DDEV..."
if command_exists ddev; then
    DDEV_VERSION=$(ddev version | head -1)
    print_success "DDEV found: $DDEV_VERSION"
else
    print_warning "DDEV not found. Installing..."
    
    if [[ "$OS" == "linux" ]]; then
        # Install DDEV on Linux
        curl -fsSL https://raw.githubusercontent.com/ddev/ddev/main/scripts/install_ddev.sh | bash
    elif [[ "$OS" == "macos" ]]; then
        # Install DDEV on macOS
        if command_exists brew; then
            brew install ddev/ddev/ddev
        else
            print_error "Homebrew not found. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    fi
    
    if command_exists ddev; then
        print_success "DDEV installed successfully"
    else
        print_error "Failed to install DDEV"
        exit 1
    fi
fi

# Check mkcert for local HTTPS
print_status "Checking mkcert..."
if command_exists mkcert; then
    print_success "mkcert found"
else
    print_warning "mkcert not found. Installing..."
    
    if [[ "$OS" == "linux" ]]; then
        if [[ "$DISTRO" == "ubuntu" ]]; then
            sudo apt-get update && sudo apt-get install -y libnss3-tools
        fi
    elif [[ "$OS" == "macos" ]]; then
        brew install mkcert
        brew install nss  # For Firefox support
    fi
    
    # Install mkcert binary
    curl -fsSL https://github.com/FiloSottile/mkcert/releases/download/v1.4.4/mkcert-v1.4.4-linux-amd64 -o /tmp/mkcert
    chmod +x /tmp/mkcert
    sudo mv /tmp/mkcert /usr/local/bin/
    
    # Install local CA
    mkcert -install
    
    if command_exists mkcert; then
        print_success "mkcert installed successfully"
    fi
fi

# Create workspace directories
print_status "Creating workspace directories..."
WORKSPACE_BASE="$HOME/ki-data/customer-workspaces"
mkdir -p "$WORKSPACE_BASE"
mkdir -p "$HOME/ki-data/shared/composer-cache"
mkdir -p "$HOME/ki-data/shared/npm-cache"
mkdir -p "$HOME/ki-data/shared/ddev-global"
mkdir -p "$HOME/ki-data/backups"
print_success "Workspace directories created"

# Check Python dependencies
print_status "Checking Python dependencies..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
    
    # Check for PyYAML
    if python3 -c "import yaml" 2>/dev/null; then
        print_success "PyYAML is installed"
    else
        print_warning "PyYAML not found. Installing..."
        pip3 install pyyaml
    fi
else
    print_error "Python 3 not found. Please install Python 3."
    exit 1
fi

# Configure DDEV
print_status "Configuring DDEV..."
ddev config global --mutagen-enabled=true --performance-mode=mutagen
print_success "DDEV configured"

# Check Git
print_status "Checking Git..."
if command_exists git; then
    GIT_VERSION=$(git --version)
    print_success "Git found: $GIT_VERSION"
    
    # Configure Git if not already configured
    if [[ -z $(git config --global user.email) ]]; then
        print_warning "Git email not configured"
        echo "Please configure Git user email:"
        echo "  git config --global user.email \"your@email.com\""
    fi
    
    if [[ -z $(git config --global user.name) ]]; then
        print_warning "Git user name not configured"
        echo "Please configure Git user name:"
        echo "  git config --global user.name \"Your Name\""
    fi
else
    print_error "Git not found. Please install Git."
    exit 1
fi

# SSH key check
print_status "Checking SSH keys..."
if [[ -f "$HOME/.ssh/id_rsa" ]] || [[ -f "$HOME/.ssh/id_ed25519" ]]; then
    print_success "SSH key found"
else
    print_warning "No SSH key found. Consider generating one for Git access:"
    echo "  ssh-keygen -t ed25519 -C \"your@email.com\""
fi

# Test DDEV
print_status "Testing DDEV..."
TEST_PROJECT="/tmp/ddev-test-$$"
mkdir -p "$TEST_PROJECT"
cd "$TEST_PROJECT"
ddev config --project-type=php --docroot=.
ddev start >/dev/null 2>&1
ddev exec echo "DDEV is working!" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    print_success "DDEV test passed"
else
    print_error "DDEV test failed"
fi
ddev delete -y >/dev/null 2>&1
cd - >/dev/null 2>&1
rm -rf "$TEST_PROJECT"

echo ""
echo "========================================"
echo "Prerequisites Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Review customer configuration: config/customers.yaml"
echo "  2. Setup a customer workspace:"
echo "     python3 scripts/setup_customer_ddev.py --customer alp-shopware --setup"
echo "  3. Or use Makefile:"
echo "     make -f Makefile.ddev ddev-setup CUSTOMER=alp-shopware"
echo ""
echo "For help:"
echo "  python3 scripts/setup_customer_ddev.py --help"
echo "  make -f Makefile.ddev help"
echo ""
