---
layout: default
title: Start a community
nav_order: 6
parent: For Everyone
---

# Start a community

Starting a Betat community means creating a permanent, verified record
for a type of human knowledge that your community originates. You
decide what your community verifies, how members authenticate, and
what standards submissions must meet — within the Betat protocol floor
that every community shares.

Once your community is running, members can enroll, submit content,
and receive provenance records. Anyone in the world can read those
records, free, forever.

---

## Before you begin

Starting a community requires one person who can set up and run a
server, or is willing to use a cloud hosting platform. The Betat
framework is software that runs on a server — it is not a hosted
service that betat.org provides (though hosted options are in the
roadmap). If your community does not have a technical person, see
the options below.

**What you will need:**

- A domain name your community controls (e.g. `archive.yourcommunity.org`)
  — this becomes your community's permanent unique identity
- A server running Linux, or a cloud hosting account
- Python 3.11 or later on that server
- A clear sense of what type of knowledge your community will verify

**What you will decide during setup:**

- Your community's name and the knowledge domain it covers
- The type of content it verifies (scientific observation, oral knowledge,
  creative work, academic writing, or another type)
- How members authenticate — peer vouching, cryptographic keys, or
  institutional identity
- The URI where your records will be published

---

## Installation paths

Choose the path that matches your situation.

### Option 1 — Install with pip (for technical operators)

If you have a Linux server and Python 3.11:

```bash
pip install betat-community
betat init
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`betat init` walks you through community setup in your terminal.
`manage.py runserver` starts the framework. Visit `localhost:8000`
in your browser to confirm it is running, then configure your domain
and a production server for public access.

Two standard Django commands worth knowing as you go:

```bash
python manage.py check --deploy   # production-readiness checks (SECRET_KEY, DEBUG, HTTPS)
python manage.py shell            # interactive Python shell with the framework loaded
```

Full reference: [Framework CLI](framework-cli.html)

### Option 2 — Browser setup wizard (for less technical operators)

After `pip install betat-community` and `python manage.py runserver`,
visit your server in a browser. If the community is not yet configured,
you will see the Betat installation screen. Click **Begin setup** to
walk through configuration in the browser — no terminal commands after
the initial install.

### Option 3 — One-click cloud deploy (coming soon)

A "Deploy to Render" button is coming to this page. It will let you
deploy a Betat community instance to a cloud server with a single
click — no terminal, no server management. You will need a free account
on the hosting platform and a domain name.

Watch the [GitHub repository](https://github.com/Sylva-AF/betat-repo)
for this when it launches.

### Option 4 — Ask for help

If none of the above fits your community's situation, reach out.
During the early period of Betat's launch, the founder is available
to remotely assist communities setting up their first instance as a
volunteer service.

Contact: open a discussion on
[GitHub](https://github.com/Sylva-AF/betat-repo/discussions) and
describe your community and what you are trying to archive.

---

## What your community commits to

When you start a Betat community, your community makes permanent
commitments through the protocol:

**Your community id never changes.** The domain you register becomes
your community's identity forever — even if you later move hosting
or change the domain's website, the community id is fixed.

**Your standards can only strengthen.** The HI standard you set at
launch is the floor. Future decisions can add requirements; they
cannot remove them. This protects the meaning of records already
issued.

**Records are permanent.** Every provenance record your community
issues is append-only — it cannot be deleted or modified. Corrections
and disputes are new records, not erasures.

These commitments exist because they are what makes the HI tag
trustworthy. A provenance record from a community that can quietly
change or delete its records is not a record worth trusting.

---

## After setup

Once your community is running:

- Enroll your first verifiers (staff users via `manage.py createsuperuser`)
- Invite your first Provenanciers to enroll
- Submit and verify your first provenance record
- Optionally, register with the Betat registry when it launches
  so other communities and readers can discover yours

---

## Questions

Open a discussion on [GitHub](https://github.com/Sylva-AF/betat-repo/discussions)
or read the full technical documentation in [For Builders](for-builders.html).

---

*Betat. The human record, for the other person.*
