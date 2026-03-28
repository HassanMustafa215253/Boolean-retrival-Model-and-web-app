import html as html_lib
import gradio as gr

# ─────────────────────────────────────────────
# 🔌  PLUG IN YOUR FUNCTION HERE
# ─────────────────────────────────────────────
from Main import search_speeches

SPEECHES_FOLDER = "Speeches/"   # ← change to your folder path




# ─────────────────────────────────────────────
# 🔧  RESULT ADAPTER
# Converts dict[int, str] → list[dict] with doc_id preserved.
# ─────────────────────────────────────────────

SNIPPET_LENGTH = 180  # chars shown in collapsed preview


def normalise_results(raw: dict) -> list[dict]:
    """
    Accepts dict[int, str] (doc_id → text) and returns a
    sorted list of normalised result dicts.
    """
    if not raw:
        return []
    out = []
    for doc_id, text in raw.items():
        if not isinstance(text, str):
            text = str(text)
        out.append({
            "doc_id": int(doc_id),
            "text":   text,
        })
    # Present in ascending doc_id order so the list is stable
    out.sort(key=lambda r: r["doc_id"])
    return out


def make_snippet(text: str, length: int = SNIPPET_LENGTH) -> str:
    flat = text.strip().replace("\n", " ")
    if len(flat) <= length:
        return flat
    return flat[:length].rsplit(" ", 1)[0] + " …"


# ─────────────────────────────────────────────
# 🎨  HTML RENDERER  — expandable <details> cards
# ─────────────────────────────────────────────

CARD_STYLE = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:ital,opsz,wght@0,8..60,300;0,8..60,400;1,8..60,300&display=swap');

  .sw { font-family: 'Source Serif 4', Georgia, serif !important; }

  /* ── result-count bar ── */
  .result-count {
    font-family: 'Playfair Display', serif !important;
    font-size: 0.79rem !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    color: #8a7355 !important;
    border-bottom: 1px solid #d4c4a8 !important;
    padding-bottom: 12px !important;
    margin-bottom: 18px !important;
    display: flex !important;
    align-items: baseline !important;
    flex-wrap: wrap !important;
    gap: 10px !important;
  }

  .rc-summary { flex-shrink: 0 !important; }

  /* pill strip for doc IDs */
  .rc-ids {
    display: flex !important;
    flex-wrap: wrap !important;
    gap: 5px !important;
    align-items: center !important;
  }
  .rc-ids-label {
    font-size: 0.85 rem !important;
    color: #b09878 !important;
    letter-spacing: 0.12em !important;
    margin-right: 2px !important;
  }
  .doc-pill {
    display: inline-block !important;
    background: #ede4d3 !important;
    color: #6b4f2e !important;
    font-size: 0.78 rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    padding: 3px 9px !important;
    border-radius: 99px !important;
    border: 1px solid #d4c4a8 !important;
    font-family: 'Source Serif 4', Georgia, serif !important;
  }

  /* ── card shell ── */
  details.sc {
    background: #fdfaf4 !important;
    border: 1px solid #e0d4bc !important;
    border-left: 4px solid #b5371a !important;
    border-radius: 4px !important;
    margin-bottom: 13px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    overflow: hidden !important;
    transition: box-shadow 0.2s, border-left-color 0.2s !important;
  }
  details.sc:hover { box-shadow: 0 4px 18px rgba(0,0,0,0.10) !important; }
  details.sc[open] { border-left-color: #7a2010 !important; }

  /* ── summary row ── */
  details.sc > summary {
    list-style: none !important;
    cursor: pointer !important;
    padding: 15px 18px !important;
    display: flex !important;
    align-items: flex-start !important;
    gap: 12px !important;
    user-select: none !important;
    -webkit-user-select: none !important;
    background: transparent !important;
  }
  details.sc > summary::-webkit-details-marker { display: none !important; }
  details.sc > summary:focus-visible { outline: 2px solid #b5371a !important; outline-offset: -2px !important; }

  /* ── animated chevron ── */
  .chev {
    flex-shrink: 0 !important;
    margin-top: 4px !important;
    width: 15px !important; height: 15px !important;
    color: #b5371a !important;
    stroke: #b5371a !important;
    transition: transform 0.22s ease !important;
  }
  details.sc[open] .chev { transform: rotate(90deg) !important; }

  .sb { flex: 1 !important; min-width: 0 !important; }

  /* ── card header row: doc-id tag + score badge side by side ── */
  .card-top {
    display: flex !important;
    align-items: center !important;
    gap: 8px !important;
    margin-bottom: 5px !important;
  }

  /* doc-id tag on the card */
  .doc-id-tag {
    display: inline-block !important;
    background: #b5371a !important;
    color: #ffffff !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.06em !important;
    padding: 2px 9px !important;
    border-radius: 2px !important;
    text-transform: uppercase !important;
  }

  /* score badge */
  .badge {
    display: inline-block !important;
    background: #ede4d3 !important;
    color: #6b4f2e !important;
    font-size: 0.71rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.05em !important;
    padding: 2px 7px !important;
    border-radius: 2px !important;
    border: 1px solid #d4c4a8 !important;
  }

  /* ── meta line (date / location) ── */
  .cm {
    font-size: 0.79rem !important;
    color: #8a7355 !important;
    letter-spacing: 0.03em !important;
    margin-bottom: 6px !important;
  }
  .cm span { margin-right: 11px !important; color: #8a7355 !important; }

  /* ── snippet preview ── */
  .cs {
    font-size: 0.92rem !important;
    color: #5a4530 !important;
    line-height: 1.6 !important;
    font-style: italic !important;
    margin: 0 !important;
  }

  /* ── "tap to read" hint ── */
  .hint {
    font-size: 0.70rem !important;
    color: #b09878 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    margin-top: 6px !important;
    transition: opacity 0.15s !important;
  }
  details.sc[open] .hint { opacity: 0 !important; height: 0 !important; overflow: hidden !important; margin: 0 !important; }

  /* ── expanded full text ── */
  .ft {
    padding: 0 18px 20px 45px !important;
    border-top: 1px solid #e8dfc9 !important;
    background: #fdfaf4 !important;
    animation: fs 0.2s ease !important;
  }
  @keyframes fs {
    from { opacity: 0; transform: translateY(-5px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  .ft p {
    font-size: 0.96rem !important;
    color: #2e2010 !important;
    line-height: 1.84 !important;
    white-space: pre-wrap !important;
    word-break: break-word !important;
    font-style: italic !important;
    margin: 14px 0 0 !important;
  }

  /* ── empty state ── */
  .empty {
    text-align: center !important;
    padding: 48px 20px !important;
    color: #8a7355 !important;
    font-style: italic !important;
  }
  .empty strong {
    display: block !important;
    font-family: 'Playfair Display', serif !important;
    font-size: 1.25rem !important;
    color: #3d2f1a !important;
    margin-bottom: 7px !important;
    font-style: normal !important;
  }
</style>
"""

CHEV = (
    '<svg class="chev" viewBox="0 0 20 20" fill="none" stroke="currentColor" '
    'stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">'
    '<polyline points="7 4 13 10 7 16"/></svg>'
)


def render_cards(results: list[dict], query: str) -> str:
    if not results:
        return (
            CARD_STYLE
            + '<div class="sw"><div class="empty">'
            + "<strong>No speeches found</strong>"
            + f"No matches for &ldquo;{html_lib.escape(query)}&rdquo;. Try different keywords."
            + "</div></div>"
        )

    n = len(results)
    doc_ids = [r["doc_id"] for r in results]

    # Build the pill strip of doc IDs
    pills = "".join(f'<span class="doc-pill">#{did}</span>' for did in doc_ids)
    id_strip = (
        f'<span class="rc-ids">'
        f'<span class="rc-ids-label">Doc IDs:</span>'
        f'{pills}'
        f'</span>'
    )

    summary_text = f"{n} speech{'es' if n != 1 else ''} matched &mdash; click a card to read"
    count_bar = (
        f'<div class="result-count">'
        f'<span class="rc-summary">{summary_text}</span>'
        f'{id_strip}'
        f'</div>'
    )

    parts = [CARD_STYLE, '<div class="sw">', count_bar]

    for r in results:
        doc_id  = r["doc_id"]
        snippet = html_lib.escape(make_snippet(r["text"]))
        full    = html_lib.escape(r["text"])

        doc_tag = f'<span class="doc-id-tag">Speech #{doc_id}</span>'

        parts.append(f"""
<details class="sc">
  <summary>
    {CHEV}
    <div class="sb">
      <div class="card-top">{doc_tag}</div>
      <p class="cs">{snippet}</p>
      <p class="hint">Tap to read full speech</p>
    </div>
  </summary>
  <div class="ft"><p>{full}</p></div>
</details>""")

    parts.append("</div>")
    return "\n".join(parts)


# ─────────────────────────────────────────────
# ⚙️  SEARCH HANDLER
# ─────────────────────────────────────────────

def handle_search(query: str):
    query = (query or "").strip()
    if not query:
        return (
            '<div style="text-align:center;padding:40px;color:#8a7355;'
            'font-style:italic;font-family:Georgia,serif;">'
            "Enter a query above to search speeches.</div>"
        )
    try:
        raw     = search_speeches(query, SPEECHES_FOLDER)
        results = normalise_results(raw)
        return render_cards(results, query)
    except Exception as e:
        return (
            f'<div style="color:#b5371a;padding:20px;border:1px solid #b5371a;'
            f'border-radius:4px;">⚠️ Error: {html_lib.escape(str(e))}</div>'
        )


# ─────────────────────────────────────────────
# 🖥️  GRADIO LAYOUT
# ─────────────────────────────────────────────

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Source+Serif+4:wght@300;400&display=swap');

/* ── Override Gradio's CSS variable system at the root ── */
:root, .light, html {
    --body-background-fill:        #f5efe3 !important;
    --background-fill-primary:     #f5efe3 !important;
    --background-fill-secondary:   #ede7d9 !important;
    --block-background-fill:       #f5efe3 !important;
    --block-border-color:          #d4c4a8 !important;
    --block-label-background-fill: #f5efe3 !important;
    --input-background-fill:       #fdfaf4 !important;
    --input-border-color:          #d4c4a8 !important;
    --input-placeholder-color:     #b09878 !important;
    --color-accent:                #b5371a !important;
    --color-accent-soft:           rgba(181,55,26,0.12) !important;
    --button-primary-background-fill:       #b5371a !important;
    --button-primary-background-fill-hover: #8f2912 !important;
    --button-primary-text-color:            #ffffff !important;
    --button-primary-border-color:          #b5371a !important;
    --border-color-primary:        #d4c4a8 !important;
    --border-color-accent:         #b5371a !important;
    --body-text-color:             #1a1209 !important;
    --body-text-color-subdued:     #8a7355 !important;
    --link-text-color:             #b5371a !important;
    --link-text-color-hover:       #8f2912 !important;
    --shadow-drop:                 0 2px 8px rgba(0,0,0,0.06) !important;
    --radius-sm:                   4px !important;
    --radius-md:                   4px !important;
    --radius-lg:                   4px !important;
}

/* ── Page & container background ── */
body,
.gradio-container,
.gradio-container > .main,
.gradio-container > .main > .wrap,
footer {
    background: #f5efe3 !important;
    font-family: 'Source Serif 4', Georgia, serif !important;
}

footer { display: none !important; }

/* ── Strip white panel boxes ── */
.block, .gap, .form,
div.gradio-html,
.gradio-row, .gradio-column,
div[class*="block"]:not(.sc):not(.sw) {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* ── Header ── */
.app-header {
    text-align: center;
    padding: 34px 20px 22px;
    border-bottom: 2px solid #d4c4a8;
    margin-bottom: 26px;
}
.app-header h1 {
    font-family: 'Playfair Display', serif;
    font-size: 2.3rem;
    color: #1a1209;
    margin: 0 0 5px;
}
.app-header p { color: #8a7355; font-style: italic; font-size: 0.97rem; margin: 0; }

/* ── Textbox ── */
.search-row textarea,
.search-row input,
textarea, input[type="text"] {
    font-family: 'Source Serif 4', Georgia, serif !important;
    font-size: 1.05rem !important;
    background-color: #fdfaf4 !important;
    border: 1px solid #d4c4a8 !important;
    border-radius: 4px !important;
    color: #1a1209 !important;
    box-shadow: none !important;
}
.search-row textarea:focus,
.search-row input:focus,
textarea:focus,
input[type="text"]:focus {
    border-color: #b5371a !important;
    box-shadow: 0 0 0 2px rgba(181,55,26,0.15) !important;
    outline: none !important;
}
::placeholder { color: #b09878 !important; opacity: 1 !important; }

/* ── Search button ── */
.sbtn,
.sbtn button,
button.sbtn,
div.sbtn > button,
.search-row button {
    background: #b5371a !important;
    background-color: #b5371a !important;
    color: #ffffff !important;
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 0.93rem !important;
    letter-spacing: 0.08em !important;
    border: 1px solid #b5371a !important;
    border-radius: 4px !important;
    cursor: pointer !important;
    transition: background 0.2s !important;
    box-shadow: none !important;
}
.sbtn:hover,
.sbtn button:hover,
button.sbtn:hover,
div.sbtn > button:hover,
.search-row button:hover {
    background: #8f2912 !important;
    background-color: #8f2912 !important;
    border-color: #8f2912 !important;
}

/* ── Output HTML panel ── */
.out, div.out {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    box-shadow: none !important;
}
"""

with gr.Blocks(css=CSS, title="Trump Speech Search") as demo:

    gr.HTML("""
    <div class="app-header">
      <h1>🇺🇸 Trump Speech Archive</h1>
      <p>Search across speeches, rallies &amp; addresses — click any result to expand the full text</p>
    </div>
    """)

    with gr.Row(elem_classes="search-row"):
        query_input = gr.Textbox(
            placeholder='e.g. "immigration", "Make America Great Again", "China trade" …',
            label="", show_label=False, scale=5, lines=1,
        )
        search_btn = gr.Button("Search", elem_classes="sbtn", scale=1)

    results_output = gr.HTML(
        value=(
            '<div style="text-align:center;padding:40px;color:#8a7355;'
            'font-style:italic;font-family:Georgia,serif;">'
            "Enter a query above to search speeches.</div>"
        ),
        elem_classes="out",
    )

    search_btn.click(fn=handle_search, inputs=query_input, outputs=results_output)
    query_input.submit(fn=handle_search, inputs=query_input, outputs=results_output)

if __name__ == "__main__":
    demo.launch(inbrowser=True)