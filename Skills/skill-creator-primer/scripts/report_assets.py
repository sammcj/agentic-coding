"""The page's stylesheet and script, inlined by render_report so the report stays one self-contained file."""

CSS = """
:root {
  color-scheme: only light;
  --grotesk: "Helvetica Neue", Helvetica, Roboto, ui-sans-serif, system-ui, Arial, sans-serif;
  --mono: ui-monospace, "SF Mono", SFMono-Regular, Menlo, Consolas, monospace;
  --ground: #fff; --ink: #0d0d0d; --muted: #5f5f5f;
  --accent: #de301e; --fill: #de301e1f; --rule: 2px;
  /* the mark ramp by confidence: possible in pale yellow, probable in orange, certain in the accent red */
  --maybe: #fff4c2; --maybe-rule: #e6c200;
  --likely: #ffc978; --likely-rule: #e07a0c;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; -moz-text-size-adjust: 100%; text-size-adjust: 100%; }
body { margin: 0; background: var(--ground); color: var(--ink);
       font: 400 16px/1.5 var(--grotesk); -webkit-font-smoothing: antialiased;
       overflow: hidden; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }

/* The panel beside the skill, not above it: a term is clicked in the findings
   and read in the source, and a stacked board put the two an entire screen
   apart. Each column scrolls on its own so neither scrolls the other away. */
.board { display: grid; grid-template-columns: minmax(440px, 41%) 1fr;
         grid-template-rows: auto minmax(0, 1fr) auto;
         gap: var(--rule); padding: var(--rule); height: 100vh; }
.cell { border: var(--rule) solid var(--ink); padding: 9px 12px; min-width: 0; }
/* Cells take their content height and the lists inside them give way first: `flex: 0 1 auto` shrinks a cell when
   the panel is full and never stretches one when it is not, so a short list leaves no gap under itself. Only once
   every cell is at its floor does the panel scroll, so a short window gets one scrollbar on the column rather than
   clipped cells. */
.panel { display: flex; flex-direction: column; gap: var(--rule);
         min-height: 0; overflow-y: auto; }
/* :not(.grow) is load-bearing: as a bare `.panel > .cell` this outweighs `.grow` on specificity, pinned the list
   cells at their full content height, and the panel clipped everything below the first long table. */
.panel > .cell:not(.grow) { flex: none; }
/* Only the list scrolls; a scrolling cell carried the footer away with it. The floor has to be set on the cell: left
   at auto, a flex item cannot shrink below its whole content, so a long structure list kept every row and pushed the
   wording cell off the column. Each floor is padding, borders and heading, plus two 26px rows, plus the footer where
   there is one, sized to that sum so the footer always fits under the list. */
.grow { flex: 0 1 auto; display: flex; flex-direction: column; min-height: 96px; overflow: hidden; }
.grow.rated { min-height: 120px; }  /* the prose-share line under the heading */
.grow:has(.foot) { min-height: 162px; }  /* the legend and caption slot, absent on a clean skill */
.grow .scroll { min-height: 54px; }
.grow .scroll:has(+ .foot) { margin-bottom: 10px; }
.doc { min-height: 0; overflow: auto; }
header, footer { grid-column: 1 / -1; }
/* Wraps rather than overflowing: on a narrow window the title took the full row and pushed the three figures out of
   the cell, which is the one part of the page that has to be readable at a glance. */
header { display: flex; align-items: center; justify-content: space-between;
         gap: 16px 32px; flex-wrap: wrap; }
header .stats { flex: 1 1 380px; max-width: 680px; }

@media (max-width: 900px) {
  body { overflow: auto; }
  .board { grid-template-columns: 1fr; grid-template-rows: none; height: auto; }
  .panel, .doc, .scroll { overflow: visible; }
  .grow { flex: none; }
  header { display: block; }
  header .stats { max-width: none; margin-top: 16px; }
}

h1 { font: 700 23px/1.1 var(--grotesk); margin: 0; letter-spacing: -0.02em;
     text-transform: uppercase; }
h1 span { background: var(--accent); color: #fff; padding: 0 6px; }
h2 { font: 700 11px/1 var(--grotesk); letter-spacing: 0.14em; text-transform: uppercase;
     margin: 0 0 8px; color: var(--muted); }
h2.sub { margin: 12px 0 8px; padding-top: 10px; border-top: 1px solid #ececec; }

/* the stat strip: a coloured rule over each figure, its label on the same baseline so the header stays one line tall */
header.cell { padding-top: 8px; padding-bottom: 8px; }
.stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 22px; }
.stats div i { display: block; height: 4px; margin-bottom: 6px; }
.stats div b { font: 700 21px/1 var(--grotesk); letter-spacing: -0.01em; }
.stats div u { text-decoration: none; margin-left: 8px; white-space: nowrap;
               font: 400 10px var(--mono); letter-spacing: 0.1em; color: var(--muted); }


footer { display: flex; align-items: center; gap: 14px;
         font: 400 10px var(--mono); letter-spacing: 0.1em; color: var(--muted);
         padding: 7px 16px; border: var(--rule) solid var(--ink); text-transform: uppercase; }
footer .end { margin-left: auto; }

/* The verdict is the one word set large: it judges every cell, so no single cell's rating may compete with it. */
.verdict { font: 700 46px/1 var(--grotesk); letter-spacing: -0.02em; text-transform: uppercase; }
.verdict.certain { color: var(--accent); }
.verdict.probable { color: var(--likely-rule); }
.verdict small { font: 700 16px var(--grotesk); letter-spacing: 0; text-transform: none; }
/* Columns by count, since the agent chip is there only when findings were passed. */
.score { display: grid; grid-auto-flow: column; grid-auto-columns: 1fr; gap: 12px; margin-top: 10px; }
.score div { border-top: 5px solid var(--ink); padding-top: 6px; font: 400 11px var(--mono); }
.score div.certain { border-top-color: var(--accent); }
.score div.probable { border-top-color: var(--likely-rule); }
.score b { display: block; font: 700 14px var(--grotesk); }
.score u { display: block; text-decoration: none; color: var(--muted); letter-spacing: 0.08em;
           text-transform: uppercase; }
.score em { font-style: normal; color: var(--muted); }
.reasons { margin: 8px 0 0; padding: 0; list-style: none; font: 400 12px/1.5 var(--mono); }
.reasons li { padding-left: 9px; border-left: var(--rule) solid var(--accent); margin-bottom: 3px; }
.reasons b { text-transform: uppercase; letter-spacing: 0.08em; font-size: 10px; margin-right: 6px; }
/* The budget's own rating, demoted to a label: set large it read as the verdict on the whole skill. */
.band { font-weight: 700; color: var(--ink); text-transform: uppercase; }
.band.ok, .band.poor { color: var(--accent); }
/* An agent finding is a sentence rather than a term, so the grade sits in the count column and the fix under the text. */
tr.agent td.n { width: 1%; }
tr.agent td.n::before { content: none; }
tr.agent small { display: block; color: var(--muted); font-size: 12px; }
tr.agent small b { color: var(--ink); font-weight: 400; }
.rate { font: 400 13px var(--mono); color: var(--muted); margin-top: 4px; }
.note { font: 400 12px/1.5 var(--mono); color: var(--ink); margin-top: 8px;
        border-left: var(--rule) solid var(--accent); padding-left: 9px; }
.gauge { position: relative; height: 22px; border: var(--rule) solid var(--ink); margin-top: 8px; }
.gauge i { position: absolute; inset: 0 auto 0 0; background: var(--accent); }
.gauge b { position: absolute; top: -2px; bottom: -2px; width: var(--rule); background: var(--ink); }
.ticks { display: flex; justify-content: space-between;
         font: 400 11px var(--mono); color: var(--muted); margin-top: 4px; }

/* per-file bars: one grey ramp, the accent reserved for the file that leads */
.bar { display: grid; grid-template-columns: 190px 1fr 44px; align-items: center;
       gap: 8px; margin-bottom: 4px; font: 400 12px var(--mono); }
.bar u { text-decoration: none; color: var(--muted); overflow: hidden;
         text-overflow: ellipsis; white-space: nowrap; }
.bar s { text-decoration: none; height: 13px; background: #d4d4d4; display: block; }
/* The accent marks the file to cut. Set explicitly: as `:first-of-type` it
   matched the band div above these rows and never reached a bar at all. */
.bar.lead s { background: var(--accent); }
.bar em { font-style: normal; text-align: right; color: var(--muted); }

table { border-collapse: collapse; width: 100%; font: 400 13px var(--mono); }
td { padding: 3px 6px 3px 0; vertical-align: top; border-bottom: 1px solid #ececec; }
td.n { width: 46px; color: var(--muted); text-align: right; white-space: nowrap; }
td.r { color: var(--muted); text-align: right; white-space: nowrap; }
tr.pick { cursor: pointer; }
tr.pick:hover td { background: var(--fill); }
/* The list is the part of a cell that gives: it takes what its content needs and hands the rest back when the panel
   is full, so 42 structure rows scroll here rather than pushing the cells under them off the column. */
.scroll { flex: 1 1 auto; min-height: 0; overflow: auto; }

/* the frequency chart, drawn behind the rows it labels rather than beside them */
td.f { width: 26%; }
td.f s { display: block; height: 11px; background: #d4d4d4; text-decoration: none; }
tr.pick:first-child td.f s { background: var(--accent); }

/* spec findings, listed with the rest: an error takes the certain step, a warning the probable one */
/* Not clickable: a spec finding names the whole file, so there is nothing to scroll to. */
tr.pick.spec, tr.pick.specw { cursor: default; }

/* before and after: two bars to a pair, the baseline hollow and the current filled */
.pair { margin-bottom: 12px; font: 400 12px var(--mono); }
.pair u { text-decoration: none; color: var(--muted); }
.pair div { display: grid; grid-template-columns: 1fr 96px; align-items: center;
            gap: 8px; margin-top: 4px; }
.pair s { text-decoration: none; height: 13px; display: block; min-width: 1px; }
.pair .was s { background: transparent; border: var(--rule) solid #9a9a9a; }
.pair .now s { background: var(--accent); }
.pair em { font-style: normal; color: var(--muted); }
.cut { color: var(--accent); }

/* The caption under the list: the reason for whatever is hovered or chosen. It shares one fixed-height slot with the
   legend, showing the legend until something is hovered and the reason after, so a hover never resizes the cell. Sized
   to the text, it pushed the list up on every hover and shoved the legend out of the cell. The reasons run from one
   line to five, so the slot scrolls rather than grows. */
.foot { flex: none; height: 4.6em; margin-top: auto; padding-top: 6px; border-top: 1px solid #ececec;
        font: 400 12px/1.45 var(--mono); overflow: hidden; }
.why { display: none; margin: 0; height: 100%; overflow: auto; }
.foot.live .why { display: block; }
.foot.live .legend { display: none; }

/* Sized to sit on the footer rule beside the date, not to stand over it. */
button { font: 400 10px/1 var(--mono); letter-spacing: 0.1em; text-transform: uppercase;
         border: 1px solid var(--ink); background: var(--ground);
         color: var(--ink); padding: 4px 9px; cursor: pointer; white-space: nowrap; }
button:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
button.done { background: var(--ink); border-color: var(--ink); color: var(--ground); }
/* The brief, kept hidden as the copy source and revealed only if the clipboard
   refuses, so there is still something to select by hand. */
#brief { margin: var(--rule); padding: 14px 16px; border: var(--rule) solid var(--ink); }
body.spill { overflow: auto; }

/* flex: none, or the wrapped second row was shrunk away by the column above it and the legend lost half its keys. */
.legend { display: flex; gap: 8px 16px; font: 400 11px var(--mono);
          color: var(--muted); flex-wrap: wrap; flex: none; }
.legend span { white-space: nowrap; }
.key { display: inline-block; width: 22px; height: 11px; margin-right: 5px;
       vertical-align: -1px; }
/* The key swatches match the marks; the underline is the same rule in each step's colour and carries no meaning
   of its own. A dotted rule on plain ground could not be seen at reading distance. */
.k-possible { background: var(--maybe); box-shadow: inset 0 -3px 0 var(--maybe-rule); }
.k-probable { background: var(--likely); box-shadow: inset 0 -3px 0 var(--likely-rule); }
.k-certain { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
.k-em { background: #e9eff9; box-shadow: inset 0 -3px 0 #1a4fa0; }
.legend b { font-weight: 700; color: var(--ink); letter-spacing: 0.1em; text-transform: uppercase; }

/* the source, one block per line so a flagged unit shades over its whole span */
/* The heading scrolls with its file. Pinned, it detached from the text it names
   and read as a stray bar over the document. */
h3.file { font: 700 11px/1 var(--mono); letter-spacing: 0.1em; text-transform: uppercase;
          margin: 22px 0 8px; padding: 7px 0; color: var(--ink);
          border-bottom: var(--rule) solid var(--ink); background: var(--ground); }
h3.file:first-of-type { margin-top: 0; }
pre { margin: 0; font: 400 13px/1.65 var(--mono); white-space: pre-wrap;
      word-wrap: break-word; }
.l { display: block; padding: 0 6px; border-left: var(--rule) solid transparent; }
.l:empty { height: 1.65em; }
/* The ramp rewrite-slop uses, shared so a reader moving between the two reports reads one scale: a dense run is
   possible (yellow); a long paragraph, a prose table and an over-long fence are probable (orange); the two deletable
   findings are certain (red). A run often contains a blob, which keeps its deeper shade inside it.
   Every shade is a block of the same weight, so the kind is carried by the margin label rather than by the colour -
   the earlier pale grey on code was invisible at reading distance and said nothing the label does not. */
.l.dense { background: #fffbe6; border-left-color: var(--maybe-rule); }
/* Possible like a dense run, but lighter: a whole file can be wrapped, and a full-strength shade on every paragraph
   would drown the findings that matter. */
.l.wrap { background: #fffdf2; border-left-color: #f0dc7a; }
.l.blob, .l.code, .l.table, .l.descw { background: #ffe4bd; border-left-color: var(--likely-rule); }
.l.redundant, .l.desc { background: #ffdedb; border-left-color: var(--accent); }
/* The label names the block on its first line, set in the right margin so it never displaces the source. */
.l.lead { position: relative; }
.l.lead::after { content: attr(data-label); position: absolute; right: 0; top: 0;
                 font: 400 10px var(--mono); letter-spacing: 0.08em; color: var(--muted);
                 background: var(--ground); padding: 0 2px 0 8px; text-transform: uppercase; }
/* The card at the cursor over the preview: the cells' ink frame, with the finding's step on the ramp down its left. */
#card { position: fixed; z-index: 10; max-width: 340px; pointer-events: none; background: var(--ground);
        border: var(--rule) solid var(--ink); border-left-width: 6px; padding: 7px 10px;
        box-shadow: 4px 4px 0 #0d0d0d26; font: 400 12px/1.45 var(--mono); }
#card[hidden] { display: none; }
#card.possible { border-left-color: var(--maybe-rule); }
#card.probable { border-left-color: var(--likely-rule); }
#card.certain { border-left-color: var(--accent); }
#card i { float: right; margin-left: 12px; font: 400 10px/1.8 var(--mono); letter-spacing: 0.08em;
          text-transform: uppercase; color: var(--muted); }
#card b { font: 700 13px var(--grotesk); }
#card p { margin: 4px 0 0; }
/* One list ranked worst first, so the row says its step on the ramp rather than its kind: a rule bar down the left
   in the confidence colour, and the count in the same. The kind is in the row's own text and its reason. */
tr.pick.possible td.n { color: var(--maybe-rule); box-shadow: inset 3px 0 0 var(--maybe-rule); }
tr.pick.probable td.n { color: var(--likely-rule); box-shadow: inset 3px 0 0 var(--likely-rule); }
tr.pick.certain td.n { color: var(--accent); font-weight: 700;
                       box-shadow: inset 3px 0 0 var(--accent); }
td.n { padding-left: 9px; }
mark { color: inherit; padding: 0 1px; cursor: pointer; }
mark[data-conf="possible"] { background: var(--maybe); box-shadow: inset 0 -3px 0 var(--maybe-rule); }
mark[data-conf="probable"] { background: var(--likely); box-shadow: inset 0 -3px 0 var(--likely-rule); }
mark[data-conf="certain"] { background: var(--fill); box-shadow: inset 0 -3px 0 var(--accent); }
/* An invisible character is shown as its code point, or the mark would be as invisible as the character. */
mark.inv { font: 400 10px var(--mono); letter-spacing: 0.06em; padding: 0 3px; vertical-align: 1px; }
tr.pick.possible td.n::before { content: "?"; color: var(--muted); margin-right: 3px; }
/* Mid-sentence bold is a density, not a defect at the span, so it takes the blue
   of the file count rather than competing with the severity ramp. */
mark.em { background: #e9eff9; box-shadow: inset 0 -3px 0 #1a4fa0; }
tr.pick.em td.n { color: #1a4fa0; }
/* a chosen term holds; everything else recedes rather than disappears */
body.sel mark { background: transparent; box-shadow: none; color: #a8a8a8; }
body.sel mark.on { background: var(--accent); color: #fff; box-shadow: none; }
body.sel tr.pick { opacity: 0.35; }
body.sel tr.pick.on { opacity: 1; }
body.sel tr.pick.on td { background: var(--fill); }
/* The arrival marker, on either end of the jump: the block scrolled to in the source, or the row traced back to
   from it. It fades, so the page is not left carrying a second permanent highlight. */
.flash { animation: flash 1.1s ease-out; }
@keyframes flash { from { background: var(--fill); border-left-color: var(--accent); } }
@media (prefers-reduced-motion: reduce) { .flash { animation: none; } }
tr.here td { background: var(--fill); box-shadow: inset 2px 0 0 var(--accent); }
.empty { color: var(--muted); font: 400 13px var(--mono); }
"""

JS = """
var body = document.body, sel = null;
var why = document.getElementById('why'), pinned = '';
/* The reason and the legend swap within one fixed slot, so the legend comes back once nothing is hovered or pinned.
   The slot is absent on a skill with no wording findings, where structure rows still call this. */
var foot = document.getElementById('foot');
function say(text) {
  why.textContent = text || pinned;
  if (foot) foot.classList.toggle('live', why.textContent !== '');
}
document.addEventListener('mouseover', function (e) {
  var el = e.target.closest('[data-why]');
  if (el) say(el.dataset.why);
});
document.addEventListener('mouseout', function (e) {
  if (e.target.closest('[data-why]')) say('');
});
/* A flagged line or word in the preview shows its rule and reason in a card at the cursor, so reading the source
   does not mean looking away to the caption. */
var card = document.createElement('div'), doc = document.querySelector('.doc');
card.id = 'card'; card.hidden = true;
card.innerHTML = '<i></i><b></b><p></p>';
body.appendChild(card);
function hideCard() { card.hidden = true; }
doc.addEventListener('mousemove', function (e) {
  var el = e.target.closest('[data-head]');
  if (!el) { hideCard(); return; }
  var head = el.dataset.head, text = el.dataset.why;
  if (text.indexOf(head + ': ') === 0) text = text.slice(head.length + 2);
  card.className = el.dataset.conf;
  card.children[0].textContent = el.dataset.conf;
  card.children[1].textContent = head;
  card.children[2].textContent = text;
  card.hidden = false;
  // Below right of the pointer, flipped at the window's edges so it never runs off screen.
  var gap = 16, x = e.clientX + gap, y = e.clientY + gap;
  if (x + card.offsetWidth > innerWidth - 8) x = e.clientX - gap - card.offsetWidth;
  if (y + card.offsetHeight > innerHeight - 8) y = e.clientY - gap - card.offsetHeight;
  card.style.left = Math.max(8, x) + 'px';
  card.style.top = Math.max(8, y) + 'px';
});
doc.addEventListener('mouseleave', hideCard);
document.addEventListener('scroll', hideCard, true);
function choose(term) {
  sel = (sel === term) ? null : term;
  body.classList.toggle('sel', sel !== null);
  // A mark carries every term that matched its span, so membership, not equality
  document.querySelectorAll('[data-term]').forEach(function (el) {
    el.classList.toggle('on', sel !== null && el.dataset.term.split('|').indexOf(sel) !== -1);
  });
  if (sel) {
    var first = document.querySelector('mark.on');
    if (first) first.scrollIntoView({block: 'center', behavior: 'smooth'});
  }
}
/* Landing is not arriving: on a document of forty orange blocks, scrolling one to the centre says nothing about
   which one was asked for. The flash names it. Removing the class and reading offsetWidth forces the reflow that
   lets the animation restart when the same target is picked twice. */
function land(el) {
  if (!el) return;
  el.scrollIntoView({block: 'center', behavior: 'smooth'});
  el.classList.remove('flash');
  void el.offsetWidth;
  el.classList.add('flash');
}
function here(row) {
  document.querySelectorAll('tr.here').forEach(function (el) { el.classList.remove('here'); });
  if (row) row.classList.add('here');
}
document.addEventListener('click', function (e) {
  // The jump back: a shaded block in the source selects the row that explains it, so a finding read in the document
  // can be traced to its rule without hunting the list for the matching line number.
  var backTo = e.target.closest('[data-back]');
  if (backTo && !e.target.closest('[data-term]')) {
    var row = document.getElementById(backTo.dataset.back);
    if (row) {
      here(row);
      pinned = row.dataset.why || '';
      say('');
      land(row);
    }
    return;
  }
  var go = e.target.closest('[data-goto]');
  if (go) {
    pinned = go.dataset.why || '';
    say('');
    here(go);
    land(document.getElementById(go.dataset.goto));
    return;
  }
  var el = e.target.closest('[data-term]');
  // A shared mark's key holds every term that matched it; select by the first,
  // or the joined key would match nothing.
  if (el) { pinned = el.dataset.why || ''; say(''); choose(el.dataset.term.split('|')[0]); }
  else if (sel) { pinned = ''; say(''); choose(sel); }
});
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape' && sel) { pinned = ''; say(''); choose(sel); }
});

var copy = document.getElementById('copy'), stash = document.getElementById('brief');
function flashed(ok) {
  if (!ok) { stash.hidden = false; body.classList.add('spill'); stash.scrollIntoView(); }
  copy.textContent = ok ? 'Copied' : 'Copy failed, brief below';
  copy.classList.add('done');
  setTimeout(function () {
    copy.textContent = 'Copy brief';
    copy.classList.remove('done');
  }, 1800);
}
/* file:// is not a secure context in every browser, so the clipboard API is not
   always there to call. */
function bySelection() {
  var ta = document.createElement('textarea'), ok = false;
  ta.value = stash.textContent;
  ta.style.cssText = 'position:fixed;top:0;left:0;opacity:0';
  document.body.appendChild(ta);
  ta.select();
  try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
  document.body.removeChild(ta);
  flashed(ok);
}
copy.addEventListener('click', function (e) {
  e.stopPropagation();
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(stash.textContent).then(function () { flashed(true); },
                                                          bySelection);
  } else bySelection();
});
"""
