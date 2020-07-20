import _ from 'lodash';

import webpack from 'webpack';
import fs from 'fs-extra';

import root from '../utils/root.js';
import mapWebpackUrlPrefix from '../utils/mapWebpackUrlPrefix.js';
import StaticManifestPlugin from '../plugins/webpackStaticManifestPlugin.js';
import FriendlyErrorsPlugin from 'friendly-errors-webpack-plugin';
import OptimizeCssAssetsPlugin from 'optimize-css-assets-webpack-plugin';
import ExtractCssPlugin from 'mini-css-extract-plugin';
import CopyWebpackPlugin from 'copy-webpack-plugin';

const beautifyOutputUrl = mapWebpackUrlPrefix([
  { prefix: 'vj4/ui/', replace: 'ui/' },
  { prefix: '_/_/node_modules/katex/dist/', replace: 'katex/' },
  { prefix: 'ui/misc/.iconfont', replace: 'ui/iconfont' },
]);

export default function (env = {}) {
  function eslintLoader() {
    return {
      loader: 'eslint-loader',
      options: {
        configFile: root('vj4/ui/.eslintrc.js'),
      },
    };
  }

  function babelLoader() {
    let cacheDirectory = root('.cache/babel');
    try {
      fs.ensureDirSync(cacheDirectory);
    } catch (ignored) {
      cacheDirectory = false;
    }
    return {
      loader: 'babel-loader',
      options: {
        ...require(root('package.json')).babelForProject,
        cacheDirectory,
      },
    };
  }

  function postcssLoader() {
    return {
      loader: 'postcss-loader',
      options: {
        sourceMap: env.production,
      }
    };
  }

  function styleLoader() {
    return 'style-loader';
  }

  function cssLoader() {
    return {
      loader: 'css-loader',
      options: {
        importLoaders: 1
      }
    }
  }

  function stylusLoader() {
    return 'stylus-loader';
  }

  function fileLoader() {
    return {
      loader: 'file-loader',
      options: {
        name: '[path][name].[ext]?[sha1:hash:hex:10]',
      },
    };
  }

  function extractCssLoader() {
    return ExtractCssPlugin.loader;
  }

  const config = {
    mode: env.production ? 'production' : 'development',
    bail: true,
    profile: true,
    context: root('vj4/ui'),
    devtool: env.production ? 'source-map' : false,
    entry: {
      vj4: './Entry.js',
    },
    output: {
      path: root('vj4/.uibuild'),
      publicPath: '/',    // overwrite in entry.js
      hashFunction: 'sha1',
      hashDigest: 'hex',
      hashDigestLength: 10,
      filename: '[name].js?[chunkhash]',
      chunkFilename: '[name].chunk.js?[chunkhash]',
    },
    resolve: {
      modules: [
        root('node_modules'),
      ],
      alias: {
        vj: root('vj4/ui'),
        picker: 'pickadate/lib/picker',
      },
    },
    optimization: {
      splitChunks: {
        minChunks: 1,
        cacheGroups: {
          vendors: {
            test: /node_modules/,
            name: "vendors",
            chunks: "all",
            reuseExistingChunk: true
          }
        },
      },
    },
    module: {
      rules: [
        {
          test: /\.jsx?$/,
          exclude: /node_modules[\/\\]/,
          enforce: 'pre',
          use: [eslintLoader()],
        },
        {
          // fonts and images
          test: /\.(svg|ttf|eot|woff|woff2|png|jpg|jpeg|gif)$/,
          use: [fileLoader()],
        },
        {
          // ES2015 scripts
          test: /\.js$/,
          exclude: /node_modules[\/\\]/,
          use: [babelLoader()],
        },
        {
          test: /\.styl$/,
          use: env.watch
            ? [styleLoader(), cssLoader(), postcssLoader(), stylusLoader()]
            : [extractCssLoader(), cssLoader(), postcssLoader(), stylusLoader()]
          ,
        },
        {
          test: /\.css$/,
          include: /node_modules[\/\\]/,
          use: env.watch
            ? [styleLoader(), cssLoader()]
            : [extractCssLoader(), cssLoader()]
          ,
        },
        {
          test: /\.css$/,
          exclude: /node_modules[\/\\]/,
          use: env.watch
            ? [styleLoader(), cssLoader(), postcssLoader()]
            : [extractCssLoader(), cssLoader(), postcssLoader()]
          ,
        },
      ],
    },
    plugins: [
      new webpack.ProgressPlugin(),

      new webpack.ProvidePlugin({
        $: 'jquery',
        jQuery: 'jquery',
        'window.jQuery': 'jquery',
        katex: 'katex/dist/katex.js',
        "React": "react",
      }),

      new FriendlyErrorsPlugin(),

      // don't include momentjs locale files
      new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),

      // don't include timeago.js locale files
      // no use. FIXME.
      // new webpack.IgnorePlugin(/locales\//, /timeago/),

      new ExtractCssPlugin({
        filename: '[name].css?[contenthash:10]',
      }),

      // copy static assets
      new CopyWebpackPlugin({
        patterns: [
          'static',
          { from: root('node_modules/emojify.js/dist/images/basic'), to: 'img/emoji/' },
        ],
      }),

      // Options are provided by LoaderOptionsPlugin until webpack#3136 is fixed
      new webpack.LoaderOptionsPlugin({
        test: /\.styl$/,
        stylus: {
          default: {
            preferPathResolver: 'webpack',
            use: [
              require('rupture')(),
            ],
            import: [
              '~vj/common/common.inc.styl',
            ],
          },
        },
      }),

      // Make sure process.env.NODE_ENV === 'production' in production mode
      new webpack.DefinePlugin({
        'process.env': {
          NODE_ENV: env.production ? '"production"' : '"debug"',
        },
      }),

      ...env.production
        ? [
          new OptimizeCssAssetsPlugin(),
          new webpack.optimize.ModuleConcatenationPlugin(),
          new webpack.LoaderOptionsPlugin({ minimize: true }),
          // Replace Module Id with hash or name
          new webpack.HashedModuleIdsPlugin()
        ]
        : [
          new webpack.NamedModulesPlugin()
        ],

      new webpack.LoaderOptionsPlugin({
        options: {
          context: root(),

          // Beautify the output path of assets
          customInterpolateName: (url, name, options) => beautifyOutputUrl(url),
        },
      }),

      // Finally, output asset hashes
      new StaticManifestPlugin({
        fileName: 'static-manifest.json',
        ignore: [
          'img/emoji/',
          'katex/',
        ],
      }),
    ],
  };

  return config;
};
