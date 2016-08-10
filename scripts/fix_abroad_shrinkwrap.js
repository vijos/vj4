var fs = require('fs');
var tree = JSON.parse(fs.readFileSync('./npm-shrinkwrap.json').toString());

function fixTree(subtree) {
  if (subtree.dependencies) {
    for (var key in subtree.dependencies) {
      var resolved = subtree.dependencies[key].resolved;
      if (typeof resolved === 'string') {
        resolved = resolved.replace(
          /^https:\/\/registry.npm.taobao.org\/([a-zA-Z0-9\-_\.]+)\/download\/([a-zA-Z0-9\-_\.]+)$/,
          'https://registry.npmjs.org/$1/-/$2'
        );
        subtree.dependencies[key].resolved = resolved;
      }
      if (subtree.dependencies[key].dependencies !== undefined) {
        fixTree(subtree.dependencies[key]);
      }
    }
  }
}

fixTree(tree);

fs.writeFileSync('./npm-shrinkwrap.json', JSON.stringify(tree, null, 2));
