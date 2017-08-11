import webpack from 'webpack';
import webpackConfig from './config/webpack.js';

export default function ({ watch, production }) {

  const compiler = webpack(webpackConfig({ watch, production }));
  compiler.apply(new webpack.ProgressPlugin());

  const outputOptions = {
    colors: true,
    errorDetails: true,
    optimizationBailout: production,
  };

  function compilerCallback(err, stats) {
    if (err) {
      // config errors
      console.error(err.stack || err);
      if (err.details) console.error(err.details);
      process.exit(1);
      return;
    }
    console.log(stats.toString(outputOptions));
    if (!watch && stats.hasErrors()) {
      process.exitCode = 1;
    }
  }

  if (watch) {
    compiler.watch({}, compilerCallback);
  } else {
    compiler.run(compilerCallback);
  }

};
