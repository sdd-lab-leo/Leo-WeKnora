# Apply product spec + prototype into `quarry-kb`

This cloud agent can write to `Leo-WeKnora` but currently gets **403** pushing to `sdd-lab-leo/quarry-kb`. Use one of the options below with an account that has write access to `quarry-kb`.

## Option A — copy from this draft (simplest)

```sh
git clone https://github.com/sdd-lab-leo/quarry-kb.git
cd quarry-kb
git checkout -b cursor/import-product-spec-prototype-b2aa

git clone --depth 1 -b cursor/quarry-kb-spec-prototype-b2aa \
  https://github.com/sdd-lab-leo/Leo-WeKnora.git /tmp/Leo-WeKnora

mkdir -p docs
cp -R /tmp/Leo-WeKnora/quarry-kb-draft/docs/. docs/
# optional: refresh README entry points from the patch branch if desired

git add docs/01-requirements/quarry-kb-product-spec-v0.1.md docs/prototypes/
git rm -f docs/01-requirements/.gitkeep 2>/dev/null || true
git commit -m "docs: import v0.1.5 product spec and HTML prototype"
git push -u origin cursor/import-product-spec-prototype-b2aa
gh pr create --base main --title "docs: import v0.1.5 product spec and HTML prototype" --body "Imports requirements-layer product spec and static HTML prototype from Leo-WeKnora draft."
```

## Option B — apply the ready patch

From a clean `quarry-kb` checkout on `main`:

```sh
git checkout -b cursor/import-product-spec-prototype-b2aa
git am /path/to/Leo-WeKnora/quarry-kb-draft/export/quarry-kb-import-v0.1.5.patch
git push -u origin cursor/import-product-spec-prototype-b2aa
```

The patch includes:
- `docs/01-requirements/quarry-kb-product-spec-v0.1.md`
- `docs/prototypes/index.html`
- `docs/prototypes/README.md`
- README links + removal of `docs/01-requirements/.gitkeep`
