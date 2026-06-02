# English Buddy — Setup Guide
## CI/CD, Environments & API Key Protection

---

## Step 1 — Create 3 branches in Git

```bash
# You are on main branch already
git checkout -b dev
git push -u origin dev

git checkout -b staging
git push -u origin staging

git checkout main
```

---

## Step 2 — Protect main branch on GitHub (FREE)

1. Go to github.com → your repo → **Settings → Branches**
2. Click **Add branch protection rule**
3. Branch name pattern: `main`
4. Tick these (all free):
   - ✅ Require a pull request before merging
   - ✅ Require approvals: 1
   - ✅ Dismiss stale pull request approvals
   - ✅ Do not allow bypassing the above settings
5. Click **Save changes**

Now nobody (including you) can push directly to main.
Only PRs from staging → main are allowed.

---

## Step 3 — Create Production environment with approval (FREE)

1. Go to repo → **Settings → Environments**
2. Click **New environment** → name it `production`
3. Tick **Required reviewers** → add yourself
4. Click **Save protection rules**

Now production deploys require you to manually click Approve.
Zero cost — this is a free GitHub feature.

---

## Step 4 — Set up Railway (3 services = $5/month total)

### Create 3 Railway services:

Go to railway.app → New Project → Deploy from GitHub

**Service 1 — Dev**
- Connect repo → select `dev` branch
- Service name: `englishbuddy-dev`
- Add environment variables (see Step 5)
- Add custom domain: `dev.englishbuddy.live`

**Service 2 — Staging**
- Connect repo → select `staging` branch
- Service name: `englishbuddy-staging`
- Add environment variables (see Step 5)
- Add custom domain: `stg.englishbuddy.live`

**Service 3 — Production**
- Connect repo → select `main` branch
- Service name: `englishbuddy-prod`
- Add environment variables (see Step 5)
- Add custom domain: `englishbuddy.live`

---

## Step 5 — API Keys per environment (CRITICAL)

### Never put API keys in code or Git. Railway env vars only.

**Dev service env vars** (test keys, low limits):
```
ANTHROPIC_API_KEY = sk-ant-your-TEST-key
PORT              = 8765
ENVIRONMENT       = dev
```

**Staging service env vars** (test keys + Stripe test mode):
```
ANTHROPIC_API_KEY    = sk-ant-your-TEST-key
STRIPE_SECRET        = sk_test_xxxx          ← test mode key
STRIPE_WEBHOOK_SECRET= whsec_test_xxxx
PORT                 = 8765
ENVIRONMENT          = staging
```

**Production service env vars** (real keys):
```
ANTHROPIC_API_KEY    = sk-ant-your-REAL-key
STRIPE_SECRET        = sk_live_xxxx          ← live mode key
STRIPE_WEBHOOK_SECRET= whsec_live_xxxx
PORT                 = 8765
ENVIRONMENT          = production
```

### Set Anthropic spend limits:
- Go to console.anthropic.com → Settings → Limits
- Dev key: $5/month hard limit
- Staging key: $10/month hard limit
- Production key: $50/month hard limit (increase as you grow)

---

## Step 6 — Point DNS to Railway (Namecheap)

For each subdomain, add a CNAME record in Namecheap:
Dashboard → Domain List → englishbuddy.live → Manage → Advanced DNS

| Type  | Host | Value                          |
|-------|------|--------------------------------|
| CNAME | dev  | your-dev-service.railway.app   |
| CNAME | stg  | your-stg-service.railway.app   |
| CNAME | @    | your-prod-service.railway.app  |

Railway gives you the exact `.railway.app` URL in
Settings → Domains → Custom Domain setup.

---

## Step 7 — Daily development workflow

```bash
# Morning — start work
git checkout dev
git pull

# Make changes to frontend/english_buddy.html or backend/server.py
# ... code, code, code ...

# Push to dev (auto-deploys to dev.englishbuddy.live)
git add .
git commit -m "Add speaking score card UI"
git push

# Test on dev.englishbuddy.live in Chrome

# Ready to test with others? Merge to staging
git checkout staging
git merge dev
git push
# GitHub Actions runs checks → deploys to stg.englishbuddy.live

# Happy with staging? Promote to production
# On GitHub: open PR from staging → main
# Review the PR → Approve → Merge
# Then go to Actions → Run workflow → choose production
# Click Approve when prompted
# Deployed to englishbuddy.live in ~90 seconds
```

---

## Free tier limits — will you hit them?

| Service          | Free limit          | Your usage        | Safe? |
|------------------|--------------------|--------------------|-------|
| GitHub Actions   | 2,000 min/month    | ~3 min/deploy      | ✅ Yes |
| GitHub repos     | Unlimited private  | 1 repo             | ✅ Yes |
| GitHub branches  | Unlimited          | 3 branches         | ✅ Yes |
| Branch protection| Free feature       | main branch        | ✅ Yes |
| Environments     | Free feature       | 1 (production)     | ✅ Yes |
| Railway Hobby    | $5/month           | 3 services         | ✅ $5  |
| Namecheap DNS    | Free with domain   | 3 CNAME records    | ✅ Yes |
| Railway SSL/TLS  | Free               | All 3 domains      | ✅ Yes |

**Total monthly cost: $5.00**

---

## Rollback if production breaks

```bash
# Option 1: Revert the last commit (triggers auto-redeploy)
git checkout main
git revert HEAD
git push
# Railway redeploys in ~90 seconds

# Option 2: Railway dashboard
# railway.app → your prod service → Deployments
# Click any previous deploy → Redeploy
# Takes ~60 seconds
```

---

## What NOT to do

- ❌ Never `git push origin main` directly — use PRs only
- ❌ Never put API keys in any .html, .py, or .js file
- ❌ Never commit .env file (it's in .gitignore)
- ❌ Never use your production Anthropic key in dev/staging
- ❌ Never use Stripe live keys in dev/staging
