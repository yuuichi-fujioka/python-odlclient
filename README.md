# How To Use

## install

```
pip install git+https://github.com/yuuichi-fujioka/python-odlclient
```

## Run Command

OpenDaylight Host, Port, User and Password are passed via Environment Variable. e.g.:

```
ODL_HOST=192.168.0.100 odlclient node list
```

Environment Vairable Names are:

| Name     | Description                                                                         |
|:---------|:------------------------------------------------------------------------------------|
| ODL_HOST | OpenDaylight Hostname(default: localhost)                                           |
| ODL_PORT | OpenDaygight API Port(default: 8181)                                                |
| ODL_USER | OpenDaylight API User Name(default admin)                                           |
| ODL_PASS | OpenDaylight API Password(default: password)                                        |
| ODL_URL  | Default Restconf API Path(default: http://${ODL_HOST}:${ODL_PORT}/restconf/config/) |

### List Nodes

```
odlclient node list
```

### List Tables

```
odlclient table list openflow:1111111111
```

### List Flows

```
odlclient flow list openflow:1111111111
```
