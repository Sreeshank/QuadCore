import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir:'./e2e', timeout:90000, fullyParallel:false,
  use:{baseURL:process.env.E2E_BASE_URL||'http://127.0.0.1:5173',channel:process.env.PLAYWRIGHT_CHANNEL||'msedge',headless:true,trace:'retain-on-failure'},
  reporter:'list',
});

