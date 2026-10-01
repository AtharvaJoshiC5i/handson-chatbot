# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  # NexaTel AI Support Frontend

  React, TypeScript, Vite, and Tailwind frontend for the NexaTel customer-support chat.

  The UI provides customer selection, the personalized welcome page, suggested questions, streaming assistant messages, Markdown/GFM formatting, structured answer details, and lazy-loaded usage/billing charts. The backend owns customer data access and calculations; the frontend renders the response and does not calculate account values.

  For architecture, API behavior, backend setup, supported questions, and safety notes, see the [project README](../README.md) and [question guide](../QUESTIONS.md).

  ## Local Development

  Run the backend on port 8001 first. From this directory:

  ```powershell
  npm install
  npm run dev
  ```

  Open `http://localhost:5173`. The Vite development server proxies `/api` and `/health` to `http://127.0.0.1:8001`.

  ## Checks

  ```powershell
  npm run lint
  npm run build
  ```

  ## Main Components

  - `src/App.tsx`: application shell, selected-customer profile, and streamed chat state.
  - `src/components/MessageBubble.tsx`: user and assistant message rendering with Markdown.
  - `src/components/StructuredPresentation.tsx`: structured result layouts and lazy chart loading.
  - `src/components/TimeSeriesChart.tsx`: numeric usage/billing visualizations and exact-value rows.
  - `src/services/api.ts`: profile, chat SSE, reset, and response parsing.

For the full system setup and API contract, see the [project README](../README.md).

