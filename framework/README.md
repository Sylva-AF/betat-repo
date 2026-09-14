# betat-community

Reference community framework for Betat — provenance of human-originated content. Anyone can run a Betat community on their own server; this package is the reference implementation.

## Quickstart

```bash
pip install betat-community
betat init
python manage.py createsuperuser
betat start
```

`betat init` walks you through community setup (domain check, standards declaration, authentication method) and runs migrations automatically. `betat start` serves the site at `http://127.0.0.1:8000` — it's a thin shortcut for `python manage.py runserver`, so either command works identically; use whichever you find easier to remember.

Full command reference: [framework-cli.md](https://betat.org/framework-cli.html) · API reference: [framework-api.md](https://betat.org/framework-api.html) · going to production (PostgreSQL): [framework-production.md](https://betat.org/framework-production.html)

## Developing this package

Install from the repo root:

```
pip install -e "./framework[dev]"
```

Build detail lives in [BLUEPRINT.md](BLUEPRINT.md); the build plan is [TODO.md](TODO.md).
