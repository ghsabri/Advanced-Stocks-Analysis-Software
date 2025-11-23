#!/usr/bin/env python3
"""
Quick Start Script for MJ Software Stock Analysis Platform
Tests if all dependencies are installed and launches the app
"""

import sys
import subprocess

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = [
        'streamlit',
        'pandas',
        'numpy',
        'plotly',
        'requests'
    ]
    
    missing_packages = []
    
    print("🔍 Checking dependencies...\n")
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("\n📦 Installing missing packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
        print("\n✅ All packages installed!")
    else:
        print("\n✅ All dependencies installed!")
    
    return True

def launch_app():
    """Launch the Streamlit app"""
    print("\n🚀 Launching MJ Software Stock Analysis Platform...")
    print("📍 App will open at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the server\n")
    
    try:
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down gracefully...")
        sys.exit(0)

if __name__ == "__main__":
    print("=" * 60)
    print("🏢 MJ Software LLC - Stock Analysis Platform")
    print("📊 Development Setup & Launch")
    print("=" * 60)
    print()
    
    if check_dependencies():
        launch_app()
