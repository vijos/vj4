var fs = require('fs');
var tree = JSON.parse(fs.readFileSync('./package-lock.json').toString());

function fixTree(subtree) {
  if (subtree.dependencies) {
    for (var key in subtree.dependencies) {
      var resolved = subtree.dependencies[key].resolved;
      if (typeof resolved === 'string') {
        resolved = resolved.replace(
          /^https?:\/\/registry.npm.taobao.org\//,
          'https://registry.npmjs.org/'
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

fs.writeFileSync('./package-lock.json', JSON.stringify(tree, null, 2));
