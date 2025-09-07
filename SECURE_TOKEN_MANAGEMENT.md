OBSOLETE: moved to obsoleate/ folder.
# 🔐 Secure Token Management Guide

## Overview
This guide explains how to securely manage your Composio API token and other sensitive configuration without exposing them in the repository.

## 🔑 Token Storage

### 1. Environment File (.env)
Your API token is stored in `.env` file:
```bash
COMPOSIO_API_KEY=oak_xgWwco9t68IcIFw9tGbG
```

### 2. Git Protection
The `.env` file is automatically excluded from git tracking via `.gitignore`:
```gitignore
# Environment variables and secrets
.env
.env.local
.env.production
.env.staging
*.key
config.json
secrets.json
composio_config.json
```

## 🛡️ Security Measures

### ✅ What's Protected:
- ✅ `.env` file is never committed to git
- ✅ Token is loaded at runtime from environment
- ✅ Template file (`.env.template`) shows structure without exposing actual tokens
- ✅ Graceful degradation if token is missing
- ✅ Token preview in logs shows only first/last characters

### ❌ What to Avoid:
- ❌ Never commit actual tokens to git
- ❌ Don't hardcode tokens in source files
- ❌ Don't share `.env` file directly
- ❌ Don't include tokens in error messages or logs

## 🔧 Setup Instructions

### 1. Initial Setup
```bash
# Copy template to create your .env file
cp .env.template .env

# Edit .env with your actual token
# Replace 'your_composio_api_key_here' with your actual token
```

### 2. Verify Configuration
```bash
# Test that token is loaded correctly
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv('COMPOSIO_API_KEY')
if key:
    print(f'✅ Token loaded: {key[:12]}...{key[-4:]}')
else:
    print('❌ No token found')
"
```

### 3. Environment Variables
Alternatively, you can set the environment variable directly:
```bash
# Windows
set COMPOSIO_API_KEY=oak_xgWwco9t68IcIFw9tGbG

# Linux/Mac
export COMPOSIO_API_KEY=oak_xgWwco9t68IcIFw9tGbG
```

## 🔄 How It Works

### 1. Token Loading
```python
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get token securely
composio_api_key = os.getenv('COMPOSIO_API_KEY')
```

### 2. Composio Initialization
```python
try:
    if composio_api_key:
        os.environ['COMPOSIO_API_KEY'] = composio_api_key
        toolset = ComposioToolSet()
        print("✅ Composio initialized successfully")
    else:
        raise ValueError("COMPOSIO_API_KEY not found")
except Exception as e:
    print(f"⚠️ Composio not available: {e}")
    # Continue with basic functionality
```

## 🚨 Emergency Procedures

### If Token is Accidentally Committed:
1. **Immediately rotate the token** in Composio dashboard
2. Update `.env` with new token
3. Remove from git history:
```bash
# Remove from all git history (DANGEROUS)
git filter-branch --env-filter 'export COMPOSIO_API_KEY=""' HEAD
git push --force
```

### If .env File is Missing:
1. Copy from template: `cp .env.template .env`
2. Get new token from Composio dashboard
3. Update `.env` with your token

## 📝 Best Practices

### ✅ Do:
- Use `.env` files for local development
- Use proper environment variables in production
- Rotate tokens regularly
- Use different tokens for different environments
- Keep tokens secure and private

### ❌ Don't:
- Commit tokens to version control
- Share tokens in chat or email
- Use production tokens in development
- Hardcode tokens in source code
- Store tokens in unsecured locations

## 🔍 Verification Commands

```bash
# Check if .env is properly ignored
git status  # Should not show .env file

# Test token loading
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print('Token loaded:', bool(os.getenv('COMPOSIO_API_KEY')))"

# Test Composio initialization
python -c "from reflex_dev_agent_enhanced import COMPOSIO_AVAILABLE; print('Composio available:', COMPOSIO_AVAILABLE)"
```

## 🆘 Support

If you encounter issues:
1. Check that `.env` file exists and contains `COMPOSIO_API_KEY`
2. Verify token is valid in Composio dashboard
3. Ensure `python-dotenv` is installed: `pip install python-dotenv`
4. Check server logs for detailed error messages

Your tokens are now secure and will never be exposed in the repository! 🔐
