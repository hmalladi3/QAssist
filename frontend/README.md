# QAssist frontend

React + TypeScript + Vite chat UI for QAssist. See the project root README and
`docs/llds/frontend-chat-ui.md` for the design this implements.

```bash
npm install
cp .env.example .env   # set VITE_API_BASE_URL if the backend isn't on :8000
npm run dev
```

- `npm test` — Vitest + React Testing Library
- `npm run typecheck` — `tsc -b`
- `npm run lint` — oxlint
- `npm run build` — production build to `dist/`
