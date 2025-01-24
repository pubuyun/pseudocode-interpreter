const MonacoWebpackPlugin = require("monaco-editor-webpack-plugin");
const HtmlWebpackPlugin = require("html-webpack-plugin");
const path = require("path");

module.exports = {
  entry: "./index.js",
  output: {
    path: path.join(__dirname, "dist"),
    filename: "index.js", // 输出的 JS 文件名
    clean: true, // 每次构建前清理 /dist 文件夹
  },
  module: {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        use: {
          loader: "babel-loader",
          options: {
            presets: ["@babel/preset-env", "@babel/preset-react"],
            plugins: ["@babel/plugin-proposal-class-properties"],
          },
        },
      },
      {
        test: /\.css$/,
        use: ["style-loader", "css-loader"],
      },
      {
        test: /\.ttf$/,
        type: "asset/resource",
      },
    ],
  },
  resolve: {
    extensions: [".js", ".json"],
  },
  plugins: [
    new HtmlWebpackPlugin({
      template: "./index.html", // 使用你的模板文件
      filename: "index.html", // 输出文件名
    }),
    new MonacoWebpackPlugin({
      languages: ["plaintext", "javascript"], // 仅加载必要语言
    }),
  ],
};
