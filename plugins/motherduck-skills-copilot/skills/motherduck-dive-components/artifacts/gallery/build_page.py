"""Build gallery/index.html: the component gallery as a standalone web page.

    python3 gallery/build_page.py

Same code as the gallery Dive, compiled with esbuild. React, Recharts, d3 and
lucide-react load as pinned UMD builds from public CDNs, Tailwind from its play CDN,
and @motherduck/react-sql-query is replaced by a small stand-in (dive state becomes
React state). Needs node (npx downloads esbuild once).
"""

import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).parent
KIT = HERE.parent
sys.path.insert(0, str(KIT))
import assemble  # noqa: E402

SHIMS = {
    "react": "module.exports = window.React;",
    "react-dom": "module.exports = window.ReactDOM;",
    "recharts": "module.exports = window.Recharts;",
    "d3": "module.exports = window.d3;",
    "lucide-react": "module.exports = window.LucideReact;",
    "@motherduck/react-sql-query": """
const React = window.React;
const dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
// Dive state becomes React state; the first theme follows the viewer's colour scheme.
export function useDiveState(key, initial) {
\treturn React.useState(key === 'base' && dark && initial === 'swiss' ? 'night' : initial);
}
export function useSQLQuery() { return { data: [], isLoading: false, isError: false, refetch() {} }; }
export const useRunFlight = () => ({ run() {}, isPending: false });
export const useFlightRun = () => ({});
export const useExport = () => ({ exportQuery: async () => {} });
""",
}

LIBS = [
    "https://cdnjs.cloudflare.com/ajax/libs/react/18.3.1/umd/react.production.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/react-dom/18.3.1/umd/react-dom.production.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/prop-types/15.8.1/prop-types.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/recharts/2.12.7/Recharts.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/d3/7.9.0/d3.min.js",
    "https://unpkg.com/lucide-react@0.454.0/dist/umd/lucide-react.min.js",
    "https://cdn.tailwindcss.com/3.4.17",
]

PAGE = """<title>Dive Components</title>
<meta name="claude:viewport-fit-sides" content="cover">
<style>
/* Layout: one intro band over the gallery, which brings its own themes. */
:root { --bg: #ffffff; --fg: #111111; --muted: #6b6b6b; --rule: #111111; --chip: #f3f3f3; --accent: #e4002b; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) { --bg: #0e1116; --fg: #e6e8eb; --muted: #8b949e; --rule: #e6e8eb; --chip: #1c222b; --accent: #ff5c6f; color-scheme: dark } }
:root[data-theme="dark"] { --bg: #0e1116; --fg: #e6e8eb; --muted: #8b949e; --rule: #e6e8eb; --chip: #1c222b; --accent: #ff5c6f; color-scheme: dark }
body { background: var(--bg); color: var(--fg); margin: 0; overflow-x: hidden; }
.intro { padding-block: 20px 16px; padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); font: 14px/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif; }
.intro-inner { max-width: 1296px; margin: 0 auto; display: grid; gap: 10px; border-bottom: 1px solid var(--rule); padding-bottom: 16px; }
.intro-top { display: flex; flex-wrap: wrap; align-items: baseline; gap: 6px 14px; }
.intro b { font-weight: 700; }
.intro .tag { font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent); font-weight: 700; }
.intro p { margin: 0; color: var(--muted); max-width: 78ch; }
.intro code { font: 12px ui-monospace, Menlo, monospace; background: var(--chip); padding: 1px 5px; color: var(--fg); }
.intro a { color: var(--fg); text-underline-offset: 3px; }
.intro a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }
#gallery { min-height: 60vh; }
</style>
<header class="intro">
  <div class="intro-inner">
    <div class="intro-top">
      <span class="tag">Example page</span>
      <b>motherduck-dive-components</b>
      <span style="color:var(--muted)">the component kit for MotherDuck Dives</span>
    </div>
    <p>Every default component on sample data. Switch a block between the renderers that can show its data, open a block's data with the <code>&lt;/&gt;</code> button, change the theme, or try a brand colour. This is the gallery Dive's code compiled to a web page; in a Dive the same blocks are built from live SQL with <code>useSQLQuery</code>.</p>
  </div>
</header>
<div id="gallery"></div>
"""


def main():
    app = (HERE / "app.tsx").read_text()
    source = assemble.assemble(app, extras=[KIT / "examples" / "funnel.tsx"])
    with tempfile.TemporaryDirectory() as tmp:
        t = pathlib.Path(tmp)
        (t / "gallery.tsx").write_text(source)
        aliases = []
        for mod, code in SHIMS.items():
            f = t / (mod.replace("/", "_").replace("@", "") + ".js")
            f.write_text(code)
            aliases.append(f"--alias:{mod}=./{f.name}")
        (t / "entry.tsx").write_text("import Gallery from './gallery.tsx';\nwindow.ReactDOM.createRoot(document.getElementById('gallery')).render(window.React.createElement(Gallery));\n")
        subprocess.run(
            ["npx", "-y", "esbuild@0.24.0", "entry.tsx", "--bundle", "--minify", "--format=iife", "--target=es2019",
             "--jsx-factory=React.createElement", "--jsx-fragment=React.Fragment", "--outfile=bundle.js", *aliases],
            cwd=t, check=True, capture_output=True,
        )
        bundle = (t / "bundle.js").read_text().replace("</script", "<\\/script")
    # lucide-react's UMD build reads the lowercase global `react`.
    scripts = "\n".join(f'<script src="{u}"></script>' + ("\n<script>window.react = window.React;</script>" if "react-dom" in u else "") for u in LIBS)
    html = PAGE + scripts + f"\n<script>\n{bundle}\n</script>\n"
    out = HERE / "index.html"
    out.write_text(html)
    print(f"{out}: {len(html):,} chars")


if __name__ == "__main__":
    main()
