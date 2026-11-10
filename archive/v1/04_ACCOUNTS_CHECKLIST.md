# Accounts checklist

These are the accounts the system needs. **Never share passwords with Claude.** Keys go straight into GitHub Secrets, where the system reads them and nobody can see them again. Expect about 1–2 hours in total. The build session walks you through any step you get stuck on.

| # | Account | Cost | You have it? | What it's for |
| --- | --- | --- | --- | --- |
| 1 | Claude Pro | Already paying | Yes | The brain (scheduled tasks), the Workshop, the Control Room |
| 2 | GitHub (free) | Free | ? | The code, plans and the free cloud runners that render and post |
| 3 | OpenAI Platform (API) | ₹500 a month cap | ? | Images only |
| 4 | Meta for Developers app | Free | ? | Automatic posting and stats for @inikki_reels |
| 5 | Google Drive folder + Google Cloud service account | Free | Drive yes | Media storage and the Control Room's live view |
| 6 | Your laptop with Python 3.9+ | Free | Yes | Voice backup only |

---

## 1. Claude Pro (you have this)
- [ ] At claude.ai/code, connect your GitHub account when asked.
- [ ] Install the **Claude GitHub App** on the `inikki-reels` repository (the build session gives you the link).
- [ ] Keep the Google Drive connector connected (Settings → Connectors).

## 2. GitHub
- [ ] Create a free account at github.com (or use your own).
- [ ] Create a **private** repository named `inikki-reels`.
- [ ] Upload this kickstart folder's files into it (the build session moves them to the right places).
- [ ] Later, add the keys listed below under **Settings → Secrets and variables → Actions**.

Note: free private repositories get a monthly allowance of runner minutes. The build checks usage, and spec section 21 has the option to go public later.

## 3. OpenAI Platform (not ChatGPT Plus)
- [ ] Sign up at **platform.openai.com** and add a payment method.
- [ ] Buy **$5 of credit** (the minimum, about ₹440–450). **Turn auto-reload off.**
- [ ] Under Limits, set a monthly budget of **$6**, as a second safety net.
- [ ] Create an API key named `inikki-reels` → save it as GitHub Secret `OPENAI_API_KEY`.
- [ ] Top up $5 by hand when the Control Room's Budget card says so (about once a month).

## 4. Instagram posting (Meta for Developers)
- [ ] Your @inikki_reels is already a Creator account.
- [ ] Log in at **developers.facebook.com** with your Facebook account and create an app (type: Business). Add the product **Instagram API with Instagram Login**.
- [ ] Add @inikki_reels as an Instagram tester in the app, and accept the invite in the Instagram app.
- [ ] Generate a token for @inikki_reels with these permissions: `instagram_business_basic`, `instagram_business_content_publish`, `instagram_business_manage_insights`, `instagram_business_manage_comments`.
- [ ] Save as GitHub Secrets: `IG_USER_ID`, `IG_ACCESS_TOKEN` (long-lived), `META_APP_ID`, `META_APP_SECRET`.
- The app can stay in development mode, because it only posts to your own account.

## 5. Google Drive and service account
- [ ] Create a Drive folder named **iNiKKi Reels**. Inside it, create `reference-reels/` and upload your sample reels, and `meme-bank/` and upload your meme clips and recordings.
- [ ] At console.cloud.google.com: create a project → enable the **Google Drive API** → create a **service account** → create a JSON key.
- [ ] Share the **iNiKKi Reels** folder with the service account's email (Editor).
- [ ] Save as GitHub Secrets: `GDRIVE_SERVICE_ACCOUNT_JSON` (the whole JSON) and `GDRIVE_ROOT_FOLDER_ID` (the ID in the folder's link).

## 6. Laptop (voice backup only)
- [ ] Python 3.9 or newer installed. `voice_tool.py` installs everything else itself.
- [ ] Only needed if the cloud voice test fails. The build session gives you a one-click helper.

## 7. On the Instagram app (2 minutes)
- [ ] Change the display name from **iNiKKi_PLAN** to **iNiKKi Reels**.
- [ ] Update the bio. Suggested: "Tamil cinema, broken down. Daily breakdowns, updates and Guess the Movie."

---

## Secrets summary (GitHub → Settings → Secrets → Actions)

| Name | From |
| --- | --- |
| `OPENAI_API_KEY` | OpenAI Platform |
| `IG_USER_ID` | Meta app |
| `IG_ACCESS_TOKEN` | Meta app (long-lived) |
| `META_APP_ID` | Meta app |
| `META_APP_SECRET` | Meta app |
| `GDRIVE_SERVICE_ACCOUNT_JSON` | Google Cloud |
| `GDRIVE_ROOT_FOLDER_ID` | Drive folder link |
| `BRAIN_FIRE_URL`, `BRAIN_FIRE_TOKEN` | The Breaking run's API trigger (created in Phase 3) |
