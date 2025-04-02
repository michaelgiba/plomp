import { defineConfig } from "vite";
import preact from "@preact/preset-vite";
import { viteSingleFile } from "vite-plugin-singlefile";
import { plompDevDataPlugin } from "./src/vite-plugins/dev-data-plugin.js";

export default defineConfig(({ command, mode }) => {
  const config = {
    plugins: [preact(), viteSingleFile()],
    resolve: {
      alias: {
        "@": "/src",
      },
      extensions: [".tsx", ".ts", ".js"],
    },
    build: {
      outDir: "dist",
      sourcemap: true,
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
  };

  if (mode === "development" || command === "serve") {
    console.log("Loading development plugins...");
    config.plugins.push(plompDevDataPlugin());
  } else {
    console.log("Production build: skipping development plugins");
  }

  return config;
});
