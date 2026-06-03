# Mortgage Rates - One-Time Setup

Three files to deal with. Everything below is free and only needs to be done once.

You'll need: a GitHub account (free at https://github.com/signup) and your FRED API key (you already have one: `0da8654f0418ac90ddeb257ff60f3b4e`).

---

## 1. Create the GitHub repo

1. Go to https://github.com/new
2. **Repository name:** `mortgage-rates` (or anything you want, just remember it)
3. Set it to **Public**. (jsDelivr only serves public repos.)
4. Check **Add a README file**.
5. Click **Create repository**.

## 2. Add your FRED key as a secret

1. In the new repo, go to **Settings -> Secrets and variables -> Actions**.
2. Click **New repository secret**.
3. **Name:** `FRED_API_KEY`
4. **Value:** `0da8654f0418ac90ddeb257ff60f3b4e`
5. Click **Add secret**.

## 3. Add the workflow file

1. In the repo, click **Add file -> Create new file**.
2. **Filename:** `.github/workflows/update-rates.yml` (yes, type the whole path - GitHub auto-creates the folders)
3. Paste the contents of `update-rates.yml` from this folder.
4. Click **Commit changes**.

## 4. Add the updater script

1. Navigate to the **root of the repo** (click the repo name at the top of the page to get back there - you don't want to be inside `.github/workflows/` for this step).
2. **Add file -> Create new file**.
3. **Filename:** `update-rates.js` (just that, no folder prefix - it lives at the repo root, next to README.md, NOT inside `.github/workflows/`).
4. Paste the contents of `update-rates.js` from this folder.
5. Click **Commit changes**.

After this step, your repo should look like:

```
your-repo/
  README.md
  update-rates.js              <- here
  .github/
    workflows/
      update-rates.yml         <- from step 3
```

## 5. Run the workflow once to seed rates.json

1. Go to the **Actions** tab in the repo.
2. Click **Update Mortgage Rates** in the left sidebar.
3. Click **Run workflow -> Run workflow**.
4. Wait ~30 seconds. When the run shows a green check, refresh the repo. You should now see a `rates.json` file.

From now on it runs automatically every Thursday afternoon.

## 6. Update marketrates.html with your repo URL

In `marketrates.html`, find this line near the top of the `<script>` block:

```js
const RATES_URL = "https://cdn.jsdelivr.net/gh/YOUR_GH_USERNAME/YOUR_REPO_NAME@main/rates.json";
```

Replace `YOUR_GH_USERNAME` with your GitHub username, and `YOUR_REPO_NAME` with whatever you named the repo in step 1. Example:

```js
const RATES_URL = "https://cdn.jsdelivr.net/gh/sorianore/mortgage-rates@main/rates.json";
```

Paste the updated HTML into your Realty ONE Group page. Done.

---

## What happens next

- Every Thursday at ~1pm ET, the workflow runs, pulls fresh PMMS rates from FRED, commits `rates.json`.
- Your page reads from jsDelivr's CDN, which picks up the new file automatically within ~10 minutes.
- You do nothing.

## If rates ever stop updating

1. Check the **Actions** tab in your GitHub repo. If the most recent run is red, click it to see what failed.
2. If FRED changed its API or your key got rotated, that's where you'll see it.

## Security note

Your FRED API key lives in GitHub Secrets - it never appears in any committed file or in the page source. Safe.
