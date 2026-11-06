// Bundles the CodeMirror based editor into a single offline file.
// Run: node tools/build_editor.mjs
import { build } from "esbuild";

const OUT = "src/oslab/assets/ui/vendor/editor.bundle.js";

await build({
  entryPoints: ["tools/editor_entry.js"],
  bundle: true,
  format: "esm",
  minify: true,
  target: ["chrome110"],
  outfile: OUT,
  legalComments: "none",
});
console.log("built", OUT);
