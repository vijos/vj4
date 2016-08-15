var path = require('path');
var webpack = require('webpack');
var _ = require('lodash');
var glob = require('glob');
var fs = require('fs');

var ExtractTextPlugin = require('extract-text-webpack-plugin');
var CopyWebpackPlugin = require('copy-webpack-plugin');

var extractProjectCSS = new ExtractTextPlugin({ filename: 'vj4.css', allChunks: true });
var extractVendorCSS = new ExtractTextPlugin({ filename: 'vendors.css', allChunks: true });
var postcssAutoprefixerPlugin = require('autoprefixer');
var stylusRupturePlugin = require('rupture');

var root = function (fn) {
  return path.resolve(__dirname, fn);
};

var getI18NEntries = function () {
  var entries = {};
  var localeFiles = glob.sync(root('vj4/locale/*.yaml'));
  localeFiles.forEach(function (fileName) {
    var locale = path.basename(fileName, '.yaml');
    var dummyEntry = root('vj4/ui/.locale-loader/' + locale + '.js');
    fs.writeFileSync(dummyEntry, 'window.LOCALES = require(\'json!yaml!../../locale/' + locale + '.yaml\');\n');
    entries['locale_' + locale] = dummyEntry;
  });
  return entries;
};

var config = {
  context: root('vj4/ui'),
  entry: _.merge({
    vj4: './Entry.js',
  }, getI18NEntries()),
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
        query: _.merge({}, require('./package.json').babel),
      },
      {
        // JSON loader for commonmark.js
        test: /\.json$/,
        loader: 'json',
      },
      {
        // fix pickadate loading
        test: /pickadate/,
        loader: 'imports',
        query: { define: '>false' },
      },
      {
        // project stylus stylesheets
        test: /\.styl$/,
        // TODO: stylus-loader requires 'resolve url' query.
        // to be added once extract-text-webpack-plugin#196 is fixed
        loader: extractProjectCSS.extract(['css', 'postcss', 'stylus?resolve url']),
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

    // extract stylesheets into a standalone file
    extractVendorCSS,
    extractProjectCSS,

    // extract 3rd-party JavaScript libraries into a standalone file
    new webpack.optimize.CommonsChunkPlugin({
      name: 'vendors',
      filename: 'vendors.js',
      minChunks: function (module, count) {
        return module.resource
          && module.resource.indexOf(root('vj4/ui/')) === -1
          && module.resource.match(/\.js$/);
      },
    }),

    // copy static assets
    new CopyWebpackPlugin([{ from: root('vj4/ui/static') }]),

    // copy emoji images
    new CopyWebpackPlugin([{ from: root('node_modules/emojify.js/dist/images/basic'), to: 'img/emoji/' }]),

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
