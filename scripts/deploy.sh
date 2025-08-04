#!/bin/bash

# Deployment Script for Personal Finance Dashboard
# Unix/Linux/macOS Shell Script

set -e  # Exit on any error

echo ""
echo "========================================"
echo "Personal Finance Dashboard - Deployment"
echo "========================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 is not installed or not in PATH"
    echo "Please install Python 3.10 or later"
    exit 1
fi

# Change to project root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo "📁 Current directory: $(pwd)"
echo ""

# Function to show menu
show_menu() {
    echo "Choose deployment option:"
    echo "1. Check prerequisites only"
    echo "2. Test backend locally"
    echo "3. Prepare Replit deployment"
    echo "4. Prepare Render deployment"
    echo "5. Prepare Appwrite Functions deployment"
    echo "6. Prepare all platforms"
    echo "7. Generate deployment checklist"
    echo "8. Full deployment preparation (test + all platforms + checklist)"
    echo "0. Exit"
    echo ""
}

# Function to run deployment manager
run_deploy_manager() {
    python3 scripts/deploy_manager.py "$@"
}

# Main menu loop
while true; do
    show_menu
    read -p "Enter your choice (0-8): " choice
    echo ""

    case $choice in
        0)
            echo "👋 Goodbye!"
            exit 0
            ;;
        1)
            echo "🔍 Running prerequisites check..."
            run_deploy_manager --check
            ;;
        2)
            echo "🧪 Running local tests..."
            run_deploy_manager --test --check
            ;;
        3)
            echo "📦 Preparing Replit deployment..."
            run_deploy_manager --platform replit
            ;;
        4)
            echo "📦 Preparing Render deployment..."
            run_deploy_manager --platform render
            ;;
        5)
            echo "📦 Preparing Appwrite Functions deployment..."
            run_deploy_manager --platform appwrite
            ;;
        6)
            echo "📦 Preparing deployment for all platforms..."
            run_deploy_manager --platform all
            ;;
        7)
            echo "📋 Generating deployment checklist..."
            run_deploy_manager --checklist
            ;;
        8)
            echo "🚀 Running full deployment preparation..."
            run_deploy_manager --test --platform all --checklist
            ;;
        *)
            echo "❌ Invalid choice. Please try again."
            ;;
    esac
    
    echo ""
    echo "========================================"
    echo ""
    read -p "Press Enter to return to menu or Ctrl+C to exit..."
    echo ""
done
