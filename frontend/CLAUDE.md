# Frontend Design System — IP-SAKTI Sahayak

## Design Style: Neumorphism

Follow **Neumorphism (soft UI)** throughout the project — elements appear extruded from or inset into the background using dual soft shadows (one light, one dark) rather than flat borders or hard drop shadows. No flat Material/skeuomorphic mixing; stay consistent across every screen (chat UI, classifier, ABS helper, dashboards).

Core neumorphic rules:
- **Same-color surfaces**: cards, buttons, inputs share the page background color; depth comes only from shadow, not color contrast.
- **Dual shadow technique**: pair a light shadow (top-left) with a darker shadow (bottom-right) of the base color to simulate a light source from the top-left.
  - Raised element: `box-shadow: 6px 6px 12px var(--shadow-dark), -6px -6px 12px var(--shadow-light);`
  - Inset/pressed element (active inputs, pressed buttons): `box-shadow: inset 4px 4px 8px var(--shadow-dark), inset -4px -4px 8px var(--shadow-light);`
- **Large border-radius** (16–24px) on cards/buttons/inputs — soft, pillowy silhouettes, never sharp corners.
- **Low contrast, high subtlety**: shadows should be gentle, not harsh — avoid pure black shadows; derive shadow colors from the base background (darken/lighten by ~8–12%).
- **Minimal borders and dividers** — let shadow and spacing create separation, not lines.
- Use a flat/inset state for **disabled** elements and a pressed/inset transition on `:active` for tactile feedback on buttons; raised states for actionable/default elements.
- **Selected/currently-active list items** (e.g. the active item in a history list) are NOT inset — inset reads as "disabled" or "pressed," not "chosen." Give them a raised `nmRaised`-style shadow plus a small accent-colored bar on the leading edge (`position: relative` on the item, a `::before` pseudo-element ~3px wide, inset a few px from the item's edges, colored `--accent-ochre`) so the selection reads as a distinct highlighted tab rather than a pushed-in button.

## Color Theme: Muted Ochre + Herbal Green

Since IP-SAKTI Sahayak is an Ayurveda-focused assistant, the palette draws from turmeric/ochre (traditional Ayurvedic pigment) and muted herbal sage/green (botanical, calming), kept desaturated and warm for a rich, premium, non-garish feel. Avoid saturated/neon tones — everything should read as muted, warm, and textured like natural dyes and dried herbs, not corporate flat-design brights.

### Light mode (primary)
| Token | Hex | Use |
|---|---|---|
| `--bg-base` | `#EDE6D8` | Page background (warm parchment/cream) |
| `--surface` | `#E8E0D0` | Card/panel base (same family as bg, for neumorphic blending) |
| `--shadow-light` | `#FFFDF6` | Light-side neumorphic shadow |
| `--shadow-dark` | `#C9BFA8` | Dark-side neumorphic shadow |
| `--accent-ochre` | `#B8834A` | Primary accent (muted turmeric/ochre) — primary CTAs, active nav, key icons |
| `--accent-ochre-deep` | `#8C5F2E` | Ochre hover/pressed state, headings emphasis |
| `--accent-green` | `#6B7F5B` | Secondary accent (muted sage/herbal green) — success states, National jurisdiction tag, secondary actions |
| `--accent-green-deep` | `#4A5A3E` | Green hover/pressed, International jurisdiction tag |
| `--text-primary` | `#3A342A` | Body text (warm dark brown-black, not pure black) |
| `--text-muted` | `#6E6656` | Secondary/help text |
| `--border-hairline` | `#DDD3BE` | Rare hairline separators only where shadow isn't enough |

### Dark mode
| Token | Hex | Use |
|---|---|---|
| `--bg-base` | `#242119` | Page background (deep warm charcoal-brown) |
| `--surface` | `#282419` | Card/panel base |
| `--shadow-light` | `#2F2B1E` | Light-side neumorphic shadow |
| `--shadow-dark` | `#1F1C14` | Dark-side neumorphic shadow |
| `--accent-ochre` | `#A06C3E` | Primary accent, brightened for dark contrast |
| `--accent-green` | `#8FA37A` | Secondary accent, brightened for dark contrast |
| `--text-primary` | `#EDE6D8` | Body text |
| `--text-muted` | `#B0A78F` | Secondary text |

Reserve pure white/black for nothing — all whites are warm-tinted (`#FFFDF6`-family), all blacks are warm-tinted (`#161410`-family), consistent with the neumorphic same-family-shadow rule above.

### Zone-based coloring within a screen

When a layout has distinct functional zones (e.g. a navigation/history sidebar vs. a primary content area), give each zone its own tint rather than painting the whole screen one flat base:
- **Navigation/utility surfaces** (sidebars, rails) get the **herbal green** identity — override `--bg-base`, `--surface`, `--shadow-light`, `--shadow-dark`, `--text-primary`, `--text-muted`, `--border-hairline` as CSS custom properties scoped to that zone's root class (e.g. `.sidebar { --surface: #90ab79; ... }`). Because custom properties inherit, every `.nmRaised`/`.nmInset` element nested inside automatically re-themes to green without new class variants.
- **Primary content surfaces** (the chat/work area) get a **lighter, more muted tint of the ochre family** than the page's default `--bg-base` — a dedicated `--chat-bg` token, lighter than `--bg-base`, applied directly as that zone's background.
- Leave `--accent-ochre` / `--accent-green` accent tokens un-overridden inside a colored zone so accent highlights (e.g. an active/selected state) keep popping as a complementary contrast against that zone's own base — don't re-tint accents to match the zone.

### Theme toggle

Dark mode is a user-facing toggle, not a `prefers-color-scheme` fallback:
- **Default theme is always `"light"`** on first mount, regardless of the visitor's OS/browser color-scheme preference — don't reintroduce a `matchMedia("(prefers-color-scheme: dark)")` initializer for this app.
- Apply the resolved theme as a `data-theme="light" | "dark"` attribute on the page's root element; the root page's own dark-mode token overrides live under `.chatbotPage[data-theme="dark"]` in its own module file, rather than inside a `prefers-color-scheme` media query.
- A **zone's** dark-mode override (e.g. the green sidebar's dark tokens) lives in that zone's own component module file and must **not** chain the page's root class (e.g. not `.chatbotPage[data-theme="dark"] .sidebar`) — CSS Modules hash class names per file, so a selector in `Sidebar.module.css` can't match a class defined in `ChatBot.module.css` without `:global()`. Since `data-theme` is only ever set on that one root element, write it as a plain attribute selector instead: `[data-theme="dark"] .sidebar { ... }` in `Sidebar.module.css`.
- Render the toggle as a sliding pill switch (thumb translates + recolors between `--accent-ochre` for light and `--accent-green` for dark) placed in the top bar — consistent with the neumorphic `nmInset` track treatment used elsewhere.
- **Exception — chrome-less pages** (e.g. the `/` landing page, which has no top bar or any toggle affordance): these may fall back to a `prefers-color-scheme` media query for dark-mode tokens instead of a manual toggle, since there's no control surface to drive explicit state from. The "always default to light, never `matchMedia`" rule above applies to pages that have app chrome (a top bar/sidebar) and therefore *could* host a toggle but shouldn't silently follow the OS instead.

## Landing / Marketing Pages

The `/` route (`src/pages/Home/`) is the app's front door — unauthenticated, no sidebar/topbar chrome — and follows its own hero-page pattern distinct from the in-app screens:
- **Structure**: ambient full-bleed background (soft blurred gradient "orbs" drifting slowly via `@keyframes`, plus a faint SVG-turbulence grain overlay at very low opacity for texture) behind a centered hero stack — brand mark → wordmark → italic tagline → one-line subtext → single primary CTA → a small caps "trust row" of credibility keywords — with the standard legal disclaimer footer pinned below.
- **One CTA only**: a landing/hero page gets exactly one primary action (here, into `/chatbot`). Don't add secondary buttons or nav links competing for attention — the whole page is built to funnel toward that single click.
- **Entrance motion**: stagger a `heroRise` fade-and-rise-in animation across the stack (logo, then name, then tagline, then subtext, then CTA, then trust row) with ~70–80ms increasing delays, so the page reveals itself as a sequence rather than popping in all at once. Always pair with an `@media (prefers-reduced-motion: reduce)` block that disables every animation on the page.
- Respect the same folder-per-page/CSS-Modules convention as every other page (`Home.jsx` + `Home.module.css`), and redeclare the shared ochre/green tokens as local custom properties on the page's root class rather than importing them from elsewhere, per the zone-based coloring rule above.

## Common Pitfalls

- **A `<Link>`/`<a>` wrapping a `<button>` leaks its underline onto the button's text** (`text-decoration` inherits down through the button into its text node in some browsers/states). Fix it on the wrapping link (`.logoutLink { text-decoration: none; }`), not by fighting specificity on the inner button.
- **Don't apply the dual light/dark neumorphic shadow technique to a saturated accent-gradient surface** (e.g. a primary CTA button) — that technique simulates depth on a *same-color* surface and reads as muddy/busy on top of a colored gradient. Use a single soft ambient drop shadow (`0 Npx Mpx -Opx rgba(<darkest accent color>, 0.5–0.6)`) instead, deepening it on hover rather than adding more shadow layers.
- **A multi-stop gradient beats a 2-stop one** whenever the two accent colors (ochre, green) are far apart in hue/lightness — a direct `linear-gradient(ochre, green)` produces a muddy seam in the middle. Add a shared mid-tone stop (e.g. `--accent-ochre-deep`) at ~40–50% so the blend reads as intentional, not accidental.

### Reference/citation chips: theme-inverted contrast

A chip that must stay legible and visually distinct from its surrounding surface **regardless of theme** (e.g. a statutory citation tag on an assistant message) should not just borrow the page's existing green/ochre accent — on some themes that accent sits too close in value to the surface it's on. Instead:
- Add a dedicated `--chip-bg` / `--chip-fg` token pair per theme, each **borrowing the other theme's tone** (e.g. light mode's chip background is a muted-olive variant of dark mode's `--chat-bg`; dark mode's chip background borrows light mode's) so the chip is guaranteed strong contrast against its own theme's local background without hand-tuning per theme.
- Don't use the raw swapped value verbatim — nudge it toward the palette's warm/olive family (desaturate, warm the hue slightly) so it reads as an intentional muted accent rather than a jarring inverted/negative patch.
- Give the chip a small leading marker (e.g. an 8px dot in `--chip-fg`) rather than a lettered badge, and a raised (not inset) shadow with a hover lift, since these chips are meant to invite a click through to the cited source.
- **Only the citation chip itself is a real link** — render it as `<a href={c.url} target="_blank" rel="noopener noreferrer">` when the citation carries a URL (backend's `CitationSchema.official_url`), and fall back to a plain non-interactive `<span>` when it doesn't; give the anchor `text-decoration: none` so it matches the span's look exactly. The rest of an assistant message bubble must **not** look or behave clickable — don't let the bubble inherit `.nmRaised`'s `:active` inset "pressed" shadow (override `.msgBubble.nmRaised:active` back to the raised shadow, and set `cursor: default` on `.msgBubble`), since a full-bubble press effect with no actual click handler misleads users into thinking the whole message is tappable.

### Assistant message bubble width

The assistant bubble is meant to read as a full-width "answer panel," not a chat-style bubble capped at 80% width like the user's message:
- `.msgRow` (both roles) stays capped at `max-width: 720px` and centered (`margin: 0 auto`) — this shared column is what defines "the chat area."
- `.msgRow.assistant .msgBubble` overrides the base `.msgBubble { max-width: 80% }` with `max-width: 100%; width: 100%` so it fills that same 720px column edge-to-edge.
- Don't remove the `max-width: 720px` cap from `.msgRow` itself to make the assistant answer "wider" — that stretches it past the column the user's right-aligned bubble sits in, so the two rows no longer share a right edge. The intended effect is the assistant bubble's right edge lining up exactly with where the user bubble's right edge already sits, not a full-viewport-width answer.

### Resizable panels (drag-to-resize)

For a panel whose width the user should be able to adjust (e.g. the history sidebar):
- Control width via component state (`sidebarWidth`) applied as an **inline style**, not a CSS class — the CSS class still owns the collapse/expand transition (padding, opacity, border), but width itself is fully state-driven so there's one source of truth.
- Render a thin (~6px) absolutely-positioned drag handle on the panel's resizable edge (`cursor: col-resize`), transparent at rest and highlighting `--accent-ochre` on hover.
- On `mousedown` on the handle, flip an `isResizing` flag and attach `mousemove`/`mouseup` listeners on `window` (cleaned up in a `useEffect` keyed on that flag) that clamp the new width between a min/max and update state; also set `document.body.style.cursor = "col-resize"` and `userSelect = "none"` for the drag's duration so dragging doesn't select page text.
- While `isResizing` is true, override the panel's `transition` inline style to `"none"` so the drag tracks the cursor immediately instead of chasing it through the CSS transition meant for the open/close animation.

### Follow-up suggestion chips

An assistant reply may carry a `followUps: string[]` array of suggested next questions, rendered as a row of clickable chips beneath the reply:
- Only render the chip row under the **last** message in the list, and only once `!isTyping` — otherwise stale chip rows would pile up under every earlier assistant turn as the conversation grows.
- Clicking a chip re-uses the normal send path: `handleSend(overrideText)` takes an optional override that falls back to the current `draft` state when omitted, so a chip click and a typed-and-submitted message both flow through one function.
- Each list item needs an optional sibling row (the chips) beneath its message row, not nested inside the bubble, so `.map` renders `<Fragment key={msg.id}>` wrapping `.msgRow` + the conditional `.followUpRow` — avoids adding an extra always-present wrapper div per message.
- Style chips as their own `.followUpChip` class (raised nm shadow, `translateY` hover lift, inset `:active`) rather than reusing `.nmRaised` directly — they need smaller padding/font than the standard raised primitive.

### Composer language selector

The response-language picker (`English` / `Hindi` / `Tamil` / `Telugu`) lives inside `Composer`, not `ChatTopbar` — it sits as a sibling of the input box on the same row (`.composerRow`), not inside `.composerInner`, so it can be styled and sized independently of the growing textarea:
- `.composerRow` uses `align-items: center` so the (intentionally shorter) select vertically centers against the taller input box rather than bottom- or top-aligning with it.
- The select's height is **hardcoded** (`height: 46px`), not derived via `align-items: stretch` from the input box's natural height — stretching looked correct in theory but the resulting control read as oversized/mismatched next to the input; a fixed height close to (but a little smaller than) the composer bar's own height reads as intentionally "roughly equal," and is the size to preserve on future edits rather than re-deriving it dynamically.
- Keep meaningful `gap` between the select and `.composerInner` (currently `24px`) — it needs to read as a separate control glued to the composer row, not as a fourth button crammed into the input box itself.
- On send, map the display label to an ISO code (`English → en`, etc.) via a lookup object before it goes into the `/query` request body's `language` field — the backend's `QueryRequest.language` schema expects ISO codes, never the display label.

### Voice input recording state

The mic button in `Composer` toggles an `isListening` boolean (`useState`), not a fire-and-forget action:
- The mic `iconBtn` gets a `.listening` class while active (filled `--accent-green` background) so the pressed/active state is visually sticky, not just a `:active` flash — click again to un-toggle it.
- While `isListening` is true, the `<textarea>` is swapped out entirely for a `.recordingIndicator` block reading "Recording" + three animated dots, rather than just disabling the textarea and leaving it empty — a disabled empty input with no feedback reads as broken, not "listening."
- The three dot `<span>`s must contain a literal `.` character — an empty `<span />` animates opacity correctly but renders nothing, which is an easy silent bug to reintroduce.
- Dot cadence is driven by two CSS `@keyframes` (`dotAppear2`, `dotAppear3`) on one shared cycle duration (currently `3s`, i.e. 1s per stage), not by `animation-delay` — delay only applies once before the *first* iteration in an infinite loop, so it can't be used to stagger a repeating reveal-then-reset pattern. Instead each dot's keyframes encode its own show/hide percentage window within the single cycle (dot 2 hidden 0–33%, dot 3 hidden 0–66%), so both animations start in sync at `0%` and the whole thing resets to "1 dot" cleanly every cycle.
- `.recordingIndicator` mirrors the textarea's box model (`padding: 8px 0`, `line-height: 1.5`) and uses `align-self: stretch` (the parent `.composerInner` is `align-items: flex-end`) so the text sits at the same vertical position the typed input would occupy, rather than bottom-pinned like a short label.

## File Structure: Folder-per-Component with CSS Modules

Every component/page gets its **own folder** containing exactly its JSX and its stylesheet — never a loose `.jsx` sitting next to unrelated files. Pages live in `src/pages/`; everything a page breaks down into (sidebar, topbar, message list, composer, icon set, …) lives in `src/components/`, one folder per component, following the exact same convention — a subcomponent is not nested inside its page's own folder.

```
src/pages/ChatBot/
├── ChatBot.jsx                    # PascalCase, matches folder name
└── ChatBot.module.css             # same basename, .module.css

src/components/Sidebar/
├── Sidebar.jsx
└── Sidebar.module.css
src/components/ChatTopbar/
├── ChatTopbar.jsx
└── ChatTopbar.module.css
```

Rules:
- **Folder name = component name, PascalCase** (e.g. `ChatBot/`, `Sidebar/`, `FormulationClassifier/`).
- **File basenames match the folder exactly**: `ChatBot.jsx` + `ChatBot.module.css` — not `index.jsx`, not camelCase, not the lowercase route name.
- **The exported component function matches the same PascalCase name** (e.g. `export default function ChatBot()` inside `ChatBot.jsx`) — folder, file, and component identifier all agree.
- **Styling is CSS Modules only** (`*.module.css`, imported as `import styles from "./ChatBot.module.css"`), and **every component/page imports its own module file** — never another component's. No inline `style={{}}` for anything beyond one-off dynamic values, no CSS-in-JS libraries.
- **Class names inside a module file are camelCase** (`.historyItem`, `.historyItemTitle`), referenced as `styles.historyItem` — never hyphenated names requiring bracket access.
- The neumorphic zone tokens (`--bg-base`, `--surface`, `--accent-ochre`, etc.) are declared as CSS custom properties scoped to a root/zone class (e.g. `.chatbotPage`, `.sidebar`) inside that component's own module file — see Zone-based coloring above. They cascade through the DOM tree to every descendant regardless of which module file that descendant's own class comes from, so a subcomponent rendered inside `.sidebar` (or inside `.chatbotPage[data-theme="dark"]`, etc.) automatically inherits the right values without redeclaring the tokens itself.
- **Shared primitive classes** (`.nmRaised`, `.nmInset` for the raised/inset neumorphic surface states) are re-declared byte-identical in every module file that uses them, rather than imported from a shared stylesheet — CSS Modules scope per-file, so this is intentional duplication, not an oversight to "DRY up."
- Two components are allowed to duplicate an identical block of markup-and-styles verbatim (e.g. the brand mark + wordmark, which appears once in `Sidebar.module.css` and again in `ChatTopbar.module.css` for the collapsed-sidebar state) rather than being extracted into a third shared component — they render in different zones with different cascaded tokens, and the duplication is small and stable.
- A small presentational element whose look is entirely defined by a *sibling* component's stylesheet (e.g. the hamburger icon's bar-lines, previously styled via `.hamburgerBtn .bar` in the topbar's CSS) should have that styling flattened into a plain, self-contained selector (`.bar` rather than `.hamburgerBtn .bar`) inside the file that actually renders the element (`Icons.module.css`), not left nested under the parent's class in the parent's file — that nesting was only ever namespacing, never a real dependency on the parent, and keeping it cross-file risks a circular import (parent imports the icon component, icon component imports the parent's styles).
- **One exception to "every component imports its own module file only":** a raw color literal (not a theme token) that would otherwise be copy-pasted verbatim across three or more component module files (e.g. `#fffdf6` used as button/text color in `Sidebar`, `ChatMessages`, and `Composer`) is hoisted once as a `:root` custom property in `src/styles/index.css` — the app's single global, non-module stylesheet, imported once in `main.jsx` — and referenced from each module file as `var(--color-warm-white)`. This is for literal, theme-independent constants only; the light/dark, zone-scoped design tokens (`--bg-base`, `--accent-ochre`, …) always stay declared per-zone as described above, never in `index.css`.

## Premium Feel Guidelines

- **Typography**: pair a refined serif or humanist display face for headings (evokes manuscript/legal-text gravitas) with a clean sans for body/UI text. Generous line-height, no cramped text blocks.
- **Spacing**: generous padding inside neumorphic cards (24–32px) — cramped soft-UI looks cheap, breathing room looks premium.
- **Iconography**: line icons with consistent stroke weight, tinted `--accent-ochre` or `--accent-green` rather than flat black.
- **Motion**: subtle, slow transitions (200–300ms ease) on hover/press shadow shifts — no bouncy/playful easing, which undercuts the legal/regulatory tone.
- **Jurisdiction color coding**: use `--accent-ochre` for National (India) content and `--accent-green` for International content consistently across badges, tags, and section headers, per the dual-jurisdiction-isolation requirement in the product spec — this doubles as a UX cue and reinforces the palette logic.
- **Never** default to generic SaaS blue/purple gradients or flat Tailwind default palette colors — every color used must trace back to the ochre/green tokens above (tints/shades of them are fine, unrelated hues are not).
