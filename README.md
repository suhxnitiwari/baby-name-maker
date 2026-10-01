# 👶 Baby Name Maker

A cute little web app for finding baby names for **boys and girls**.

## Features
- **Girl / Boy / Either:** pick a gender and the whole theme changes color
- **Filter by style:** classic, modern, nature, vintage, or mythic
- **Starts with:** limit results to a starting letter
- **Meanings and origins** for every name
- **Blend parents:** mix two names (like Mom + Dad) into brand-new ones
- **Favorites:** tap ♡ to save names (stored in your browser)

## Run it
No build step. Just open `index.html` in a browser.

## Add names
Add entries to `names.js`:
```js
{ n: "Name", g: "girl" | "boy" | "either", o: "Origin", m: "meaning", s: "classic" }
```
