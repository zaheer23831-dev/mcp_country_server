/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AGENT_BASE_URL?: string; // e.g. http://localhost:5050
  readonly VITE_USE_PROXY?: '0' | '1';   // '1' to use vite proxy for /report
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
