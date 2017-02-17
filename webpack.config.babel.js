import _ from 'lodash';
import path from 'path';
import webpack from 'webpack';
import fs from 'fs-extra';

import mapUrl from './scripts/build/mapUrlHelper.js';
import DummyOutputPlugin from './scripts/build/webpackDummyOutputPlugin.js';
import ExtractTextPlugin from 'extract-text-webpack-plugin';
import CopyWebpackPlugin from 'copy-webpack-plugin';

const extractProjectCSS = new ExtractTextPlugin({ filename: 'vj4.css?[sha1:contenthash:hex:10]', allChunks: true });
const extractVendorCSS = new ExtractTextPlugin({ filename: 'vendors.css?[sha1:contenthash:hex:10]', allChunks: true });

function root(fn) {
  return path.resolve(__dirname, fn);
}

function eslintLoader() {
  return {
    loader: 'eslint-loader',
    options: {
      configFile: root('vj4/ui/.eslintrc.yml'),
    },
  };
}

function babelLoader() {
  return {
    loader: 'babel-loader',
    options: {
      ...require('./package.json').babelForProject,
      cacheDirectory: !_.isError(_.attempt(() => fs.ensureDirSync(root('.cache/babel'))))
        ? root('.cache/babel')
        : false,
    },
  };
}

function jsonLoader() {
  return 'json-loader';
}

function postcssLoader() {
  return 'postcss-loader';
}

function styleLoader() {
  return 'style-loader';
}

function cssLoader() {
  return 'css-loader?importLoaders=1';
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

const beautifyOutputUrl = mapUrl([
  { prefix: 'vj4/ui/',                  replace: 'ui/' },
  { prefix: 'node_modules/katex/dist/', replace: 'katex/' },
  { prefix: 'ui/misc/.iconfont',        replace: 'ui/iconfont' },
]);

export default function (env = {}) {
  const config = {
    context: root('vj4/ui'),
    devtool: env.production ? 'source-map' : 'nosources-source-map',
    watchOptions: {
      aggregateTimeout: 1000,
    },
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
      modules: [root('node_modules'), root('vj4/ui')],
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
          test: /\.json$/,
          use: [jsonLoader()],
        },
        {
          // fix pickadate loading
          test: /pickadate/,
          use: [
            {
              loader: 'imports-loader',
              options: { define: '>false' },
            },
          ],
        },
        {
          // project stylus stylesheets
          test: /\.styl$/,
          use: env.watch
            ? [styleLoader(), cssLoader(), postcssLoader(), stylusLoader()]
            : extractProjectCSS.extract([cssLoader(), postcssLoader(), stylusLoader()])
            ,
        },
        {
          // vendors stylesheets
          test: /\.css$/,
          include: /node_modules[\/\\]/,
          use: env.watch
            ? [styleLoader(), cssLoader()]
            : extractVendorCSS.extract([cssLoader()])
            ,
        },
        {
          // project stylesheets
          test: /\.css$/,
          exclude: /node_modules[\/\\]/,
          use: env.watch
            ? [styleLoader(), cssLoader(), postcssLoader()]
            : extractProjectCSS.extract([cssLoader(), postcssLoader()])
            ,
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

      // don't include momentjs locale files
      new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/),

      // don't include timeago.js locale files
      // no use. FIXME.
      // new webpack.IgnorePlugin(/locales\//, /timeago/),

      // extract stylesheets into a standalone file
      env.watch
        ? new DummyOutputPlugin('vendors.css')
        : extractVendorCSS
        ,

      env.watch
        ? new DummyOutputPlugin('vj4.css')
        : extractProjectCSS
        ,

      // extract 3rd-party JavaScript libraries into a standalone file
      env.watch
        ? new DummyOutputPlugin('vendors.js')
        : new webpack.optimize.CommonsChunkPlugin({
            name: 'vendors',
            minChunks: (module, count) => (
              module.resource
              && module.resource.indexOf(root('vj4/ui/')) === -1
              && module.resource.match(/\.jsx?$/)
            ),
          })
        ,

      // extract manifest into a standalone file
      env.watch
        ? new DummyOutputPlugin('manifest.js')
        : new webpack.optimize.CommonsChunkPlugin({
            name: 'manifest',
          })
        ,

      new webpack.optimize.CommonsChunkPlugin({
        children: true,
        async: true,
        minChunks: 2,
      }),

      // copy static assets
      new CopyWebpackPlugin([{ from: root('vj4/ui/static') }]),

      // copy emoji images
      new CopyWebpackPlugin([{ from: root('node_modules/emojify.js/dist/images/basic'), to: 'img/emoji/' }]),

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
              '~common/common.inc.styl',
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

      // Replace Module Id with hash or name
      env.production
        ? new webpack.HashedModuleIdsPlugin()
        : new webpack.NamedModulesPlugin()
        ,

      new webpack.LoaderOptionsPlugin({
        options: {
          context: __dirname,

          postcss: [require('autoprefixer')],

          // Beautify the output path of assets
          customInterpolateName: (url, name, options) => beautifyOutputUrl(url),
        },
      }),

    ],
    stats: {
      children: false,
    },
  };

  return config;
};
