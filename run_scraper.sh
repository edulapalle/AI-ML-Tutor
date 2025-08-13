#!/bin/bash

# YouTube Scraper Wrapper Script
# Automatically sets SSL certificate environment variables

echo "🔒 Setting up SSL certificates for YouTube scraper..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set SSL certificate environment variables
export SSL_CERT_FILE="$SCRIPT_DIR/corp_root_ca.pem"
export REQUESTS_CA_BUNDLE="$SCRIPT_DIR/corp_root_ca.pem"

# Verify SSL certificates are set
if [ -f "$SSL_CERT_FILE" ]; then
    echo "✅ SSL certificate found: $SSL_CERT_FILE"
    echo "✅ REQUESTS_CA_BUNDLE set: $REQUESTS_CA_BUNDLE"
else
    echo "❌ SSL certificate not found: $SSL_CERT_FILE"
    echo "Please ensure corp_root_ca.pem is in the project directory"
    exit 1
fi

# Check if URL is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run_scraper.sh <youtube_url>"
    echo "Example: ./run_scraper.sh \"https://www.youtube.com/watch?v=aircAruvnKk\""
    exit 1
fi

YOUTUBE_URL="$1"

echo "🚀 Running YouTube scraper with SSL certificates configured..."
echo "URL: $YOUTUBE_URL"
echo ""

# Run the Python scraper
python youtube_single_scraper.py "$YOUTUBE_URL"
