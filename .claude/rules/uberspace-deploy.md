---
paths:
  - "deploy/**"
  - ".github/workflows/**"
---

# Uberspace deployment

- Apps must bind `0.0.0.0`. Each Uberspace has its own network namespace and the
  frontend proxies in over a veth interface, so `127.0.0.1`/`localhost`/`::1`
  return 502. https://u8manual.uberspace.de/web_backends/
- Check u8manual.uberspace.de before changing hosting config.
- Units live in `deploy/systemd/` and are installed by the deploy step. Don't
  hand-edit units over SSH.
- gunicorn keeps `--no-control-socket` (benoitc/gunicorn#3509).
