const { merge } = require('webpack-merge');
const common = require('./webpack.common.js');
// const MonacoEditorSrc = path.join(__dirname, "..", "src");

module.exports = merge(common, {
  mode: "development",
  devtool: "source-map",
  devServer: { 
    contentBase: "./",
    host: "0.0.0.0",  // 添加这一行
    disableHostCheck: true, 
  }
});
