---
name: halo-deploy
description: Deploy preview/dev only. Capture URL. Live probe REQUIRED before any human-facing message. Never production without human.
---

# Halo Deploy

1. Run project deploy command from STACK / package scripts (preview flags only).  
2. Parse URL from output.  
3. `python3 $HALO_SYS/python/halo_probe.py --url "$URL" --json`  
4. **If fail** → fix or escalate; **zero** human notification with that URL.  
5. **If pass** → write `.halo/evidence/deploy-ok-Sxxx.json` + optional smoke; then notify:

```
Demo ready (probed live): $URL
```

Production promote = human only.
