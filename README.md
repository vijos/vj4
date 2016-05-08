# VJ4

## Prerequisites

* [Python 3.5+ and its header files](https://www.python.org/downloads/source/)
* MongoDB 2.6+ from [official repo](https://docs.mongodb.org/manual/installation/) or
  [manual build](https://git.vijos.org/vijos/vj4/wikis/mongodb-manual-build)
* Node.js 0.11+ from [official repo](https://github.com/nodejs/node-v0.x-archive/wiki/Installing-Node.js-via-package-manager)
  or [manual install](http://npm.taobao.org/mirrors/node)
* [RabbitMQ](http://www.rabbitmq.com/)

## Install requirements

In the root of the repository, where `requirements.txt` and `package.json` locates:

```bash
python3.5 -m pip install -r requirements.txt
npm install   # cnpm install
```

You don't need root privilege to run `npm install`. It installs stuffs in the project directory.

You may want to use [cnpm](https://npm.taobao.org/) and [tuna](https://pypi.tuna.tsinghua.edu.cn/)
if you are in China.

## Development

In the root of the repository:

```bash
npm run build  # to watch modifications: npm run watch
python3.5 -m vj4.server --debug
```

As an intuitive example, you may want to add a first user and problem to start:

```bash
alias pm="python3.5 -m"
pm vj4.model.user add -1 icebox 12345 icebox@iceboy.org
pm vj4.controller.problem add system "Dummy Problem" "# It *works*" -1 777
```

* Set `--port=x` to use a different port (default: 8888).
* Set `--ssl-certfile=x` (required) and `--ssl-keyfile=x` (optional) to enable SSL.

## Production

```bash
npm run build:production
python3.5 -OO -m vj4.unix_server
```

* Set `--path` (default: /tmp/vijos.sock) to specify UNIX socket path.
* Set `--cdn-prefix` (default: /) to set CDN prefix.
* Set `--ip-header` (default: X-Real-IP) to use IP address in request headers.
* Set `--db-host=x` (default: localhost) and/or `--db-name=x` (default: test) to use a different
  database.

## Notes

Have fun!

Maximum line width: 100

Indentation: 2 spaces

## References

* [aiohttp](http://aiohttp.readthedocs.org/en/stable/)
* [Jinja2 Documentation](http://jinja.pocoo.org/docs/)
* [Motor: Asynchronous Python driver for MongoDB](http://motor.readthedocs.org/en/stable/)
* [Webpack Module Bundler](http://webpack.github.io/docs/)
* [Typescript](http://www.typescriptlang.org/Handbook)
