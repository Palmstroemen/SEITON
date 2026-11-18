# Scope and SunTree - Colour Inventory

Made 2026-11-15 for "Colours: Follow the System" (Designdocument Setup.md, 5). Nothing is built
yet. The question: which of today's colours are base values, which can be worked out from them,
and which stay fixed on purpose.

## 1. What there is today

- `core/schemes/dark.json` and `light.json`: 79 names each, 48 for Scope (list, rows, setup,
  dialogs) and 31 for SunTree and the small crown (`crown…`, `stem…`, `notice…`, `lens…`).
- Derived already: `textMuted` and `textSoft` (text 13 % and 7 % towards the background,
  `apps/Scope/main.qml`), text on a project's colour (black or white by contrast), the CWD mark
  (`FBUtils.cwdMarkColor`), the middle of the FilesPanel (`filesPanelCenter` with 52 % of the
  project colour, `FilesPanel.qml` `centerTintMix`).
- Eleven colours can be set on General (window background, text; files area; selected files,
  dropping, lens frame; projects row, MyOS folders row, path bar, folders, current folder).
- Outside the schemes, written into the QML: tag colours and their menu, signal reds
  (`#e53935`, `#d64f4f`), the ACL chips (greys), the lines of the small crown, the shadow under
  the folder row, defaults in `FolderItem.qml` (always given from outside? to check).

## 2. What the numbers show (OKLCH)

Converted to lightness L, chroma C and hue h, the 79 colours turn out to be far fewer:

- **A hidden blue tint.** Almost every surface, border and text has hue 260–275 at low chroma
  (0.01–0.06). That is one tint of today's schemes, written out 60 times. The exceptions are
  neutral grey: the three folder row tints, `filesPanelCenter`, dark `text`, the ACL dialogs.
- **A ladder of lightness.** Surfaces lie at fixed steps from the background towards the text:
  `panelAlt`, `panel`, `pill`, `smallButtonBg` … with a border about 0.08 above each. In Dark the
  steps are two to three times as large as in Light (`pill`: +0.14 in Dark, −0.05 in Light).
- **Three hue families of their own.** Teal (h 215–246) for what is the system's: the crown's
  system folders, the lens levels in SunTree. Amber (h 58–80) for the lens: its frame, the "take
  off" button. Red (h 24) for errors. These carry meaning and do not follow the tint.
- **Duplicates.** 79 names, 71 values in Dark, 69 in Light. `setupPill` = `stemClipboard` =
  `noticeUndo`, `setupText` = `stemClipboardText` = `noticeText`, and more.
- **Dialogs are the scheme turned over.** `dialog…` is the light ladder in Dark and the dark one in
  Light (on purpose, 2026-11-06). The ACL dialogs do not join in: neutral grey, the same in both.
- **The notice after a drop is dark in both** (on purpose, it must stand out on a light desktop).
- **Selection and dropping are the same in both:** see-through grey-blue and a strong blue at 50 %,
  both of the hidden tint's hue.

## 3. The proposal: base values, rules, fixed

### Base values

| Base value | System | Scheme of one's own |
|---|---|---|
| background | `QPalette.Window` | set |
| text | `QPalette.WindowText` | set |
| content background (lists, cards) | `QPalette.Base` | set |
| accent | `QPalette.Accent`, else `Highlight` | set |
| room | the project's colour | the project's colour |
| tint | none: neutral as the system's greys | hue and chroma, may be none (today's Dark and Light: their blue) |

Light or dark is not a base value: it follows from background and text (Designdocument Setup.md,
5, checked 2026-11-15).

### Rules (in OKLCH; "up" means from the background towards the text)

| Family | Today's names | Rule |
|---|---|---|
| tint | all surfaces, borders, texts | the tint base value; under "System" none |
| surfaces | `panelAlt`, `panel`, `pill`, `smallButtonBg`, `setupPanel…`, `setupPill`, `stemPreviewBack`, `stemFolder`, `crownBackOwn` | background, n steps up; a step in Dark about 2.5 times one in Light |
| content | `card` | content background |
| borders | `…Border` of each surface | its surface, one step (about 0.08) up |
| side texts | `smallButtonText`, `setupMuted`, `stemSubText`, `dialogTextMuted`, `…Placeholder` | text, a share towards the background (as `textMuted` today) |
| active, selected | `accentSecondary`, `smallButtonActive…`, `stemCurrent…`, `crownFolderOwn` | accent at low chroma (about 0.06), lightness from the ladder |
| what SEITON brings | `crownFolderSystem`, `crownBackSystem`, `lensLevel…` | the accent turned by a fixed angle (today 268 → about 224, so about −45°), lightness from the ladder |
| hover | `…Hover` | its colour, one step up |
| selection, dropping | `fileSelection…`, `selectionBox…`, `dropHighlight` | accent, see-through as today; dropping at full chroma |
| text on a colour | `accentPrimaryText`, text on projects | black or white by contrast (as today) |
| overlays | `stemTint`, `crownFolderLine`, `crownEmbryoLine` | background or text with opacity |
| dialogs | `dialog…`, `aclDialog…` | the same rules with background and text swapped, tinted; the ACL dialogs join in |
| notice | `notice…` | the same rules on a dark ladder, always |
| folder rows | `folderPathTint`, `folderCwpTint`, `folderULineTint` | background, three steps up, in the room's hue |
| room | `filesPanelCenter`, frame of the FilesPanel, `projectButtonActive` | content background mixed with the room; the share is the new slider (instead of 52 %); the P button in the room's colour |

### Fixed on purpose

| What | Why |
|---|---|
| amber of the lens (`lensFrame`, `lensOff…`) | a signal: one wears a lens; hue fixed, lightness from the ladder |
| red of errors (`dialogError`, signal reds in the QML) | a signal |
| tag colours and their menu, ACL chips | the user's own data, look the same everywhere |
| lines of the small crown | each slider's mark has the same colour |

So from 79 names come 5 base values (6 with the tint of one's own scheme), 2 fixed hues and
about a dozen rules. One's own schemes
set the base values and may still overwrite each name, as the eleven boxes do today.

### The test that tells whether the rules are right

With today's base values (Dark: background `#0f1014`, text `#e6e6e6`, accent of hue 268) the rules
must give back today's `dark.json` closely enough that one sees no difference, and the same for
Light. Where they do not, either the rule is wrong or the old colour was a slip (`text` in Dark
is the only neutral text, for example).

## 4. Decided (2026-11-15)

1. **No tint under "System":** the surfaces are as neutral as the system's greys. A scheme of one's
   own may have a tint (today's Dark and Light keep their blue).
2. **What SEITON brings is worked out from the accent** (turned by a fixed angle), not a fixed
   teal. The lens's amber and the red of errors stay fixed.
3. **The ACL dialogs join the other dialogs:** turned over and tinted.
4. **The P button takes the colour of the room.**
