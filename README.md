# VJ4

[![Build Status](https://img.shields.io/travis/vijos/vj4.svg?branch=master&style=flat-square)](https://travis-ci.org/vijos/vj4)
[![Code Climate](https://img.shields.io/codeclimate/github/vijos/vj4.svg?style=flat-square)](https://codeclimate.com/github/vijos/vj4)
[![Dependency Status](https://www.versioneye.com/user/projects/575c163d7757a0004a1ded62/badge.svg?style=flat)](https://www.versioneye.com/user/projects/575c163d7757a0004a1ded62)
[![GitHub license](https://img.shields.io/badge/license-AGPLv3-blue.svg?style=flat-square)](https://raw.githubusercontent.com/vijos/vj4/master/LICENSE)

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
if you are in China. Make sure to use `cnpm` by adding `alias` to `npm` instead of installing cnpm cli-tool.

### IP Geo-Location

To enable IP geo-location translation, you need to obtain a [MaxMind GeoLite City DB](http://dev.maxmind.com/geoip/geoip2/geolite2/) and put it in the project root directory:

```bash
curl "http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz" | gunzip -c > GeoLite2-City.mmdb
```

You may also want to install [libmaxminddb](https://github.com/maxmind/libmaxminddb/blob/master/README.md) for higher performance.

## Development

In the root of the repository:

```bash
npm run generate:icon
npm run generate:constant
npm run generate:locale
npm run build  # to watch modifications: npm run watch
python3.5 -m vj4.server --debug
```

* Set `--listen` (default: http://127.0.0.1:8888) to listen on a different address.

As an intuitive example, you may want to add a first user and problem to start:

```bash
alias pm="python3.5 -m"
pm vj4.model.user add -1 icebox 12345 icebox@iceboy.org
pm vj4.model.adaptor.problem add system "Dummy Problem" "# It *works*" -1 777
```

You need to run rank script on a regular basis to maintain correct ranks for all users:

```bash
pm vj4.job.rank rank
```

### After Modifying Icons (`vj4/ui/misc/icons`)

1. `npm run generate:icon`

### After Modifying Constants (`vj4/ui/constant`)

1. `npm run generate:constant`
2. Restart server

### After Modifying Locales (`vj4/locale`)

1. `npm run generate:locale`
2. Restart server

## Production

```bash
npm run generate:icon
npm run generate:constant
npm run generate:locale
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

[JavaScript Style Guide](https://github.com/airbnb/javascript)

## References

* [aiohttp](http://aiohttp.readthedocs.org/en/stable/)
* [Jinja2 Documentation](http://jinja.pocoo.org/docs/)
* [Motor: Asynchronous Python driver for MongoDB](http://motor.readthedocs.org/en/stable/)
* [Webpack Module Bundler](http://webpack.github.io/docs/)
