# Usage 

## Install
```
$ virtualenv cicero-env
$ source cicero-env/bin/activate
$ pip install -r cicero/requirements.txt
```


## Render local file
```
(cicero-env) $ python cicero/cicero.py --file talk.md
```
... and then browse to http://0.0.0.0:5000/ for the output.

## Render remote file (on Github)
```
(cicero-env) $ python cicero/cicero.py
```
... and then search for the file on Github using the search box in the
[output](http://0.0.0.0:5000/).

