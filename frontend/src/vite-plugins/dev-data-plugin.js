import fs from "fs";
import path from "path";

/**
 * Plugin to set __PLOMP_BUFFER_JSON__ with development data in dev mode
 */
export function plompDevDataPlugin() {
  return {
    name: "plomp-dev-data-plugin",
    transformIndexHtml: {
      order: "pre",
      handler(html, ctx) {
        // Only replace in development mode
        if (ctx.server) {
          const devDataPath = path.resolve(
            __dirname,
            "./sample-buffer-data.json",
          );

          try {
            const data = fs.readFileSync(devDataPath, "utf-8");
            return html.replace(
              "<!-- insert plomp JSON data here -->",
              "window.__PLOMP_BUFFER_JSON__ = " + data + ";",
            );
          } catch (error) {
            console.error("Error reading dev data file:", error);
            return html;
          }
        }
        return html;
      },
    },
  };
}
