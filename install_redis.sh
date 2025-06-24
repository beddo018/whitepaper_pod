#!/bin/bash

# Redis installation helper script

echo "Checking Redis installation..."

if command -v redis-server >/dev/null 2>&1; then
    echo "✅ Redis is already installed!"
    redis-server --version
    exit 0
fi

echo "Redis not found. Installing..."

# Detect OS and install Redis
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    if command -v brew >/dev/null 2>&1; then
        echo "Installing Redis via Homebrew..."
        brew install redis
        brew services start redis
    else
        echo "Homebrew not found. Please install Homebrew first:"
        echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        exit 1
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    if command -v apt-get >/dev/null 2>&1; then
        echo "Installing Redis via apt-get..."
        sudo apt-get update
        sudo apt-get install -y redis-server
        sudo systemctl start redis-server
    elif command -v yum >/dev/null 2>&1; then
        echo "Installing Redis via yum..."
        sudo yum install -y redis
        sudo systemctl start redis
    else
        echo "Package manager not found. Please install Redis manually:"
        echo "  https://redis.io/download"
        exit 1
    fi
else
    echo "Unsupported OS. Please install Redis manually:"
    echo "  https://redis.io/download"
    exit 1
fi

echo "✅ Redis installed successfully!"
redis-server --version 