# Agent instructions

Start with START_HERE.md and agent/START_HERE.md. This is an evidence-linked quick reference, not an automatic answer service.

Read docs/competition.md before preparing accounts or study tasks. Apply notices only to their stated competition stage and specific resource; do not extend an exclusion to the whole module. Current notices override conflicting historical operational guidance. Original source evidence and answer verification states remain historical records.

data/curated/ is the sole fact source. Site, Wiki, upload packs and llms-full.txt are compiled by python -m app kb build. Never infer conclusions from raw ASR/OCR. Preserve source IDs, hashes and review provenance. Identical source hashes must not overwrite reviewed fields; changed hashes require draft status and re-review.

Separate question-text review from answer verification. Human-confirmed answers apply only to the original conditions and option text. Candidates and training samples are separate records. New machine-authored material is machine_reviewed, never human_reviewed without the user's confirmation.

First help the user prepare relevant official entries, accounts and institutional access, distinguishing public lookup from account-only functions. When answering a question, prioritize current online evidence from official platforms and original documents. Use this repository to identify platforms, choose search methods and consult historical references, not as a substitute for live verification. Use python -m app kb search when local files are available. Draft and quarantined sources are excluded by default. Validate dynamic values on the original platform. Stop at login, CAPTCHA, institutional authentication and paywalls; wait for the user's authorized session. Explain unavailable access honestly. Do not store credentials or submit competition answers automatically.

Do not publish absolute paths, secrets, guesses or raw media. Future media links belong in data/curated/media.json. Before handoff run python -m app kb build, python -m app kb lint --strict, python -m app.validate_readable and python -m pytest.
