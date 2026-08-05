# Publication checklist

Before making the repository public:

- [x] Public review target: `chosen8823/sophia-bridge-protocol`.
- [ ] Confirm whether public attribution should name a person, Anchor1 LLC, or
      only the GitHub account. The draft presently names only the account.
- [ ] Confirm GPL-3.0 is the intended license before merging; it is the existing
      repository license. Move to a fresh repository before merge if a different
      license is required.
- [ ] Add a contact address that is safe to publish.
- [ ] Run `python benchmark.py --require-pass` and `python -m unittest -v`.
- [ ] Commit the emitted reference result as `results/reference.json`.
- [ ] Enable issue tracking for reproducibility reports and counterexamples.
- [ ] Submit the public repository with the accelerator applications.

Do not publish private keys, cloud credentials, unpublished personal records,
or claims that exceed what the benchmark measures.
