# invoke-mongodb
Invoke tasks to stand up MongoDB deployments

**Requires**: [Invoke](http://www.pyinvoke.org/index.html)

Install with `python setup.py install`

**Supports**: MongoDB 3.2, 3.4, 3.6, 4.0

## Usage

### Basic usage:

```
$ minv -l
Subcommands:

  _version     print detected mongod version
  clean        remove data directory
  kill         kill all mongod/mongos
  ps           list all mongod/mongos
  replset      create a replica set
  sharded      create a sharded cluster
  standalone   create a standalone mongod
```

### Standalone:

```
$ minv standalone -h
Usage: minv [--core-opts] standalone [--options] [other tasks here ...]

Docstring:
  create a standalone mongod

Options:
  --auth
  --dbpath=STRING
  --port=INT
  --script
```

### Replica set:

```
$ minv replset -h
Usage: minv [--core-opts] replset [--options] [other tasks here ...]

Docstring:
  create a replica set

Options:
  --auth
  --dbpath=STRING
  --name=STRING
  --num=INT
  --port=INT
  --script
```

### Sharded cluster:

```
$ minv sharded -h
Usage: minv [--core-opts] sharded [--options] [other tasks here ...]

Docstring:
  create a sharded cluster

Options:
  --auth
  --nodespershard=INT
  --numconfig=INT
  --numshards=INT
  --port=INT
  --script
```
