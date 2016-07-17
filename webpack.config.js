var path = require('path');
var webpack = require('webpack');

var ExtractTextPlugin = require('extract-text-webpack-plugin');
var CopyWebpackPlugin = require('copy-webpack-plugin');

var extractProjectCSS = new ExtractTextPlugin({ filename: 'vj4.css', allChunks: true });
var extractVendorCSS = new ExtractTextPlugin({ filename: 'vendors.css', allChunks: true });
var postcssAutoprefixerPlugin = require('autoprefixer');
var stylusRupturePlugin = require('rupture');

var root = function (fn) {
  return path.resolve(__dirname, fn);
};

var config = {
  context: root('vj4/ui'),
  entry: {
    vj4: './Entry.js',
  },
  output: {
    path: root('vj4/.uibuild'),
    filename: '[name].js',
    chunkFilename: '[name].chunk.js',
  },
  resolve: {
    modules: [root('node_modules'), root('vj4/ui')],
    extensions: ['.js', ''],
  },
  devtool: 'source-map',
  module: {
    preLoaders: [
      {
        test: /\.js?$/,
        loader: 'eslint',
        exclude: /node_modules\//,
      }
    ],
    loaders: [
      {
        // fonts
        test: /\.(ttf|eot|svg|woff|woff2)$/,
        loader: 'file',
        query: {
          name: '[path][name].[ext]?[sha512:hash:base62:7]',
        },
      },
      {
        // images
        test: /\.(png|jpg)$/,
        loader: 'url',
        query: {
          limit: 4024,
          name: '[path][name].[ext]?[sha512:hash:base62:7]',
        }
      },
      {
        // ES2015 scripts
        test: /\.js$/,
        exclude: /node_modules\//,
        loader: 'babel',
        query: {
          cacheDirectory: true,
          plugins: ['lodash', 'transform-runtime'],
          presets: ['es2015-webpack', 'stage-0', 'react'],
        }
      },
      {
        // vendors stylesheets
        test: /\.css$/,
        include: /node_modules\//,
        loader: extractVendorCSS.extract(['css']),
      },
      {
        // project stylesheets
        test: /\.css$/,
        exclude: /node_modules\//,
        loader: extractProjectCSS.extract(['css', 'postcss']),
      },
      {
        // project stylus stylesheets
        test: /\.styl$/,
        loader: extractProjectCSS.extract(['css', 'postcss', 'stylus?resolve url']),
      },
    ]
  },
  plugins: [
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery',
    }),

    // don't include locale files in momentjs
    new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),

    // extract 3rd-party libraries into a standalone file
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendors',
      filename: 'vendors.js',
      minChunks: function (module, count) {
        return module.resource && module.resource.indexOf(root('vj4/ui/')) === -1;
      },
    }),

    // extract stylesheets into a standalone file
    extractProjectCSS,
    extractVendorCSS,

    // copy static assets
    new CopyWebpackPlugin([{ from: root('vj4/ui/static') }]),

  ],
  postcss: function () {
    return [postcssAutoprefixerPlugin];
  },
  stylus: {
    use: [
      stylusRupturePlugin(),
    ],
    import: [
      '~common/common.inc.styl',
    ]
  },
  eslint: {
    configFile: root('vj4/ui/.eslintrc.yml'),
  },
  stats: {
    children: false,
  },
};

module.exports = config;
