# Self-hosted fonts (owner: C)

Copied unchanged from npm `@fontsource-variable/space-grotesk@5.3.0` and `@fontsource-variable/manrope@5.3.0`
(Latin and Latin-ext variable WOFF2 subsets). Licence: SIL Open Font License 1.1 (files `*-OFL.txt`).
Served from `/fonts/`, preloaded in `web/index.html`, declared in `web/src/styles.css`. Self-hosted rather than
imported from node_modules so the two Latin files can be preloaded with stable URLs (they arrive before the
app first renders, so text does not shift when they swap in).
