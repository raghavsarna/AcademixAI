---
name: AcademixAI
description: What changed in AI research today, drawn as a metro map, with every paper explained at your level.
colors:
  ground: "#ffffff"
  panel: "#f2f3f4"
  rule: "#d8dadd"
  rule-strong: "#9a9ea5"
  ink: "#141518"
  ink-soft: "#575b62"
  band: "#16171a"
  band-soft: "#b9bcc1"
  signal: "#ffd23f"
  depth-plain: "#fff1b8"
  depth-student: "#ffd23f"
  depth-expert: "#16171a"
  link: "#0a5bd1"
  danger: "#b4232a"
  line-language: "#d42a2f"
  line-vision: "#0a5bd1"
  line-learning: "#00804a"
  line-agents: "#f47a2a"
  line-robotics: "#7d3bb0"
  line-other: "#7f6244"
typography:
  display:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "3.5rem"
    fontWeight: 800
    lineHeight: 0.98
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "3.25rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  sign:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.33
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.375
  body-lead:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.125rem"
    fontWeight: 400
    lineHeight: 1.625
  body:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.65
  label:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    lineHeight: 1.43
  station-name:
    fontFamily: "Archivo, ui-sans-serif, system-ui, sans-serif"
    fontSize: "16px"
    fontWeight: 700
    letterSpacing: "0.01em"
    fontVariation: "'wdth' 78"
rounded:
  hairline: "2px"
  code: "3px"
  sign: "4px"
  switch: "6px"
  transfer: "10px"
  full: "9999px"
spacing:
  gutter: "20px"
  gutter-wide: "32px"
  band-y: "14px"
  band-x: "24px"
  board: "24px"
  entry-y: "32px"
  section: "64px"
  section-end: "80px"
components:
  button-primary:
    backgroundColor: "{colors.band}"
    textColor: "{colors.ground}"
    typography: "{typography.body-lead}"
    rounded: "{rounded.sign}"
    padding: "14px 24px"
  button-primary-hover:
    backgroundColor: "{colors.ink}"
  button-secondary:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sign}"
    padding: "14px 24px"
  button-secondary-hover:
    backgroundColor: "{colors.panel}"
  button-on-band:
    backgroundColor: "{colors.signal}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sign}"
    padding: "14px 24px"
  button-on-band-hover:
    backgroundColor: "{colors.ground}"
  sign-band:
    backgroundColor: "{colors.band}"
    textColor: "{colors.ground}"
    typography: "{typography.sign}"
    padding: "14px 24px"
  station-board:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.ink}"
    padding: "{spacing.board}"
  transfer-sign:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.transfer}"
    padding: "4px 12px"
  depth-tab:
    textColor: "{colors.ink-soft}"
    rounded: "{rounded.sign}"
    height: "40px"
    padding: "0 18px"
  depth-tab-selected:
    backgroundColor: "{colors.band}"
    textColor: "{colors.ground}"
  input:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.sign}"
    padding: "10px 14px"
  suggestion-chip:
    backgroundColor: "{colors.ground}"
    textColor: "{colors.ink}"
    rounded: "{rounded.full}"
    padding: "6px 14px"
  line-bullet-md:
    rounded: "{rounded.full}"
    size: "28px"
---

# Design System: AcademixAI

## Overview

**Creative North Star: "The Transit Map"**

The field of AI is drawn as a metro system. Each research area is a line with a fixed colour, each day's papers are newly opened stations ranked left to right, and a paper cross-listed on two areas is an interchange. The whole interface borrows the grammar of transit signage: a white ground, near-black ink, black signage bands with white type naming every section, round line bullets, white station ticks and capsules, and geometry that turns only at 45 and 90 degrees.

The system is flat and plain on purpose. Depth comes from tone (black band, grey board, white ground) and from heavy rules, never from shadows. Colour carries meaning, not mood: the six line colours identify research areas and nothing else, signal yellow marks where you are, and link blue marks where you can go. Type is one family, Archivo, set heavy and tight for headlines and condensed on its width axis for anything that names a station or a line.

There is one authored motion moment: the lines draw in, then the stations open. Everything else changes state in 150 to 250ms or, for readers who ask for less motion, instantly.

**Key Characteristics:**
- White ground, black signage bands with white Archivo type naming each section.
- Six line colours with fixed meanings; a line colour never decorates.
- Signal yellow marks the current location only.
- Panel grey is the station-board surface.
- White capsules mark interchanges; white rings mark stations.
- No shadows, no gradients; depth is tonal.
- One motion moment: lines draw, then stations open.

## Colors

A neutral signage palette (white, greys, near-black) carrying six saturated line colours whose meanings never change, plus one signal yellow and one link blue.

### Primary
- **Signage Black** (band): the black band behind every section name, the masthead, footer, closing call-to-action band, primary buttons, the selected depth tab, and the 6px top edge of every board. It is the system's voice.
- **Signal Yellow** (signal): the "you are here" colour. It rings the open station on the map, outlines the current station on the station rail, underlines the active masthead link, fills the current stage of the upload progress, backs the skip link, and is the text-selection colour.

### Secondary
- **Route Blue** (link): every inline link and the "Read it at your level" action, the keyboard focus ring on white (3px, offset 2px; on black signage the ring is signal yellow), the focused input border, and the text caret. It is the same value as the Vision line, which is acceptable because links are always underlined text and the Vision line is always a stroke or bullet.

### Tertiary: the research lines
Each line colour is bound to one research area and carries text in the colour named in parens. They appear only as map strokes, route bullets, strip-map spines and rail segments.
- **Language Red** (line-language, white text): cs.CL. Bullet "L".
- **Vision Blue** (line-vision, white text): cs.CV, eess.IV. Bullet "V".
- **Learning Green** (line-learning, white text): cs.LG, stat.ML, cs.NE. Bullet "M".
- **Agents Orange** (line-agents, ink text): cs.AI, cs.MA. Line name "Agents & reasoning". Bullet "A".
- **Robotics Purple** (line-robotics, white text): cs.RO. Bullet "R".
- **Other Brown** (line-other, white text): every other category. Line name "Other fields". Bullet "X".

The canonical track order is Language, Vision, Learning, Agents, Robotics, Other; the map may reorder tracks only to keep interchanging lines adjacent, preferring the canonical order on ties.

### Neutral
- **Signage White** (ground): the page, station rings, interchange capsules, inputs, transfer signs and the label halo on the map.
- **Board Grey** (panel): the station board under the map and the "What changed" board on the paper page. Also used, never as a standing surface, for hover washes (secondary button, timetable rows, drop zone), skeleton fills and inline code.
- **Hairline Grey** (rule): row dividers, card outlines (depth demo, chat, empty library), the depth switch border.
- **Strong Rule Grey** (rule-strong): input and secondary-control borders, the rule above through-lines and the paper sidebar, the dashed drop zone, the scrollbar thumb.
- **Ink** (ink): body text, station ring and capsule strokes, transfer-sign borders, hover state of black buttons.
- **Soft Ink** (ink-soft): meta lines, secondary paragraphs, rank numerals, placeholders, unselected depth tabs.
- **Band Soft** (band-soft): secondary text and inactive navigation on black bands.
- **Danger Red** (danger): error messages (role alert), invalid input borders and the edge of a failed upload card.

### Reading depth
Depth runs light to dark: the deeper the reading, the darker the sign. **Plain** is pale yellow (`depth-plain`), **Student** is signal yellow (`depth-student`), **Expert** is black (`depth-expert`, white type). These fill the header of each depth card in "One paper, three readers" and the depth chips; they never colour a line, a button or a link.

### The livery
All six line colours in their fixed order, as one stripe (`.livery-x`, `.livery-y`). It stands for the whole network, so it carries no single line's meaning: it is the track of the "How each edition is made" strip, and nowhere else. The masthead has no stripe under it. Never break it up or reorder it.

### Named Rules
**The Fixed Line Rule.** A line colour means one research area everywhere: on the map, in bullets, on the rail, in the footer legend. Never use a line colour for a button, a heading, an illustration or a state.

**The You-Are-Here Rule.** Signal yellow marks the current location: the open station, the current rail station, the active nav item, the current stage of an upload, selected text, the skip link. Beyond wayfinding it appears as the Student depth, the upload drop zone's badge, and one large surface: the closing call to action on the landing page, a yellow platform sign with a black button. Do not add more yellow surfaces.

**The Board Rule.** Panel grey as a standing surface belongs to boards: the station board and the "What changed" board, each topped by a 6px black edge. Elsewhere it appears only transiently (hover, loading).

## Typography

**Display Font:** Archivo (variable, with the `wdth` axis), falling back to ui-sans-serif and system-ui
**Body Font:** Archivo
**Label/Mono Font:** Archivo condensed to 78% width (the signage setting); no monospace face beyond the browser default for inline code

**Character:** One grotesque doing every job, the way a transit authority uses one typeface. Headlines are extra-bold and tightly tracked; station and line names are condensed like platform signs; reading text is open and calm.

### Hierarchy
- **Display** (800, 2.75rem phone, 3.5rem at 640px, 3.875rem at 1280px; line-height 0.98; -0.035em): the landing headline only, capped at 17ch.
- **Headline** (800, 2.25rem rising to 3.25rem at 640px; line-height 1.05; -0.03em): page titles (edition headline, Explain a paper, All editions, not found). Paper titles use the same voice one step smaller (2rem to 2.75rem, line-height 1.08).
- **Sign** (700, 1.25rem rising to 1.5rem; -0.01em): the title inside every black signage band.
- **Title** (700, 1.25rem to 1.375rem, line-height 1.375): station entry titles, board titles, card titles. Prose h2 inside explanations is 1.25rem, h3 1.0625rem, both line-height 1.25.
- **Body lead** (400, 1.125rem, line-height 1.625): intros and section standfirsts, capped at 60ch.
- **Body** (400, 1.0625rem, line-height 1.65): the explanation reading column, 60ch measure, 0.9em between blocks. The "what changed" sentence is set at this size in weight 500.
- **Label** (600, 0.875rem): meta lines joined by middle dots ("New method · Agents & reasoning + Language · arXiv 2511.01234"), sidebar fact labels (700), table headers (700). Navigation and depth tabs use 0.9375rem.
- **Station name** (700, 16px on the map, 0.9375rem on the rail; condensed to 78% width, +0.01em): station labels, line names beside bullets, pipeline stop names.
- **Rank numeral** (800, 1.875rem to 2.25rem, tabular, soft ink): the station number beside each entry.

### Named Rules
**The Whole Name Rule.** A sign shows a whole name. Station names are authored short names, or a title cut at a word boundary (24 characters on the map) that never ends on a joining word; they wrap to at most two lines and are never truncated with an ellipsis.

**The Tabular Count Rule.** Dates, counts and rank numerals use tabular figures.

**The No Kicker Rule.** A heading stands alone; nothing small and uppercase sits above it. Context goes in a meta line below the title or in the band beside it.

## Layout

One centred container (max 88rem) with a 20px gutter on phones and 32px from 640px. Sections are introduced by a signage band that bleeds out across the gutter, so its title starts on the same line as the content below it (the **Aligned Sign Rule**: band text, table columns and panel text all share the content edge; a panel that sits under a band, such as the chat or the "What changed" board, bleeds by the same amount) and spaced 64px apart (80px at the end of landing sections). Reading text is held to a 60ch measure everywhere, including the station board summary and through-line notes.

Responsive behaviour uses Tailwind's default breakpoints. Below 768px the metro diagram, its station board and legend are replaced by a vertical strip map (one station per paper, a 10px spine in the paper's primary line colour). From 1024px the edition list gains a 17rem sticky station rail on the right, the station board becomes three columns (title, summary, action), and the paper page becomes a 40rem article beside an 18rem sticky sidebar. Tables (the edition timetable) collapse to stacked rows below 640px.

Vertical rhythm inside components: 14px band padding, 20 to 24px board padding, 32px between station entries separated by hairline rules, 16 to 24px between a heading and its first paragraph.

## Elevation & Depth

The system has no shadows anywhere. Depth is tonal and structural: black bands sit at the top of the hierarchy, panel-grey boards sit one step below with a 6px black top edge, and everything else lies flat on white separated by hairline or strong rules. The open station board is tied to its station by a 10px black notch that slides along the board's top edge.

### Named Rules
**The Flat Signage Rule.** Nothing floats. If something needs emphasis, give it a black band, a black top edge or a heavier rule, never a shadow.

## Shapes

Signage corners: buttons, inputs, tabs and chat bubbles use a 4px corner; the depth switch track and drop zone 6px; transfer signs 10px; suggested questions and line bullets are fully round. Bands and boards are square.

The map's forms are fixed. Lines are 13-unit strokes with round caps and joins, running horizontally and bending only at 45 degrees. A station is a white ring (radius 10, 4-unit ink stroke). An interchange is a white capsule spanning both tracks (24 units wide, fully rounded, 4-unit ink stroke); where the lines cannot run side by side, two rings joined by a 3-unit ink link mark an out-of-station interchange. Route bullets are filled circles in the line colour with the line letter in bold. The same ring and capsule shapes recur at smaller sizes on the strip map, the station rail and the pipeline strip.

## Components

### Buttons
- **Shape:** signage corner (4px).
- **Primary:** black band fill, white bold type, 14px by 24px at the large size (lg type) or 10px by 16 to 20px in compact contexts. Hover deepens to ink in 150ms.
- **Secondary:** white with a 2px black border, ink type; hover washes to panel grey. Compact secondary actions (Log in, edition prev/next) use a 1px strong-rule border that turns ink on hover.
- **On a black band:** signal-yellow fill, ink type; hover turns white. One per band.
- **Disabled:** 50% opacity, not-allowed cursor.
- **Text actions:** link blue, weight 600, underlined (offset 0.22em, 1.5px thickness). "Read it at your level" is the canonical wording for opening a paper.

### Signage Band
Black bar, white sign-type title on the left, optional supporting content right-aligned on the right (band-soft text, a depth switch, a link underlined in signal). It bleeds across the page gutter so its title lines up with the content edge; `split` sets the title and its text in the hero's two columns, so the day's headline sits under the hero description. A band heading a standalone bordered panel ("What you get back") stays inside the panel with the same inset. Use it to name every major section and the chat panel. It is the only section-heading device.

### Route Bullet
A round bullet in the line colour carrying the line letter: 20px (labels, legend, footer), 28px (entries, board), 40px. With a label, the line name follows in condensed type. Stack two bullets for an interchange paper.

### Metro Diagram (signature)
An SVG drawn from the real edition by the metro layout: tracks 54 units apart, stations evenly spaced and ranked left to right, the secondary line of an interchange bending at 45 degrees to run 18 units beside the primary through the capsule, then bending back. Labels are condensed bold, haloed in white, and placed above or below whichever collides least. Hovering or focusing a station opens it: a 6-unit signal-yellow ring surrounds it and the station board below updates (aria-live polite). Line bullets sit at the left terminal. A legend of the lines in use and one sentence explaining the capsule sits beneath. Shown from 768px.

### Station Board
Panel grey, 6px black top edge, a sliding black notch pointing at the open station. Holds bullets with "Station n of N", the full title, a meta line, the what-changed summary (60ch) and "Read it at your level". The same board style is the "What changed" board on the paper page. Use it for nothing else.

### Strip Map and Station Rail
The phone form of the map is a vertical strip: spine in the primary line colour, ring or capsule per station, full title and summary beside it. On desktop edition pages a sticky station rail lists every station by name in condensed type with a 6px spine; the station in view is bold with a signal outline and `aria-current="location"`.

### Station Entry
A two-column listing: rank numeral and bullets on the left; title, meta line, the what-changed sentence (weight 500), why it matters (soft ink), transfers, and two text actions on the right. Entries are separated by hairline rules.

### Transfer Sign
Earlier work a paper connects to, after a bold "Transfers" label: white sign, 2.5px ink border, 10px corners, relation in soft ink then the work in semibold.

### Depth Switch
A segmented tablist (Plain, Student, Expert) with a sliding pill: 4px-padded track with a 6px corner and hairline border, 40px tabs with 4px corners, bold 0.9375rem labels. Light tone: panel track, black pill, white selected label. Inside a black band: dark track (#2a2c31), white pill, ink selected label. Arrow keys move between depths. The explanation below settles in (250ms opacity and blur) when the depth changes.

### Inputs / Fields
- **Style:** white, 1px strong-rule border, 4px corner, 10px by 14px padding, soft-ink placeholder, label above in weight 600.
- **Focus:** border turns link blue plus the global 3px blue focus ring.
- **Error / Disabled:** danger border via `aria-invalid`; disabled at 60% opacity.
- **Drop zone:** 2.5px dashed strong-rule border, 6px corner, 48px vertical padding; hover turns the border ink over panel grey, dragging turns it link blue over a pale blue tint.

### Chips
Suggested questions are fully round, white, 1px strong-rule border, label type; hover border turns ink.

### Chat Panel
A signage band ("Ask about this paper") over a hairline-bordered body. Reader messages are black 4px bubbles with white text (46ch); replies are white bordered bubbles set in the reading column. Signed-out readers see a short reason and primary/secondary account buttons in place of the form. On a paper, replies stream in with a blinking ink caret (static under reduced motion). Citations are small superscript link-blue numbers; each opens its passage in a "From the paper" list under the reply: a signal-yellow number chip, the section and page, and the passage set as a quotation with a 4px signal rule. Only cited passages are listed.

### Navigation
The masthead is a black band holding the wordmark (two lines meeting at a capsule), three links in 0.9375rem semibold band-soft type, and account actions on the right. The active link is white with a 3px signal underline 10px below. On phones the links wrap to a horizontally scrolling full-width row. A skip link appears on focus in signal yellow.

### Edition Timetable
Editions as a table: black-band or 2px-black-ruled header, date, the day's biggest change in bold, tabular counts right-aligned; rows wash to panel on hover. Stacks to rows on phones.

### Pipeline Strip
How an edition is made, as a single black line with four white rings (4px black border) and condensed stop names; horizontal from 768px, vertical below.

### Motion
- **Draw the lines:** each map line draws in over 1100ms on the expo-out curve, staggered 90ms per line.
- **Open the stations:** each station scales from 40% and fades in over 520ms, starting at 500ms and staggered 70ms per station.
- **State changes:** colour transitions 150ms; the depth pill and the board notch slide 250ms on the smooth-out curve.
- **Reduced motion:** content is visible by default and only animates under `prefers-reduced-motion: no-preference`; under `reduce`, every animation and transition is collapsed to effectively zero and skeleton pulses stop.

### Accessibility
- Focus is always visible: a 3px outline, 2px offset, on every interactive element, link blue on white and signal yellow inside black signage (masthead, bands, footer); map station labels also underline on keyboard focus.
- The map is an SVG group with a spoken summary; each station is a link labelled with rank and full title, and the station board announces changes politely.
- Line bullets are labelled by line name; decorative rings, spines and notches are hidden from assistive tech.
- Depth switch is a proper tablist with roving tab index and arrow-key movement; the explanation is its tabpanel.
- Errors use `role="alert"`, progress uses `role="status"`, inputs have visible labels and hints tied by `aria-describedby`.

## Do's and Don'ts

### Do:
- **Do** name every major section with a black signage band carrying a white Archivo title.
- **Do** keep each line colour bound to its research area and its fixed bullet letter (L, V, M, A, R, X).
- **Do** use signal yellow only to mark the current location, plus at most one action inside a black band.
- **Do** draw map geometry at 45 and 90 degrees only, with white rings for stations and white capsules for interchanges.
- **Do** set station and line names in the condensed signage setting (78% width) and show them whole, wrapped to at most two lines.
- **Do** keep reading text to a 60ch measure.
- **Do** gate every animation behind `prefers-reduced-motion: no-preference` and keep the one authored moment (lines draw, stations open) as the only choreography.
- **Do** use stroke SVG icons (Lucide) at 16 to 32px, hidden from assistive tech, when an icon is needed.

### Don't:
- **Don't** put an eyebrow or kicker (small uppercase label) above a heading.
- **Don't** use unicode glyphs as icons (arrows, check marks, stars, bullets).
- **Don't** truncate a station name with an ellipsis.
- **Don't** use a line colour for anything but its line, or add a seventh line colour.
- **Don't** use signal yellow as decoration, a highlight wash or a general accent.
- **Don't** use panel grey as a general card background; it belongs to boards.
- **Don't** add shadows, gradients or glass; depth is tonal.
- **Don't** add a hero with feature cards or a newsletter sign-up box.
