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

  _version          print detected mongod version
  clean (cl)        remove data directory
  kill (kl)         kill all mongod/mongos
  m                 show script to install mongodb version manager
  ps                list all mongod/mongos
  replset (rs)      create a replica set
  sharded (sh)      create a sharded cluster
  standalone (st)   create a standalone mongod
```

### Standalone:

```
$ minv -h st
Usage: minv [--core-opts] st [--options] [other tasks here ...]

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
$ minv -h rs
Usage: minv [--core-opts] rs [--options] [other tasks here ...]

Docstring:
  create a replica set

Options:
  --auth
  --dbpath=STRING
  --name=STRING
  --num=STRING
  --port=INT
  --script
```

`num` is a positional argument when creating a replica set. It is also possible to pass replica set deployment configuration into `rs`. For example:

```
  minv rs 1 -- start a one node replica set
  minv rs 3 -- start a three node replica set
  minv rs PSA -- start a PSA replica set
  minv rs PSSAA -- start a PSSAA replica set
```

### Sharded cluster:

```
$ minv -h sh
Usage: minv [--core-opts] sh [--options] [other tasks here ...]

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
