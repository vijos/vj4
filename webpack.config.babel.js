import path from 'path';
import webpack from 'webpack';

import ExtractTextPlugin from 'extract-text-webpack-plugin';
import CopyWebpackPlugin from 'copy-webpack-plugin';
import postcssAutoprefixerPlugin from 'autoprefixer';
import stylusRupturePlugin from 'rupture';

import responsiveCutoff from './vj4/ui/responsive.inc.js';

const extractProjectCSS = new ExtractTextPlugin({ filename: 'vj4.css', allChunks: true });
const extractVendorCSS = new ExtractTextPlugin({ filename: 'vendors.css', allChunks: true });

function root(fn) {
  return path.resolve(__dirname, fn);
}

function vjResponsivePlugin() {
  return style => {
    style.define('vjResponsiveCutoff', responsiveCutoff, true);
  };
}

const config = {
  context: root('vj4/ui'),
  watchOptions: {
    aggregateTimeout: 1000,
  },
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
        test: /\.(svg|ttf|eot|woff|woff2)$/,
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
        query: require('./package.json').babelForProject,
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
    ],
  },
  plugins: [
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery',
      katex: 'katex',
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
      minChunks: (module, count) => (
        module.resource
        && module.resource.indexOf(root('vj4/ui/')) === -1
        && module.resource.match(/\.js$/)
      ),
    }),

    // copy static assets
    new CopyWebpackPlugin([{ from: root('vj4/ui/static') }]),

    // copy emoji images
    new CopyWebpackPlugin([{ from: root('node_modules/emojify.js/dist/images/basic'), to: 'img/emoji/' }]),

  ],
  postcss: () => [postcssAutoprefixerPlugin],
  stylus: {
    use: [
      vjResponsivePlugin(),
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

export default config;
