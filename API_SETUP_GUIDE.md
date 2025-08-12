# API Configuration Setup Guide

Welcome to the Personal Life Coordination Agents API setup guide! This document will help you configure all the necessary API keys for your agents to function properly.

## 🚀 Quick Start

1. **Run the interactive setup script:**
   ```bash
   python setup_api_keys.py
   ```

2. **For quick setup with just essentials:**
   - Choose option `2` in the setup script
   - This will configure OpenAI API and Google Calendar only

3. **Check configuration status:**
   - Choose option `3` in the setup script to see what's configured

## 📋 Required vs Optional APIs

### ✅ Required (Essential Functionality)

| API | Purpose | Agent | Get Your Key |
|-----|---------|-------|--------------|
| **OpenAI API** | Core AI functionality | All Agents | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) |
| **Google Calendar** | Calendar management | Nani (Scheduler) | [console.developers.google.com](https://console.developers.google.com/) |

### 🔧 Optional (Enhanced Features)

| Category | API | Purpose | Agent | Get Your Key |
|----------|-----|---------|-------|--------------|
| **AI Alternative** | Anthropic Claude | Alternative AI provider | All | [console.anthropic.com](https://console.anthropic.com/) |
| **Weather** | OpenWeather | Weather-aware scheduling | Nani | [openweathermap.org/api](https://openweathermap.org/api) |
| **Fitness** | Fitbit | Device integration | Luna | [dev.fitbit.com/apps](https://dev.fitbit.com/apps) |
| **Fitness** | Garmin Connect | Device integration | Luna | [developer.garmin.com](https://developer.garmin.com/) |
| **Fitness** | Strava | Activity tracking | Luna | [developers.strava.com](https://developers.strava.com/) |
| **Nutrition** | USDA Food Database | Nutritional data | Milo | [fdc.nal.usda.gov/api-guide.html](https://fdc.nal.usda.gov/api-guide.html) |
| **Nutrition** | Nutritionix | Nutrition analysis | Milo | [developer.nutritionix.com](https://developer.nutritionix.com/) |
| **Nutrition** | Spoonacular | Recipe database | Milo | [spoonacular.com/food-api](https://spoonacular.com/food-api) |
| **Shopping** | Walmart API | Product prices | Bucky | [developer.walmart.com](https://developer.walmart.com/) |
| **Shopping** | Target API | Product info | Bucky | [developer.target.com](https://developer.target.com/) |
| **Shopping** | Kroger API | Grocery prices | Bucky | [developer.kroger.com](https://developer.kroger.com/) |

## 🔐 Detailed Setup Instructions

### 1. OpenAI API Key (REQUIRED)

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key and save it securely
5. **Important**: This key starts with `sk-proj-` or `sk-`

**Cost**: Pay-per-use, typically $5-20/month for moderate usage

### 2. Google Calendar API (REQUIRED for Nani)

1. Go to [Google Cloud Console](https://console.developers.google.com/)
2. Create a new project or select existing
3. Enable the **Google Calendar API**
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Set application type to "Web application"
6. Add authorized redirect URI: `http://localhost:8000/auth/google/callback`
7. Note down Client ID and Client Secret

**Cost**: Free (up to generous quotas)

### 3. Fitness APIs (Optional for Luna)

#### Fitbit API
1. Go to [Fitbit Developer](https://dev.fitbit.com/apps)
2. Register a new app with OAuth 2.0 Application Type: "Personal"
3. Set Callback URL to: `http://localhost:8000/auth/fitbit/callback`

#### Strava API
1. Go to [Strava Developers](https://developers.strava.com/)
2. Create an app in "My API Application"
3. Set Authorization Callback Domain to: `localhost`

### 4. Nutrition APIs (Optional for Milo)

#### USDA Food Database
1. Go to [USDA FDC](https://fdc.nal.usda.gov/api-guide.html)
2. Sign up for a free account
3. Generate an API key

#### Nutritionix
1. Visit [Nutritionix Developer](https://developer.nutritionix.com/)
2. Create a free account
3. Create an application to get App ID and API Key

#### Spoonacular
1. Go to [Spoonacular Food API](https://spoonacular.com/food-api)
2. Sign up for an account
3. Subscribe to a plan (free tier available)

### 5. Shopping APIs (Optional for Bucky)

Most shopping APIs require business applications. For personal use, consider:

- **Walmart Open API**: Apply at [developer.walmart.com](https://developer.walmart.com/)
- **Target Partners**: Limited to approved partners
- **Kroger Developer**: Apply at [developer.kroger.com](https://developer.kroger.com/)

## 🛠️ Manual Configuration

If you prefer to configure manually, edit the `.env` file:

```bash
# Core AI APIs (REQUIRED)
OPENAI_API_KEY=sk-proj-your-key-here
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# Google Calendar (REQUIRED for Nani)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Optional APIs
OPENWEATHER_API_KEY=your-weather-key
FITBIT_CLIENT_ID=your-fitbit-id
# ... and so on
```

## 🔍 Verification

### Check Configuration Status
```bash
python setup_api_keys.py
# Choose option 3 to view status
```

### Test Configuration Loading
```bash
python shared/utils/config_loader.py
```

### Test Individual Agents
```bash
# Test Nani (Scheduler)
python agents/nani_scheduler/mcp_server.py

# Test Luna (Health)
python agents/luna_health/mcp_server.py

# Test Milo (Nutrition)
python agents/milo_nutrition/mcp_server.py

# Test Bucky (Shopping)
python agents/bucky_shopping/mcp_server.py
```

## 🚨 Troubleshooting

### Common Issues

1. **"Environment variable not set" warnings**
   - These are normal for optional APIs
   - Only worry about required APIs (OpenAI, Google Calendar)

2. **Google Calendar OAuth errors**
   - Verify redirect URI exactly matches: `http://localhost:8000/auth/google/callback`
   - Make sure Google Calendar API is enabled in Google Cloud Console

3. **OpenAI API errors**
   - Verify your API key starts with `sk-`
   - Check you have credits/billing set up in OpenAI dashboard

4. **Permission errors**
   - Make sure the script is executable: `chmod +x setup_api_keys.py`

### Getting Help

1. Check the configuration status: `python setup_api_keys.py` → option 3
2. Review the logs when starting agents
3. Verify your `.env` file has the correct format
4. Make sure no spaces around the `=` in `.env` file

## 🔒 Security Best Practices

1. **Never commit API keys** to version control
2. **Use environment variables** (.env file is already in .gitignore)
3. **Rotate keys regularly** for production use
4. **Use minimum required permissions** for each API
5. **Monitor usage** to detect unexpected activity

## 💰 Cost Considerations

- **OpenAI**: ~$5-20/month for typical personal use
- **Google Calendar**: Free for personal use
- **Most other APIs**: Free tiers available, costs scale with usage
- **Shopping APIs**: Often require business partnerships

## 🎯 Next Steps

1. **Start with essentials**: OpenAI + Google Calendar
2. **Test basic functionality** with those two APIs
3. **Gradually add optional APIs** based on which features you want
4. **Monitor usage and costs** as you go

---

Need help? The interactive setup script (`python setup_api_keys.py`) will guide you through everything step by step!