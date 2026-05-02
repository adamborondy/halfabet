# halfabet — project brief

## Concept

halfabet is a daily word game. Each day every player gets the same 13 letters (half the 26-letter alphabet), chosen by a seeded random draw based on the date. Players have 120 seconds to find as many valid words as possible using only those letters. The twist is scoring: rare words score big, common words barely register. The goal is not just quantity but vocabulary depth.

Tagline: *Find words using half the alphabet and 120 seconds on the clock. Rare finds score big, common ones barely register. Same halfabet for everyone, different scores.*

---

## Files

- `index.html` — landing page (logo animation, Play button)
- `game.html` — the game itself (all logic + UI in one file, no build step)
- `data/words.json` — dictionary: `{ "word": frequencyScore }` where frequency is 0–100 (100 = most common)

---

## Technical architecture

### Stack
- Vanilla HTML/CSS/JS, no framework, no bundler
- Fonts: **Syne** (headings, UI) + **DM Mono** (tiles, numbers, monospace elements)
- Hosted as static files; deployed from `main` branch

### Daily seed
```js
function dailySeed() {
  const d = new Date();
  const s = `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;
  let h = 2166136261; // FNV-1a
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = (h * 16777619) >>> 0;
  }
  return h;
}
```
Then shuffled with **mulberry32** PRNG, first 13 letters taken. Same output for every player on the same day.

### Scoring
```js
const score = Math.round(Math.sqrt(100 - frequency) * 10);
```
- `frequency` comes from `words.json` (0 = rarest, 100 = most common)
- Score is inverted: rarest word → score ~100, most common → score ~0
- Sqrt curve means ~5 common words ≈ 1 rare word — avoids punishing volume

### Rarity labels
| Score | Label |
|-------|-------|
| 90–100 | very rare |
| 70–89 | rare |
| 50–69 | uncommon |
| 30–49 | moderate |
| 10–29 | common |
| 0–9 | everyday |

### Game states
`'idle'` → `'playing'` → `'ended'`

---

## Design system

### Colors
```css
--bg: #0e0e0e        /* near-black background */
--fg: #f8f6f2        /* warm off-white text */
--fg-dim: #888       /* secondary labels */
--fg-dimmer: #333    /* inactive tiles, borders */
--accent: #c8f060    /* lime green — active tiles, scores, CTA */
--error: #ff5f5f     /* invalid input, timer urgent */
--panel: #161616     /* input background */
--border: #222       /* tile and panel borders */
```

### Logo
Three-span structure: `half` (accent color) + vertical divider (1.5px, accent) + `abet` (white). On mobile (≤480px) the logo stacks vertically with a horizontal divider instead.

```html
<span class="logo-a">half</span>
<span class="logo-div"></span>
<span class="logo-b">abet</span>
```

### UI sections (top to bottom in game.html)
1. **Header** — logo left, stats (time / words / score) + start/play-again button right. Stats hidden until game starts.
2. **Tagline** — DM Mono, dimmed, `<strong>` highlights in white
3. **Today's letters** — 26 tiles, active ones (accent) vs inactive (dimmed)
4. **Enter a word** — text input + submit button; input turns red/green as you type
5. **Rarity map** — horizontal bar 0–100, dot per found word with hover tooltip
6. **Words found** — list sorted by score descending; each row: word, bar fill, score, rarity label

### Tile flash
When a word is accepted, its unique letters briefly flash (lime highlight, 500ms) to connect letters to words visually.

### Responsive
- ≤600px: smaller tiles, condensed input/button padding, rarity column hidden
- ≤480px: logo stacks vertically, start/play-again button smaller

---

## Feedback messages

| Situation | Message |
|-----------|---------|
| Letter not in set | `"x" is not in your halfabet` |
| Already used | `already submitted` |
| Not in dictionary | `not a recognised word` |
| Valid word | `word · rarity · N points` |

Timer turns red (`--error`) when ≤10 seconds remain. End of game: feedback cleared, "↺ Play again" button appears, stats remain visible.

---

## Brainstorming / ideas not yet built

### Competitive / social
- **Share result** — one-tap copy of emoji grid showing score breakdown (like Wordle)
- **Leaderboard** — daily scores per halfabet, needs backend
- **Streak tracking** — localStorage streak counter (days played in a row)
- **Challenge a friend** — share link with same daily seed, compare scores async

### Gameplay variations
- **Hard mode** — only 10 letters, shorter time
- **Bonus round** — after time's up, one free guess with any letter (costs half score)
- **Letter hints** — spending points to reveal which letters are in today's set before starting (pre-game meta layer)
- **Word of the day** — highlight the rarest word found across all players

### UI / polish
- **Post-game summary screen** — "You found N words, best was X (very rare, top 5%)"
- **Score history chart** — past 7 days of scores via localStorage
- **Keyboard shortcut hints** — Enter to submit, already works but could be surfaced
- **Haptics on mobile** — navigator.vibrate() on valid/invalid submit
- **Sound design** — subtle click on tile flash, success chime on rare word

### Content
- Expand `words.json` — currently covers common English; could add proper nouns toggle, British spellings
- Frequency data source — current file is curated; could cross-reference against a corpus (e.g. Google Books Ngrams)
