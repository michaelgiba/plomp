import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import path from "path";
import { plompDevDataPlugin } from "./src/vite-plugins/dev-data-plugin.js";

export default defineConfig({
  plugins: [preact(), viteSingleFile(), plompDevDataPlugin()],
  mode: "development",
  resolve: {
    alias: {
      "@": "/src",
    },
    extensions: [".tsx", ".ts", ".js"],
  },
  build: {
    outDir: "dist",
    sourcemap: "inline",
    assetsInlineLimit: Infinity,
    cssCodeSplit: false,
    rollupOptions: {
      input: "index.html",
      output: {
        manualChunks: undefined,
        inlineDynamicImports: true,
      },
    },
    emptyOutDir: true,
  },
});
