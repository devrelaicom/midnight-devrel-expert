# Registering a note in its DynamicList component

Every note prepends a release object to
`src/components/DynamicList<Item>.js` and demotes the previous `LATEST` to
`SUPPORTED`. This is scripted — do not hand-edit:

`python3 -m scripts.register_release <path-to-DynamicList.js> '<rel-json>'`

`rel-json` shape:

```json
{
  "version": "4.1.1",
  "status": "LATEST",
  "date": "2 June 2026",
  "summary": "<one line, mirrors High-level summary>",
  "details": ["<mirrors Summary of updates bullets>"],
  "artifacts": [{ "name": "NPM Package", "url": "https://www.npmjs.com/search?q=midnight-ntwrk" }],
  "link": "/relnotes/<dir-basename>/<file_prefix>-<version-dashed>"
}
```

The script prepends the object and rewrites the prior first `LATEST` to
`SUPPORTED`, so exactly one `LATEST` remains.
