# 🗺️ AI-Powered Nearby Places Search

Search for nearby places based on city name and your preferences using Google's Gemini AI and Agent Development Kit.

## ⚡ Quick Start

```bash
# 1. Run installation script (macOS/Linux)
./install.sh

# 2. Add your Google API key to .env file
# Get key from: https://aistudio.google.com/app/apikey

# 3. Run the application
python3 main.py
```

## ✨ Features

- 🤖 **AI-Powered**: Uses Google's Gemini 2.0 model for intelligent search
- 🔍 **Smart Search**: Leverages Google Search for real-time information
- 🎯 **Personalized**: Finds places based on your specific preferences
- 🔄 **Reliable**: Automatic retry logic for API calls
- 📝 **User-Friendly**: Simple command-line interface

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | Get started in 3 steps |
| [SETUP.md](SETUP.md) | Detailed setup instructions |
| [PROJECT_README.md](PROJECT_README.md) | Full project documentation |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture |
| [COMMANDS.md](COMMANDS.md) | Command reference |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete project overview |

## 🚀 Example Usage

```
📍 Enter city name: Tokyo
❤️  What do you like?: ramen and temples

🔍 Searching for places in Tokyo...

📍 SEARCH RESULTS
============================================================
1. Ichiran Ramen (Shibuya) - Famous tonkotsu ramen...
2. Senso-ji Temple - Tokyo's oldest Buddhist temple...
3. Afuri Ramen - Known for yuzu-infused ramen...
...
============================================================
```

## 🛠️ Tech Stack

- **Framework**: Google Agent Development Kit (ADK)
- **AI Model**: Gemini 2.0 Flash Exp
- **Language**: Python 3.8+
- **Tools**: Google Search integration

## 📦 Installation

### Automated (Recommended)
```bash
chmod +x install.sh
./install.sh
```

### Manual
```bash
pip3 install -r requirements.txt
cp .env.example .env
# Add your GOOGLE_API_KEY to .env
python3 verify_setup.py
```

## 🔐 API Key Setup

1. Get your free API key: [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Copy `.env.example` to `.env`
3. Add your key: `GOOGLE_API_KEY=your_key_here`

## 🧪 Testing

```bash
# Test imports
python3 test_imports.py

# Verify complete setup
python3 verify_setup.py

# Run the app
python3 main.py
```

## 📋 Requirements

- Python 3.8 or higher
- Google Gemini API key (free tier available)
- Internet connection

## 🤝 Contributing

This is an educational project demonstrating Google ADK usage. Feel free to fork and extend!

## 📄 License

See [LICENSE](LICENSE) file for details.

## 🆘 Support

- Check [SETUP.md](SETUP.md) for troubleshooting
- Run `python3 verify_setup.py` for diagnostics
- Review documentation in the docs above

---

**Built with** ❤️ **using Google Agent Development Kit**
