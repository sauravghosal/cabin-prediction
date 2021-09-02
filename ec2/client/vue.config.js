const dotenv = require("dotenv");
const dotenvExpand = require("dotenv-expand");
var myEnv = dotenv.config({ path: "../.env" });
dotenvExpand(myEnv);

module.exports = {
  outputDir:
    process.env.NODE_ENV == "development" ? "dist" : "../server/templates",
  assetsDir: process.env.NODE_ENV == "development" ? "" : "../static",
  // NOTE: set alias via `configureWebpack` or `chainWebpack`
};
