# Basic MongoDB

from __future__ import print_function

import os
import time
import json
import string
import random

class BasicMongo:
    def __init__(self):
        pass

    def version(self):
        return '0.0'


    ## Command lines

    def cmdline(self, port, dbpath):
        return 'mongod --port {0} --dbpath {1} --logpath {1}/mongod.log --fork '.format(port, dbpath)

    def cmdline_replset(self, port, dbpath, name):
        return self.cmdline(port, dbpath) + '--replSet {0} '.format(name)

    def cmdline_configsvr(self, port, dbpath):
        return self.cmdline_replset(port, dbpath, replSet='config') + '--configsvr '

    def cmdline_shardsvr(self, port, dbpath):
        return self.cmdline_replset(port, dbpath, replSet='shard') + '--shardsvr '


    ## Auth

    def create_first_user(self, ctx, port, script):
        user = {'user': 'user', 'pwd': 'password', 'roles': ['root']}
        command_str = 'mongo --host localhost --port {0} admin '.format(port)
        command_str += '--eval "db.createUser({0})"'.format(user)
        print(command_str)
        if not script:
            ctx.run(command_str)

    def create_keyfile(self, ctx, dbpath, script):
        self.create_data_dir(ctx, script)
        keyfilepath = '{0}/keyfile.txt'.format(dbpath)
        if not os.path.isfile(keyfilepath):
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
            key = ''.join(random.choice(chars) for _ in range(40))
            command_str = 'echo {1} > {0} && chmod 600 {0}'.format(keyfilepath, key)
            print(command_str)
            if not script:
                ctx.run(command_str)
        return keyfilepath


    ## Standalone

    def create_data_dir(self, ctx, script):
        if not os.path.exists('data'):
            print('mkdir data')
            if not script:
                os.makedirs('data')

    def deploy_standalone(self, ctx, port=27017, dbpath='data', auth=False, script=False):
        self.create_data_dir(ctx, script)
        cmdline = self.cmdline(port, dbpath)
        if auth:
            cmdline += '--auth '
        print('%s' % cmdline)
        if not script:
            ctx.run(cmdline, hide=True)
        if auth:
            self.create_first_user(ctx, port, script)
        return {'cmdlines': cmdline}


    ### Replica set

    def create_data_dir_replset(self, ctx, num, port, script):
        self.create_data_dir(ctx, script)
        num = int(num)
        dbpaths = []
        for i in range(num):
            dirname = 'data/%d' % (port + i)
            dbpaths.append(dirname)
            print('mkdir {0}'.format(dirname))
            if not script:
                os.makedirs(dirname)
        return {'dbpaths': dbpaths}

    def wait_for_primary(self, ctx, port, script):
        for i in range(10):
            cmd = 'mongo --port {0} --quiet --eval "db.isMaster()"'.format(port)
            if script:
                cmdline = 'until {0} | grep ''"ismaster".*:.*true''; '.format(cmd)
                cmdline += 'do sleep 1; echo waiting for primary...; done'
                print(cmdline)
                return True
            print(cmd)
            res = ctx.run(cmd, hide=True)
            if res.stdout.find('"ismaster" : true') > 0:
                return True
            time.sleep(2)
        return False

    def replset_conf(self, ctx, num, port, name):
        num, port = int(num), int(port)
        replconf = {'_id': name, 'members': []}
        for i in range(num):
            replconf['members'].append({'_id': i, 'host': 'localhost:%d' % (port+i)})
        for i in range(7, num):
            replconf['members'][i]['votes'] = 0
            replconf['members'][i]['priority'] = 0
        replconf['members'][0]['priority'] = 2
        return replconf

    def initiate_replset(self, ctx, num, port, name, script):
        replconf = self.replset_conf(ctx, num, port, name)
        cmd = 'mongo --port {0} '.format(port)
        cmd += '--eval "rs.initiate({0})"'.format(replconf)
        print(cmd)
        if not script:
            ctx.run(cmd)
        return replconf

    def deploy_replset(self, ctx, num, port, dbpath, name, auth, script):
        num, port = int(num), int(port)
        dbpaths = self.create_data_dir_replset(ctx, num, port, script)
        if auth:
            keyfilepath = 'data/keyfile.txt'
        cmdlines = []
        for i in range(num):
            i_port = port + i
            i_dbpath = dbpaths.get('dbpaths')[i]

            cmdline = self.cmdline_replset(i_port, i_dbpath, name)

            if auth:
                cmdline += '--keyFile {0} '.format(keyfilepath)
            if name.startswith('shard'):
                cmdline += '--shardsvr'
            elif name.startswith('config'):
                cmdline += '--configsvr'
            print(cmdline)

            cmdlines.append(cmdline)
            if not script:
                ctx.run(cmdline, hide=True)

        replconf = self.initiate_replset(ctx, num, port, name, script)
        setup = {'dbpaths': dbpaths, 'cmdlines': cmdlines, 'replconf': replconf}

        if auth and self.wait_for_primary(ctx, port, script):
            self.create_first_user(ctx, port, script)

        return setup


    ### Sharded cluster

    def create_uri_from_replconf(self, conf):
        replsetid = conf.get('_id')
        hosts = [x.get('host') for x in conf.get('members')]
        return replsetid + '/' + ','.join(hosts)

    def deploy_shardsvr(self, ctx, numshards, nodespershard, dbpath, port, auth, script):
        shardsetup = []
        for i in range(numshards):
            i_port = port + (i * nodespershard)
            i_name = 'shard%02d' % i
            setup = self.deploy_replset(ctx, nodespershard, i_port, dbpath, i_name, auth, script)
            shardsetup.append(setup)
        return shardsetup

    def deploy_configsvr(self, ctx, num, dbpath, port, auth, script):
        configsvr = self.deploy_replset(ctx, num, port, dbpath, 'config', auth, script)
        return configsvr

    def deploy_mongos(self, ctx, configsvr, shardsvr, dbpath, port, auth, script):
        configuri = self.create_uri_from_replconf(configsvr.get('replconf'))
        mongoscmd = 'mongos --configdb {0} --port {1} --logpath data/mongos.log --fork '.format(configuri, port)
        if auth:
            mongoscmd += '--keyFile data/keyfile.txt '
        print(mongoscmd)
        if not script:
            ctx.run(mongoscmd, hide=True)
        shardconf = [x.get('replconf') for x in shardsvr]
        for shard in shardconf:
            cmd = 'mongo --eval "sh.addShard(\'{0}\')" '.format(self.create_uri_from_replconf(shard))
            if auth:
                cmd += '-u user -p password --authenticationDatabase admin'
            print(cmd)
            if not script:
                ctx.run(cmd)
        return {'cmdlines': mongoscmd}
