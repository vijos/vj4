# 1. install nvm/node
```
$ cd ~/
$ git clone https://github.com/creationix/nvm.git .nvm
$ cd ~/.nvm 
$ git checkout v0.33.8
$ . nvm.sh
$ cat >>~/.bashrc<<EOF
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh" 
[ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
EOF
$ cd ~/
$ nvm ls-remote
$ nvm install --lts=carbon 
$ node -v 
```

# 2. install mongodb/rabbitmq
```
$ sudo apt-get install rabbitmq-server
$ sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
$ echo "deb [ arch=amd64] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.6.list
$ sudo apt-get install apt-transport-https
$ sudo apt-get update
$ sudo apt-get install -y mongodb-org
$ sudo service mongod start
$ sudo apt-get install python3-pip
$ sudo pip3 install --upgrade pip
$ sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 1
$ sudo update-alternatives --install /usr/bin/python python /usr/bin/python2 2
```

# 3. install vj4
```
$ cd ~/
$ git clone https://github.com/vijos/vj4.git
$ cd vj4
$ sudo python -m pip install -r requirements.txt
$ npm install
$ curl "http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.mmdb.gz" | gunzip -c > GeoLite2-City.mmdb 
$ npm run build:production
$ python -m vj4.server --listen=http://0.0.0.0:8888/
$ python -m vj4.model.user add -1 your_username your_password user@domain.com 
$ python -m vj4.model.user set_superadmin -1 
$ python -m vj4.model.user add -2 judge 123456 user@domain.com
$ python -m vj4.model.user set_judge -2
$ python -m vj4.job.rp recalc_all
$ python -m vj4.job.rank run_all
$ python -m vj4.server --listen=http://0.0.0.0:8888/ --smtp-host=your_smtp_server --smtp-user=your_smtp_user --smtp-password=your_smtp_password 
```


# 4. install jd4
```
$ git clone https://github.com/vijos/jd4.git
$ sudo python -m pip install -r requirements.txt
$ mkdir -p ~/.config/jd4
$ cp examples/config.yaml ~/.config/jd4/
$ cp examples/langs.yaml ~/.config/jd4/
$ sudo python setup.py build_ext --inplace
$ sudo python -m jd4.daemon
```

