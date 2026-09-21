# Motion (read only when the user asks for animation)

Contents: Mapping content to motion | Morph | Entrances and steps | Count-up | Ken-burns | Loops | Code morph | Checks

Every animation must carry meaning: the same thing changing, a point arriving on cue, a number landing. Decorative motion stays out. Over a video call frame drops smear movement, so keep tweens short and loops slow.

## Mapping content to motion

- the same thing changing across consecutive slides -> morph (shared `id`s + `transition:"morph"` on the later one)
- a list revealed point by point -> `fx:{step:n}` on each element, one slide
- a build across slides -> morph slides with `unnumbered:true` on the continuations
- a headline number -> `fx:{countUp:true}`, one plain number per box
- a hero image -> ken-burns drift
- a flow or timeline -> `path` with a `dash-march` loop, or morph a highlight through the steps
- a cover -> at most one ambient motion
- repeated chrome or logo -> keep its `id` stable so it morphs in place

## Morph

- Pairing key is `morphId || id`, unique within a slide. Different ids on the two slides = no morph, the elements cut. Generators must emit deterministic ids.
- Matched elements render the destination slide's content (html, fontSize, fontFamily) from frame one. Only x/y/w/h/rotation, opacity, text colour, shape fill/stroke and image crop tween. Keep `fontFamily` identical on both slides and keep the box aspect ratio, or the text swaps and stretches.
- The slide before a morph slide has its own transition forced to none. Backward navigation morphs too.
- On arrival, a partnered element skips `fx.enter` and `countUp`; an unpartnered one runs both, and without `fx.enter` gets a default fade-and-rise (0.45s from 40% of the morph).
- `present.morphSeconds` 0.1-6 (default 0.65). Code token morphs move one line-height, so raise it to about 1.5.

## Entrances and steps

- `fx.enter`: fade | fade-up | fade-down | slide-left | slide-right | slide-up | slide-down. `enterDur` seconds (slide-* 0.75, fade-* 0.55). `order` staggers: 0.12s + index x 0.05s, equal values enter together.
- `fx.step: n` (n >= 1): hidden on arrival, revealed on the n-th click. Gaps allowed. Backward arrival shows all. Stepped elements without `enter` get a plain fade.

## Count-up

`fx:{countUp:true}` rewrites `textContent`, so markup in the box is lost and every number in it animates (years, footnotes). One plain number per box.

## Ken-burns

`fx:{ambient:"kenburns", ken:{dir:"drift"|"in"|"out", scale, duration}}` (drift 1.1/26s loops; in/out 1.06/2.5s settle once). Full-bleed photo at 0,0,1280,720 + scrim rect + text on top.

## Loops

Both under `fx.loop`. Never combine with `fx.enter` on the same element (`entrance-on-motion-path`).

- `{type:"dash-march", distance:18, duration:1.4}` animates `strokeDashoffset`, so the shape needs a `stroke` and `strokeStyle:"dashed"` or `"dotted"`; on a solid stroke nothing is visible (`dash-march-no-dash`).
- `{type:"motion-path", path:"M0,0 C60,-40 140,40 200,0", duration:6, delay:0, ease:"none", speeds:[1,1]}`: path coords are offsets from the element's rest position, so start at `M0 0`. `speeds` is optional, one multiplier per on-curve anchor. `ease` in none|linear|power1-3.in/out/inOut|sine.in/out/inOut.

## Code morph

Same-id `code` elements across slides morph token by token. Needs a 1.2.0+ shell and a slower `present.morphSeconds`.

## Checks

- `validate()` codes: `overridden-enter-fx`, `entrance-on-motion-path`, `inert-countup`, `dash-march-no-dash`, `morph-key-collision`.
- `render_check.mjs --settle` (default 1500ms) waits for entrances before each capture; raise it for long `enterDur` values.
- Self-audit: does each animation carry meaning? do morphing slides share ids and `fontFamily`? one ambient motion per cover at most, none behind body text?
