# Vendored browser dependencies

Minified ES module builds copied from npm, so the dashboard runs with no install or build step. `index.html` maps the bare specifiers (`preact`, `preact/hooks`, `htm`, `marked`) to these files with an import map. Licences are in `LICENSES.txt`.

Changes from upstream:

- The trailing `//# sourceMappingURL=` line is removed, because the `.map` files aren't shipped.
- The minified files (`preact.mjs`, `hooks.mjs`, `htm.mjs`) gain a first-line comment pointing here.

The hashes below are of the npm file without its source map line, so they exclude the pointer comment.

## Files

- `preact.mjs`: preact 11.0.0, npm `dist/preact.mjs`
  - Readable source: https://github.com/preactjs/preact/tree/11.0.0/src
  - sha256 `0dac8cbd2dfcd285ff87c58abcf28e4561b446127c6d644a4338042bb4214652`
- `hooks.mjs`: preact 11.0.0, npm `hooks/dist/hooks.mjs`. Imports `preact`, resolved by the import map.
  - Readable source: https://github.com/preactjs/preact/tree/11.0.0/hooks/src
  - sha256 `d8c209c75f5b0eb60b5d89dc050e8eb8f9cabb484eaf2e51ea144700142a1f64`
- `htm.mjs`: htm 3.1.1, npm `dist/htm.mjs`
  - Readable source: https://github.com/developit/htm/tree/3.1.1/src
  - sha256 `ab33dd3f38059b9be4d5f5350128eefb2356639c4e0bbe9d9e8b3ba75847e9e4`
- `marked.esm.js`: marked 18.0.14, npm `lib/marked.esm.js`
  - Readable source: https://github.com/markedjs/marked/tree/v18.0.14/src
  - sha256 `0eab1f03c00471183d1b79febacfdca34e3f4bf506d25720883c682780f9e5e1`

## Verify or update

Fetch the npm file, drop the source map line, and compare with the vendored file minus its pointer comment (skip the `tail` for `marked.esm.js`, which has none).

```sh
curl -sL https://unpkg.com/preact@11.0.0/hooks/dist/hooks.mjs | sed '/^\/\/# sourceMappingURL=/d' | shasum -a 256
tail -n +2 hooks.mjs | shasum -a 256
```

To update, bump the version in the URL and write the stripped result over the vendored file. Re-add the pointer comment to minified files, then refresh the version, path and hash above and the matching section of `LICENSES.txt`.
