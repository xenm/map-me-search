# ⚡ Quick Start - AI Places Search

## 🎯 What This Does
Searches for nearby places based on your city and preferences using Google's Gemini AI.

## 🏃 3 Steps to Run

### 1️⃣ Install Dependencies
```bash
pip install google-adk python-dotenv
```

### 2️⃣ Add Your API Key
1. Get API key: https://aistudio.google.com/app/apikey
2. Create `.env` file:
   ```bash
   cp .env.example .env
   ```
3. Edit `.env` and add your key:
   ```
   GOOGLE_API_KEY=your_actual_key_here
   ```

### 3️⃣ Run It!
```bash
python main.py
```

## 💡 Example Usage

```
📍 Enter city name: Tokyo
❤️  What do you like?: ramen and temples

🔍 Searching...

📍 SEARCH RESULTS
============================================================
Here are some great places in Tokyo for ramen and temples:

1. **Ichiran Ramen (Shibuya)** - Famous tonkotsu ramen chain...
2. **Senso-ji Temple** - Tokyo's oldest Buddhist temple...
3. **Afuri Ramen** - Known for yuzu-infused ramen...
...
============================================================
```

## 📚 More Information
- **Full Documentation**: See `PROJECT_README.md`
- **Setup Troubleshooting**: See `SETUP.md`
- **Verify Installation**: Run `python verify_setup.py`

## 🎨 Project Structure
```
map-me-search/
├── main.py              # 👈 Run this file
├── requirements.txt     # Dependencies
├── .env.example         # Template for API key
└── .env                 # Your actual API key (create this)
```

---
🚀 **Ready?** Run `python main.py` and start exploring!
