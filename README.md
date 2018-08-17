# invoke-mongodb
Invoke tasks to stand up MongoDB deployments

**Requires**: [Invoke](http://www.pyinvoke.org/index.html)

Install Invoke with `pip install -r requirements.txt`

**Supports**: MongoDB 3.2, 3.4, 3.6, 4.0

## Usage

### Basic usage:

```
$ inv -l
Available tasks:

  _version     print detected mongod version
  clean        remove data directory
  kill         kill all mongod
  replset      create a replica set
  sharded      create a sharded cluster
  standalone   create a standalone mongod
```

### Standalone:

```
$ inv standalone -h
Usage: inv[oke] [--core-opts] standalone [--options] [other tasks here ...]

Docstring:
  create a standalone mongod

Options:
  -d STRING, --dbpath=STRING
  -p INT, --port=INT
```

### Replica set:

```
$ inv replset -h
Usage: inv[oke] [--core-opts] replset [--options] [other tasks here ...]

Docstring:
  create a replica set

Options:
  -a STRING, --name=STRING
  -d STRING, --dbpath=STRING
  -n INT, --num=INT
  -p INT, --port=INT
```

### Sharded cluster:

```
$ inv sharded -h
Usage: inv[oke] [--core-opts] sharded [--options] [other tasks here ...]

Docstring:
  create a sharded cluster

Options:
  -n INT, --numshards=INT
  -o INT, --nodespershard=INT
  -p INT, --port=INT
  -u INT, --numconfig=INT
```
