#!/usr/bin/env python3
"""
Crypto/Forex Alarm Bot Setup Script
This script automates the necessary steps to set up the project.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_colored(text, color='white'):
    """Prints text in a specified color."""
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'purple': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'end': '\033[0m'
    }
    print(f"{colors.get(color, colors['white'])}{text}{colors['end']}")

def check_python_version():
    """Checks the Python version."""
    if sys.version_info < (3, 8):
        print_colored("❌ Python 3.8 or higher is required!", 'red')
        sys.exit(1)
    print_colored(f"✅ Python {sys.version.split()[0]} is available", 'green')

def create_virtual_environment():
    """Creates a virtual environment."""
    venv_path = Path("venv")
    
    if venv_path.exists():
        print_colored("⚠️  Virtual environment already exists", 'yellow')
        return
    
    print_colored("🔧 Creating virtual environment...", 'blue')
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        print_colored("✅ Virtual environment created", 'green')
    except subprocess.CalledProcessError:
        print_colored("❌ Failed to create virtual environment!", 'red')
        sys.exit(1)

def install_requirements():
    """Installs required packages."""
    print_colored("📦 Installing packages...", 'blue')
    
    # Pip path for Windows and Linux
    if os.name == 'nt':  # Windows
        pip_path = os.path.join("venv", "Scripts", "pip")
    else:  # Linux/Mac
        pip_path = os.path.join("venv", "bin", "pip")
    
    try:
        subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
        print_colored("✅ All packages installed successfully", 'green')
    except subprocess.CalledProcessError:
        print_colored("❌ Package installation failed!", 'red')
        sys.exit(1)

def create_env_file():
    """Creates the environment variables file."""
    env_file = Path(".env")
    
    if env_file.exists():
        print_colored("⚠️  .env file already exists", 'yellow')
        return
    
    print_colored("🔧 Creating .env file...", 'blue')
    
    # Copy from .env.template
    template_file = Path(".env.template")
    if template_file.exists():
        shutil.copy(".env.template", ".env")
        print_colored("✅ .env file created (from .env.template)", 'green')
    else:
        # Create manually
        with open(".env", "w", encoding="utf-8") as f:
            f.write("""# Telegram Bot Token (Required)
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Binance API (Optional)
BINANCE_API_KEY=your_binance_api_key_here
BINANCE_API_SECRET=your_binance_api_secret_here

# Exchange Rate API (Optional)
EXCHANGE_RATE_API_KEY=your_exchange_rate_api_key_here
""")
        print_colored("✅ .env file created", 'green')

def create_directories():
    """Creates necessary directories."""
    dirs = ["charts", "logs"]
    
    for dir_name in dirs:
        dir_path = Path(dir_name)
        if not dir_path.exists():
            dir_path.mkdir()
            print_colored(f"✅ {dir_name} directory created", 'green')

def print_setup_complete():
    """Prints the setup complete message."""
    print_colored("\n" + "="*50, 'cyan')
    print_colored("🎉 SETUP COMPLETE! 🎉", 'green')
    print_colored("="*50, 'cyan')
    
    print_colored("\n📋 NEXT STEPS:", 'yellow')
    print_colored("1. Edit the .env file and add your bot token", 'white')
    print_colored("2. Activate the virtual environment:", 'white')
    
    if os.name == 'nt':  # Windows
        print_colored("   venv\\Scripts\\activate", 'cyan')
    else:  # Linux/Mac
        print_colored("   source venv/bin/activate", 'cyan')
    
    print_colored("3. Run the bot:", 'white')
    print_colored("   python main.py", 'cyan')
    print_colored("\n📚 Guide to getting your Telegram Bot Token:", 'yellow')
    print_colored("   1. Send a message to @BotFather", 'white')
    print_colored("   2. Use the /newbot command", 'white')
    print_colored("   3. Set a bot name and username", 'white')
    print_colored("   4. Add the token you receive to the .env file", 'white')

def main():
    """Main setup function."""
    print_colored("🚀 Starting Crypto/Forex Alarm Bot Setup...", 'purple')
    print_colored("="*50, 'purple')
    
    # Step-by-step setup
    check_python_version()
    create_virtual_environment()
    install_requirements()
    create_env_file()
    create_directories()
    
    print_setup_complete()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print_colored("\n❌ Setup cancelled by user", 'red')
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Setup error: {e}", 'red')
        sys.exit(1)
