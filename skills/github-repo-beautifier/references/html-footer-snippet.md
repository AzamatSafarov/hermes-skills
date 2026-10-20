# HTML Footer for Visualizations

> Copy into every HTML artifact: timelines, diagrams, interactive pages.

## Basic variant (minimalist, dark theme)

```html
<!-- Authorship -->
<div style="position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:10;
  color:#444460;font-size:11px;letter-spacing:0.5px;font-family:'Segoe UI',system-ui,sans-serif;
  pointer-events:none;">
  Built by <span style="color:#7c83fd">AUTHOR_NAME</span> ·
  <a href="https://github.com/OWNER/REPO" style="color:#666680;text-decoration:none;pointer-events:auto;">REPO</a>
</div>
```

## Extended variant (with multiple links)

```html
<div id="author" style="position:fixed;bottom:12px;left:50%;transform:translateX(-50%);z-index:10;
  color:#444460;font-size:11px;letter-spacing:0.5px;font-family:'Segoe UI',system-ui,sans-serif;
  pointer-events:none;text-align:center;">
  Built by <a href="https://github.com/OWNER" style="color:#7c83fd;text-decoration:none;pointer-events:auto;">AUTHOR_NAME</a> ·
  <a href="https://github.com/OWNER/REPO1" style="color:#666680;text-decoration:none;pointer-events:auto;">REPO1</a> ·
  <a href="https://github.com/OWNER/REPO2" style="color:#666680;text-decoration:none;pointer-events:auto;">REPO2</a>
</div>
```

## Rules

1. **position: fixed; bottom: 12px** — always pinned to bottom, does not scroll
2. **left: 50%; transform: translateX(-50%)** — perfect centering
3. **z-index: 10** — above canvas/graph, but below tooltip (z-index: 100)
4. **color: #444460** — muted, does not distract from content
5. **pointer-events: none** on container, **pointer-events: auto** on links — only links are clickable
6. **Accent color for name** — `#7c83fd` (violet) or `#58a6ff` (GitHub blue)

## CSS variant (if using stylesheet)

```css
#author {
  position: fixed;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10;
  color: #444460;
  font-size: 11px;
  letter-spacing: 0.5px;
  pointer-events: none;
  text-align: center;
}
#author a {
  color: #666680;
  text-decoration: none;
  pointer-events: auto;
  transition: color 0.2s;
}
#author a:hover { color: #58a6ff; }
#author .name { color: #7c83fd; }
```

## Usage examples

- Timeline visualization: `timeline-project`
- Architecture diagram: `system-architecture`
- Knowledge map: `knowledge-map`
- Any p5.js / D3.js / Canvas project
