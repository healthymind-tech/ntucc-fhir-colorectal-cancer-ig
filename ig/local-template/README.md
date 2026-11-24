# Local template

Inherits `fhir2.base.template#0.1.0` (the only published version) and overrides a
single file:

- `layouts/layout-profile-history.html` — upstream line 14 repeats the page
  heading as an unclosed `<h2 id="root">`. That produced one QA error per
  profile ("more than one top level heading") plus malformed-HTML and
  duplicate-id warnings. The override deletes that line; nothing else differs.

Remove this folder and set `template = fhir2.base.template#<version>` in
`ig.ini` once the upstream template is fixed.
