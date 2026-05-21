# Stitch Design System Extracted

The supplied Stitch HTML is the F1 visual source of truth. The frontend keeps the same clean grey/black surface-based dashboard style, Inter typography, Material Symbols icons, and Tailwind token names.

## Color Tokens

Core tokens:

- `background`: `#f7f9fb`
- `surface`: `#f7f9fb`
- `surface-bright`: `#f7f9fb`
- `surface-container-lowest`: `#ffffff`
- `surface-container-low`: `#f2f4f6`
- `surface-container`: `#eceef0`
- `surface-container-high`: `#e6e8ea`
- `surface-container-highest`: `#e0e3e5`
- `surface-variant`: `#e0e3e5`
- `primary`: `#1a1a1a`
- `primary-container`: `#2f2f2f`
- `on-primary`: `#ffffff`
- `on-surface`: `#191c1e`
- `on-background`: `#191c1e`
- `on-surface-variant`: `#444748`
- `secondary`: `#505f76`
- `secondary-container`: `#d0e1fb`
- `secondary-fixed`: `#d3e4fe`
- `outline`: `#747878`
- `outline-variant`: `#c4c7c7`
- `error`: `#ba1a1a`
- `error-container`: `#ffdad6`

Semantic extras used in mock UI:

- High priority dot: `#10b981`
- Medium priority dot: `#f59e0b`
- Low priority dot: `#ef4444`

## Typography

- Font family: `Inter`
- Icon font: `Material Symbols Outlined`
- Display: `32px / 40px`, weight `600`
- Headline medium: `24px / 32px`, weight `600`
- Headline small: `20px / 28px`, weight `500`
- Body large: `16px / 24px`, weight `400`
- Body medium: `14px / 20px`, weight `400`
- Label medium: `12px / 16px`, weight `500`
- Label small: `11px / 14px`, weight `600`

## Spacing

- Base unit: `4px`
- `xs`: `4px`
- `sm`: `8px`
- `md`: `16px`
- `gutter`: `16px`
- `lg`: `24px`
- `xl`: `32px`
- Mobile margin: `16px`
- Desktop margin: `32px`

## Radius

- Default: `4px`
- Large: `8px`
- XL: `12px`
- Full: `9999px`

## Shadows

Ambient card shadow:

```css
0 4px 24px -4px rgba(0,0,0,0.03), 0 2px 8px -2px rgba(0,0,0,0.02)
```

Hover:

```css
0 8px 32px -8px rgba(0,0,0,0.06), 0 4px 12px -4px rgba(0,0,0,0.04)
```

## Component Styles

- Cards: `surface-container-lowest`, `rounded-xl`, subtle ambient shadow, `border surface-variant` where table/drawer needs framing.
- Sidebar: fixed desktop rail, `surface-container-low`, right border, active item uses left border and `surface-container-high`.
- Topbar: sticky top bar, `surface`, 64px height, compact icon buttons.
- Buttons: dark primary container for primary actions, surface-container low with outline for secondary actions.
- Table: sticky header, surface-low header band, rows separated by `surface-variant`, selected row uses `surface-container`.
- Drawer: right side panel, `surface-container-lowest`, border, rounded XL, internal sticky header/footer.
- Badges: compact label text, small radius, semantic background from surface/secondary tokens.
- Mobile nav: bottom fixed rail using the same nav icons and selected pill treatment.

## UX Corrections Applied

- Users are Minjian and Chang.
- `New` discovery badge becomes `New in this run`.
- `Seen` discovery badge becomes `Seen before`.
- Status remains separate from discovery.
- `New Alert` is replaced with `Run Fetch`.
- Logout is removed because there is no authentication.
- Munich mock data is replaced with Berlin/Potsdam/Remote-focused data.
- Codex actions are described as manual prepare/import flows, not direct AI calls.
