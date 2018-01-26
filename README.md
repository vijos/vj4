<p align="center">
  <a href="https://github.com/vijos/vj4">
    <img src="https://rawgit.com/vijos/vj4/master/.github_banner.png" alt="vj4" width="100%" align="middle" />
  </a>
</p>

<p align="center">
  <a href="https://travis-ci.org/vijos/vj4" target="_blank"><img src="https://img.shields.io/travis/vijos/vj4/master.svg?style=flat-square"></a>
  <a href="https://codeclimate.com/github/vijos/vj4" target="_blank"><img src="https://img.shields.io/codeclimate/github/vijos/vj4.svg?style=flat-square"></a>
  <a href="https://www.versioneye.com/user/projects/598d6f846725bd005228a0e4" target="_blank"><img src="https://www.versioneye.com/user/projects/598d6f846725bd005228a0e4/badge.svg?style=flat-square"></a>
  <a href="https://raw.githubusercontent.com/vijos/vj4/master/LICENSE" target="_blank"><img src="https://img.shields.io/badge/license-AGPLv3-blue.svg?style=flat-square"></a>
</p>

<p align="center">
  Next generation of <a href="https://vijos.org" target="_blank">Vijos</a>, built with asyncio on Python 3.5.
</p>

***

## Overview

- Problem Categories and Tags
- Solution Sharing & Voting
- Online Coding and Testing (a.k.a. Scratchpad Mode)
- Discussions & Comments
- Trainings
- Contests (ACM & OI)
- Dynamic Ranking System
- Real-time Status Updates
- Online Judge as a Service (a.k.a. Domain): create your own OJ website without dev-ops!
- Management UI
- Sandboxed & Distributed Judging: see [jd4](https://github.com/vijos/jd4), [winjudge](https://github.com/iceb0y/winjudge) and [windows-container](https://github.com/iceb0y/windows-container)
- Secure (we are also CTF players)
- Modern Architecture & User Interface

## Prerequisites

* [Python 3.5+]
```bash
sudo apt-get install python3 python3-pip
sudo pip3 install --upgrade pip
```
* [MongoDB 3.0+]
```bash
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
echo "deb [ arch=amd64] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
sudo apt-get install apt-transport-https
sudo apt-get update
sudo apt-get install -y mongodb-org
sudo service mongod start
```
* [Node.js 6.0+]
```bash
cd ~/
git clone https://github.com/creationix/nvm.git .nvm
cd ~/.nvm 
git checkout v0.33.8
. nvm.sh
cat >>~/.bashrc<<EOF
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" 
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
EOF
nvm install --lts=carbon
```
* [RabbitMQ](http://www.rabbitmq.com/)
```bash
sudo apt-get install rabbitmq-server
```

## Install requirements

In the root of the repository, where `requirements.txt` and `package.json` locates:

```bash
python3 -m pip install -r requirements.txt
npm install   # cnpm install
```

You don't need root privilege to run `npm install`. It installs stuffs in the project directory.

You may want to use [cnpm](https://npm.taobao.org/) and [tuna](https://pypi.tuna.tsinghua.edu.cn/)
if you are in China. Make sure to use `cnpm` by adding `alias` to `npm` instead of installing cnpm cli-tool.

Some requirements may need `Python.h`. In Ubuntu/Debian simply use

```bash
apt install python3-dev
```

to solve the problem.

### IP Geo-Location

To enable IP geo-location translation, you need to obtain a [MaxMind GeoLite City DB](http://dev.maxmind.com/geoip/geoip2/geolite2/) and put it in the project root directory:

```bash
curl "http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz" | gunzip -c > GeoLite2-City.mmdb
```

You may also want to install [libmaxminddb](https://github.com/maxmind/libmaxminddb/blob/master/README.md) for higher performance.

## Development

In the root of the repository:

```bash
npm run build   # or: npm run build:watch
python3 -m vj4.server --debug
```

> Set `--listen` (default: http://127.0.0.1:8888) to listen on a different address.

As an intuitive example, you may want to add a super administrator and a problem to start:

```bash
alias pm="python3 -m"
pm vj4.model.user add -1 icebox 12345 icebox@iceboy.org
pm vj4.model.user set_superadmin -1
pm vj4.model.adaptor.problem add system "Dummy Problem" "# It *works*" -1 1000   # you can also use web UI
```

You need to run these scripts on a regular basis to maintain correct RP and ranks for all users:

```bash
pm vj4.job.rp recalc_all
pm vj4.job.rank run_all
```

### Watch and Restart

Frontend source codes can be recompiled automatically by running:

```bash
npm run build:watch
```

However you need to manually restart the server for server-side code to take effect.

## Production

```bash
npm run build:production
python3 -m vj4.server --listen=unix:/var/run/vj4.sock
```

* Set `--listen` (default: http://127.0.0.1:8888) to listen on a different address.
* Set `--prefork` (default: 1) to specify the number of worker processes.
* Set `--ip-header` (default: '') to use IP address in request headers.
* Set `--url-prefix` (default: https://vijos.org) to set URL prefix.
* Set `--cdn-prefix` (default: /) to set CDN prefix.
* Set `--smtp-host`, `--smtp-user` and `--smtp-password` to specify a SMTP server.
* Set `--db-host` (default: localhost) and/or `--db-name` (default: test) to use a different
  database.

Better to use a reverse proxy like Nginx or h2o.

## Judging

To enable vj4 to judge, at least one judge user and one judge daemon instance are needed.

* Use following commands to create a judge user:

```bash
alias pm="python3 -m"
pm vj4.model.user add -2 judge 123456 judge@example.org
pm vj4.model.user set_judge -2
```

* See https://github.com/vijos/jd4 for more details about the judge daemon.

## Notes

Have fun!

Maximum line width: 100

Indentation: 2 spaces

[JavaScript Style Guide](https://github.com/airbnb/javascript)

## References

* [aiohttp](http://aiohttp.readthedocs.org/en/stable/)
* [Jinja2 Documentation](http://jinja.pocoo.org/docs/)
* [Motor: Asynchronous Python driver for MongoDB](http://motor.readthedocs.org/en/stable/)
* [Webpack Module Bundler](https://webpack.js.org/)
