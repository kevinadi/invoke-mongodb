# Basic MongoDB

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

    def create_first_user(self, ctx, port):
        user = {'user': 'user', 'pwd': 'password', 'roles': ['root']}
        command_str = 'mongo --host localhost --port {0} admin '.format(port)
        command_str += '--eval "db.createUser({0})"'.format(user)
        print '>>>', command_str
        ctx.run(command_str)

    def create_keyfile(self, ctx, dbpath):
        self.create_data_dir(ctx)
        keyfilepath = '{0}/keyfile.txt'.format(dbpath)
        if not os.path.isfile(keyfilepath):
            print('Creating keyfile ...')
            chars = string.ascii_uppercase + string.ascii_lowercase + string.digits
            key = ''.join(random.choice(chars) for _ in range(40))
            command_str = 'echo {1} > {0} && chmod 600 {0}'.format(keyfilepath, key)
            print '>>>', command_str
            ctx.run(command_str)
        return keyfilepath


    ## Standalone

    def create_data_dir(self, ctx):
        if not os.path.exists('data'):
            print('Creating data directory ...')
            os.makedirs('data')

    def deploy_standalone(self, ctx, port=27017, dbpath='data', auth=False):
        self.create_data_dir(ctx)
        cmdline = self.cmdline(port, dbpath)
        if auth:
            cmdline += '--auth '
        print('>>> %s' % cmdline)
        result = ctx.run(cmdline, hide=True)
        if auth:
            self.create_first_user(ctx)
        return cmdline


    ### Replica set

    def create_data_dir_replset(self, ctx, num, port):
        self.create_data_dir(ctx)
        print('Creating sub-directories ...')
        num = int(num)
        dbpaths = []
        for i in range(num):
            dirname = 'data/%d' % (port + i)
            dbpaths.append(dirname)
            os.makedirs(dirname)
        return {'dbpaths': dbpaths}

    def wait_for_primary(self, ctx, port):
        for i in range(10):
            print 'Waiting for primary ...'
            time.sleep(2)
            res = ctx.run('mongo --port {0} --quiet --eval "db.isMaster()"'.format(port), hide=True)
            if res.stdout.find('"ismaster" : true') > 0:
                return True
        return False

    def replset_conf(self, ctx, num, port, name):
        num, port = int(num), int(port)
        replconf = {'_id': name, 'members': []}
        for i in range(num):
            replconf['members'].append({'_id': i, 'host': 'localhost:%d' % (port+i)})
        return replconf

    def initiate_replset(self, ctx, num, port, name):
        replconf = self.replset_conf(ctx, num, port, name)
        cmd = 'mongo --port {0} '.format(port)
        cmd += '--eval "rs.initiate({0})"'.format(replconf)
        print '>>>', cmd
        ctx.run(cmd)
        return replconf

    def deploy_replset(self, ctx, num, port, dbpath, name, auth):
        num, port = int(num), int(port)
        dbpaths = self.create_data_dir_replset(ctx, num, port)
        if auth:
            keyfilepath = self.create_keyfile(ctx, dbpath)
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
            print '>>>', cmdline

            cmdlines.append(cmdline)
            ctx.run(cmdline, hide=True)

        replconf = self.initiate_replset(ctx, num, port, name)
        setup = {'dbpaths': dbpaths, 'cmdlines': cmdlines, 'replconf': replconf}

        if auth and self.wait_for_primary(ctx, port):
            self.create_first_user(ctx, port)

        return setup


    ### Sharded cluster

    def create_uri_from_replconf(self, conf):
        replsetid = conf.get('_id')
        hosts = [x.get('host') for x in conf.get('members')]
        return replsetid + '/' + ','.join(hosts)

    def deploy_shardsvr(self, ctx, numshards, nodespershard, dbpath, port, auth):
        shardsetup = []
        for i in range(numshards):
            i_port = port + (i * nodespershard)
            i_name = 'shard%02d' % i
            setup = self.deploy_replset(ctx, nodespershard, i_port, dbpath, i_name, auth)
            shardsetup.append(setup)
        return shardsetup

    def deploy_configsvr(self, ctx, num, dbpath, port, auth):
        print('Deploying config servers ...')
        configsvr = self.deploy_replset(ctx, num, port, dbpath, 'config', auth)
        return configsvr

    def deploy_mongos(self, ctx, configsvr, shardsvr, dbpath, port, auth):
        print('Deploying mongos ...')
        configuri = self.create_uri_from_replconf(configsvr.get('replconf'))
        mongoscmd = 'mongos --configdb {0} --port {1} --logpath data/mongos.log --fork '.format(configuri, port)
        if auth:
            mongoscmd += '--keyFile data/keyfile.txt '
        print '>>>', mongoscmd
        ctx.run(mongoscmd, hide=True)
        shardconf = [x.get('replconf') for x in shardsvr]
        for shard in shardconf:
            cmd = 'mongo --eval "sh.addShard(\'{0}\')" '.format(self.create_uri_from_replconf(shard))
            if auth:
                cmd += '-u user -p password --authenticationDatabase admin'
            print '>>>', cmd
            ctx.run(cmd)
