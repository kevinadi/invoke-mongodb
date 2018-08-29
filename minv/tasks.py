from __future__ import print_function

import os
import time
from invoke import task
from invoke.tasks import call


def _get_mongod_version(ctx):
    result = ctx.run('mongod --version', hide=True)
    db_ver = result.stdout.split('\n')[0]
    return db_ver

def _setup(ctx):
    db_ver = _get_mongod_version(ctx)
    if db_ver.find('v4.0') > 0:
        import mongo_4_0 as mongo_ver
    elif db_ver.find('v3.6') > 0:
        import mongo_3_6 as mongo_ver
    elif db_ver.find('v3.4') > 0:
        import mongo_3_4 as mongo_ver
    elif db_ver.find('v3.2') > 0:
        import mongo_3_2 as mongo_ver
    else:
        sys.exit('MongoDB version not supported')

    mongo = mongo_ver.Mongo()
    return mongo

def _cmdlines(setup, dbpath, script):
    cmdlines = ''
    if isinstance(setup, dict) and isinstance(setup.get('cmdlines'), list):
        cmdlines = '\n'.join(x for x in setup.get('cmdlines'))
    elif isinstance(setup, list):
        cmdlines = '\n'.join('\n'.join(x.get('cmdlines')) for x in setup)
    else:
        cmdlines = setup.get('cmdlines')
    if not script:
        with open('{0}/start.sh'.format(dbpath), 'a') as outfile:
            print(cmdlines, file=outfile)
    else:
        pass

@task
def _version(ctx):
    ''' print detected mongod version '''
    __mongo__ = _setup(ctx)
    print(__mongo__.version())

@task
def m(ctx):
    ''' show script to install mongodb version manager '''
    cmd = 'curl https://raw.githubusercontent.com/aheckmann/m/master/bin/m'
    print(cmd)

@task(auto_shortflags=False)
def ps(ctx):
    ''' list all mongod/mongos '''
    cmd = "ps -Ao 'pid,command' | grep -v 'grep .* mongod' | grep --color '\smongo[ds]\s'"
    ctx.run(cmd)

@task(auto_shortflags=False)
def kill(ctx):
    ''' kill all mongod/mongos '''
    ps(ctx)
    ctx.run('pgrep mongo[d,s] | xargs -t kill', hide=False)

@task(auto_shortflags=False)
def clean(ctx):
    ''' remove data directory '''
    cmd = 'rm -rf data'
    print(cmd)
    ctx.run(cmd)

@task(auto_shortflags=False)
def standalone(ctx, port=27017, dbpath='data', auth=False, script=False):
    ''' create a standalone mongod '''
    __mongo__ = _setup(ctx)
    print('#', __mongo__.version())
    setup = __mongo__.deploy_standalone(ctx, port, dbpath, auth, script)
    _cmdlines(setup, dbpath, script)
    return setup

@task(auto_shortflags=False)
def replset(ctx, num=3, port=27017, dbpath='data', name='replset', auth=False, script=False):
    ''' create a replica set '''
    __mongo__ = _setup(ctx)
    print('#', __mongo__.version())
    if auth:
        __mongo__.create_keyfile(ctx, dbpath, script)
    setup = __mongo__.deploy_replset(ctx, num, port, dbpath, name, auth, script)
    _cmdlines(setup, dbpath, script)
    return setup

@task(auto_shortflags=False)
def sharded(ctx, numshards=2, nodespershard=1, numconfig=1, port=27017, auth=False, script=False):
    ''' create a sharded cluster '''
    __mongo__ = _setup(ctx)
    print('#', __mongo__.version())
    if auth:
        __mongo__.create_keyfile(ctx, 'data', script)
    shardsvr = __mongo__.deploy_shardsvr(ctx, numshards, nodespershard, 'data', port+1, auth, script)
    _cmdlines(shardsvr, 'data', script)
    configsvr = __mongo__.deploy_configsvr(ctx, numconfig, 'data', port+(numshards*nodespershard)+1, auth, script)
    _cmdlines(configsvr, 'data', script)
    mongos = __mongo__.deploy_mongos(ctx, configsvr, shardsvr, 'data', 27017, auth, script)
    _cmdlines(mongos, 'data', script)


