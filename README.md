# VJ4

Next generation of Vijos, built with asyncio on Python 3.5.

## Prerequisites

* [Python 3.5+ and its header files](https://www.python.org/downloads/source/)
* [MongoDB 3.0+](https://docs.mongodb.org/manual/installation/)
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

* Set `--listen` (default: http://127.0.0.1:8888) to listen on a different address.

As an intuitive example, you may want to add a first user and problem to start:

```bash
alias pm="python3.5 -m"
pm vj4.model.user add -1 icebox 12345 icebox@iceboy.org
pm vj4.controller.problem add system "Dummy Problem" "# It *works*" -1 777
```

## Production

```bash
npm run build:production
python3.5 -OO -m vj4.server --listen=unix:/var/run/vj4.sock
```

* Set `--listen` (default: http://127.0.0.1:8888) to listen on a different address.
* Set `--prefork` (default: 1) to specify the number of worker processes.
* Set `--ip-header` (default: X-Forwarded-For) to use IP address in request headers.
* Set `--url-prefix` (default: https://vijos.org) to set URL prefix.
* Set `--cdn-prefix` (default: /) to set CDN prefix.
* Set `--smtp-host`, `--smtp-user` and `--smtp-password` to specify a SMTP server.
* Set `--db-host` (default: localhost) and/or `--db-name` (default: test) to use a different
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
