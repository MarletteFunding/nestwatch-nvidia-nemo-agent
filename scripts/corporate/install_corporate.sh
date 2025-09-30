#!/bin/bash
# Corporate-Friendly Installation Script for Multi-Provider AI System
# Handles Zscaler proxy environments and corporate security constraints

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Detect corporate environment
detect_corporate_env() {
    log "🔍 Detecting corporate environment..."
    
    CORPORATE_DETECTED=false
    
    # Check for proxy environment variables
    if [[ -n "$HTTP_PROXY" || -n "$HTTPS_PROXY" || -n "$http_proxy" || -n "$https_proxy" ]]; then
        warn "Proxy environment detected"
        CORPORATE_DETECTED=true
    fi
    
    # Check for common corporate domains
    if [[ "$HOSTNAME" == *"corp"* || "$HOSTNAME" == *"corporate"* ]]; then
        warn "Corporate hostname detected: $HOSTNAME"
        CORPORATE_DETECTED=true
    fi
    
    # Check for Zscaler indicators
    if command -v zscaler &> /dev/null || [[ -n "$ZSCALER_PROXY" ]]; then
        warn "Zscaler environment detected"
        CORPORATE_DETECTED=true
    fi
    
    if [[ "$CORPORATE_DETECTED" == "true" ]]; then
        success "Corporate environment detected - using proxy-friendly installation"
    else
        log "Standard environment detected"
    fi
}

# Configure pip for corporate environments
configure_pip_corporate() {
    log "🔧 Configuring pip for corporate environment..."
    
    # Create pip config directory
    mkdir -p ~/.pip
    
    # Create pip.conf with corporate-friendly settings
    cat > ~/.pip/pip.conf << EOF
[global]
timeout = 300
retries = 10
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
               download.pytorch.org
               developer.download.nvidia.com
               huggingface.co
               cdn-lfs.huggingface.co

[install]
trusted-host = pypi.org
               pypi.python.org
               files.pythonhosted.org
               download.pytorch.org
               developer.download.nvidia.com
               huggingface.co
               cdn-lfs.huggingface.co
EOF
    
    # Add proxy configuration if detected
    if [[ -n "$HTTPS_PROXY" || -n "$https_proxy" ]]; then
        PROXY_URL="${HTTPS_PROXY:-$https_proxy}"
        echo "proxy = $PROXY_URL" >> ~/.pip/pip.conf
        log "Added proxy configuration: $PROXY_URL"
    fi
    
    success "Pip configured for corporate environment"
}

# Install dependencies in corporate-friendly way
install_dependencies_corporate() {
    log "📦 Installing dependencies with corporate-friendly methods..."
    
    # Activate virtual environment
    if [[ ! -d "venv" ]]; then
        error "Virtual environment not found. Please create it first with: python -m venv venv"
        exit 1
    fi
    
    source venv/bin/activate
    
    # Upgrade pip first
    log "Upgrading pip..."
    pip install --upgrade pip --timeout 300 --retries 10
    
    # Install dependencies in stages for better corporate network handling
    log "Installing core FastAPI dependencies..."
    pip install fastapi>=0.104.1 uvicorn[standard]>=0.24.0 pydantic>=2.5.0 python-multipart>=0.0.6 --timeout 300 --retries 10
    
    log "Installing HTTP and SSL handling libraries..."
    pip install requests>=2.31.0 urllib3>=2.0.0 certifi>=2023.7.22 --timeout 300 --retries 10
    
    log "Installing AI provider libraries..."
    pip install openai>=1.0.0 anthropic>=0.18.0 jsonschema>=4.25.0 --timeout 300 --retries 10
    
    log "Installing AWS Bedrock integration..."
    pip install boto3>=1.34.0 botocore>=1.34.0 --timeout 300 --retries 10
    
    log "Installing PyTorch (corporate-friendly)..."
    # Use CPU-only PyTorch for corporate environments to avoid CUDA issues
    pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cpu --timeout 300 --retries 10
    
    log "Installing Hugging Face libraries..."
    pip install transformers>=4.21.0 huggingface_hub>=0.17.0 tokenizers>=0.14.0 --timeout 300 --retries 10
    
    log "Installing utility libraries..."
    pip install python-dotenv>=1.0.0 pyyaml>=6.0.0 omegaconf>=2.3.0 hydra-core>=1.3.0 --timeout 300 --retries 10
    
    log "Installing system monitoring utilities..."
    pip install psutil>=5.9.0 packaging>=23.0 typing-extensions>=4.8.0 --timeout 300 --retries 10
    
    success "All dependencies installed successfully"
}

# Test network connectivity
test_connectivity() {
    log "🌐 Testing network connectivity to required services..."
    
    declare -A test_urls=(
        ["PyPI"]="https://pypi.org/simple/"
        ["AWS"]="https://aws.amazon.com/"
        ["Anthropic"]="https://api.anthropic.com/"
        ["OpenAI"]="https://api.openai.com/"
        ["Hugging Face"]="https://huggingface.co/"
    )
    
    for service in "${!test_urls[@]}"; do
        url="${test_urls[$service]}"
        if curl -s --max-time 10 --head "$url" > /dev/null 2>&1; then
            success "$service: Connected"
        else
            warn "$service: Connection failed or blocked"
        fi
    done
}

# Setup corporate-friendly model configuration
setup_corporate_models() {
    log "🤖 Setting up corporate-friendly model configuration..."
    
    # Create models directory
    mkdir -p models
    
    # Create corporate model configuration
    cat > models/corporate_config.json << EOF
{
  "corporate_models": [
    "microsoft/DialoGPT-medium",
    "microsoft/DialoGPT-small",
    "gpt2",
    "distilgpt2"
  ],
  "download_method": "huggingface_hub",
  "cache_dir": "./models",
  "offline_mode": false,
  "proxy_friendly": true,
  "corporate_safe": true,
  "max_model_size_gb": 2
}
EOF
    
    success "Corporate model configuration created"
}

# Create corporate environment file
create_corporate_env() {
    log "📝 Creating corporate environment configuration..."
    
    if [[ ! -f ".env.local" ]]; then
        cp zscaler.env.example .env.local
        success "Corporate environment file created: .env.local"
        warn "Please edit .env.local with your API keys and corporate settings"
    else
        warn ".env.local already exists - skipping creation"
    fi
}

# Main installation function
main() {
    echo "🚀 Starting Corporate-Friendly Multi-Provider AI Installation"
    echo "============================================================"
    
    # Change to project directory
    cd "$(dirname "$0")/.."
    
    # Detect environment
    detect_corporate_env
    
    # Configure for corporate environment
    if [[ "$CORPORATE_DETECTED" == "true" ]]; then
        configure_pip_corporate
    fi
    
    # Test connectivity
    test_connectivity
    
    # Install dependencies
    install_dependencies_corporate
    
    # Setup models
    setup_corporate_models
    
    # Create environment file
    create_corporate_env
    
    echo ""
    echo "🎉 Corporate installation complete!"
    echo "============================================================"
    echo "📋 Next Steps:"
    echo "   1. Edit .env.local with your API keys"
    echo "   2. Configure your corporate proxy settings if needed"
    echo "   3. Test the installation: python scripts/setup_zscaler_environment.py"
    echo "   4. Start the server: cd backend && python app.py"
    echo ""
    echo "🔧 Corporate Environment Notes:"
    echo "   - PyTorch installed with CPU-only support"
    echo "   - Heavy NeMo dependencies commented out"
    echo "   - Proxy-friendly pip configuration applied"
    echo "   - Extended timeouts for corporate networks"
    echo "============================================================"
}

# Run main function
main "$@"
