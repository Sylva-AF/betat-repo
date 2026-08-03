# TODO 09 — Discoverability: announce & export

> Status: not started
> Blueprint: [§9](../BLUEPRINT.md) · Spec: COMMUNITY_FRAMEWORK.md → "Discoverability commands"
> Depends on: 05, 06 · Blocks: nothing

## Goal
Two push-side CLI commands as the accessibility valve for intermittent hosts — while pull-crawling stays primary and NO crawler ships in this package.

## Tasks
- [ ] `betat announce` — POST to registry/reference index: "new records, crawl me now"; optional auto-run on accept
- [ ] `betat export` — signed, integrity-verifiable dump of all records, submittable by any means
- [ ] Export format: every record's `record_id` recomputes and matches
- [ ] Confirm no crawler is introduced anywhere

## Acceptance criteria
- [ ] `export` output validates (all record_ids recompute)
- [ ] `announce` posts correct payload (registry mockable in tests)
- [ ] no crawler exists in the package

## Security notes
- Export signature covers record content; a tampered export fails verification
- `announce` sends pointers/metadata only, never content

## Out of scope
- Building/running any index or crawler (index operators' job; betat main has its own)
