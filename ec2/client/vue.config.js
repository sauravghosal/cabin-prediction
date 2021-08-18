const dotenv = require("dotenv");
const dotenvExpand = require("dotenv-expand");
var myEnv = dotenv.config({ path: "../.env" });
dotenvExpand(myEnv);

module.exports = {
  outputDir:
    process.env.NODE_ENV == "development" ? "dist" : "../server/templates",
  assetsDir: process.env.NODE_ENV == "development" ? "" : "../static",
  runtimeCompiler: true,
  // NOTE: set alias via `configureWebpack` or `chainWebpack`
  configureWebpack: {
    resolve: {
      alias: {
        "balm-ui-plus": "balm-ui/dist/balm-ui-plus.js",
        "balm-ui-css": "balm-ui/dist/balm-ui.css",
      },
    },
  },
};
