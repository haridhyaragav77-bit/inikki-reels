# Security

This repository is public so its automation can run for free. It holds no keys: they live only in GitHub Secrets.

**Found a problem?** Please do not open a public issue. Use GitHub's private report: the **Security** tab of this repository → **Report a vulnerability**.

How the agent protects itself is in `AGENT.md` section 21 (the Guard): masking of keys and emails in everything printed or saved, a key check on every push and commit, commands accepted only from the owner's own Drive account, jobs that give nothing to pull requests from outside, and a daily look-around that holds posting on a clear sign of a break-in.

What the owner does when something leaks is in `GUIDE.md` section 12.
