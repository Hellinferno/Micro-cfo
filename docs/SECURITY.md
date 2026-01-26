# 🔒 Security Guidelines for MicroCFO MCP Server

## ⚠️ CRITICAL: API Key Security

**NEVER commit API keys to version control!**

This project requires API keys for AI services (Gemini, OpenRouter). All API keys must be stored securely using environment variables or `.env` files.

## 🛡️ Secure Configuration Methods

### Method 1: Environment Variables (Recommended for Production)

#### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY="your_gemini_api_key_here"
$env:OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

#### Windows (CMD)
```cmd
set GEMINI_API_KEY=your_gemini_api_key_here
set OPENROUTER_API_KEY=your_openrouter_api_key_here
```

#### Unix/Linux/Mac
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
export OPENROUTER_API_KEY="your_openrouter_api_key_here"
```

### Method 2: .env File (Recommended for Development)

1. **Copy the example file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your actual keys:**
   ```bash
   GEMINI_API_KEY=your_actual_gemini_key_here
   OPENROUTER_API_KEY=your_actual_openrouter_key_here
   ```

3. **Load environment variables (optional):**
   ```python
   # Install python-dotenv
   pip install python-dotenv
   
   # In your script
   from dotenv import load_dotenv
   load_dotenv()
   ```

## 🔑 Getting API Keys

### Google Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key (starts with `AIzaSy...`)

### OpenRouter API Key
1. Visit: https://openrouter.ai/keys
2. Sign up or log in
3. Create a new API key
4. Copy the key (starts with `sk-or-...`)

## 🚫 What NOT to Do

### ❌ NEVER do this:
```python
# BAD - Hardcoded API key in source code
os.environ['GEMINI_API_KEY'] = 'AIzaSyBYF5rjxv8YzTZ5UJciZ_c3PHzOaKNUm7g'
```

### ✅ ALWAYS do this:
```python
# GOOD - Load from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set")
```

## 📁 Files Protected by .gitignore

The following files are automatically excluded from git:

- `.env` - Your actual API keys
- `.env.local` - Local environment overrides
- `*.key` - Any key files
- `*.pem` - Certificate files
- `secrets.json` - Secret configuration files
- `credentials.json` - Credential files

## 🔍 Checking for Exposed Keys

Before committing, always check:

```bash
# Search for potential API keys in staged files
git diff --cached | grep -i "api_key\|apikey\|secret\|password"

# Check git history for exposed keys
git log -p | grep -i "AIzaSy\|sk-or-"
```

## 🚨 If You Accidentally Commit an API Key

1. **Immediately revoke the key:**
   - Gemini: https://makersuite.google.com/app/apikey
   - OpenRouter: https://openrouter.ai/keys

2. **Generate a new key**

3. **Remove from git history:**
   ```bash
   # Use git filter-branch or BFG Repo-Cleaner
   # See: https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository
   ```

4. **Force push to remote:**
   ```bash
   git push --force
   ```

## 🔐 Best Practices

1. **Use different keys for development and production**
2. **Rotate keys regularly** (every 90 days recommended)
3. **Set up key expiration** where supported
4. **Monitor API usage** for unusual activity
5. **Use least privilege** - only grant necessary permissions
6. **Never share keys** via email, chat, or screenshots
7. **Use secrets management** for production (AWS Secrets Manager, Azure Key Vault, etc.)

## 🛠️ Testing Without Real Keys

The MicroCFO server includes fallback modes that work without API keys:

```python
# Agent A will use mock data if no API key is set
result = scan_invoice_document('test.jpg', use_mock=True)

# Agent D uses template-based generation as fallback
result = generate_negotiation_draft(...)  # Works without API keys
```

## 📞 Security Contact

If you discover a security vulnerability, please:
1. **DO NOT** open a public issue
2. Email the maintainer directly
3. Include details of the vulnerability
4. Allow time for a fix before public disclosure

## ✅ Security Checklist

Before making your repository public:

- [ ] All API keys removed from source code
- [ ] `.env` file added to `.gitignore`
- [ ] `.env.example` created with placeholder values
- [ ] `SECURITY.md` reviewed and understood
- [ ] Git history checked for exposed keys
- [ ] All team members briefed on security practices
- [ ] API key rotation schedule established

## 📚 Additional Resources

- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [GitHub Secret Scanning](https://docs.github.com/en/code-security/secret-scanning)
- [12-Factor App: Config](https://12factor.net/config)

---

**Remember: Security is everyone's responsibility. When in doubt, ask!** 🔒
