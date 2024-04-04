# richwar

Adding install scripts to ringgem is tedious, so I'd like to move
to using single yaml file from which I can generate scripts using
jinja2.

richwar is an effort to cleanup the install scripts from [ringgem](https://github.com/taylormonacelli/ringgem).

# Usage:

```bash
cd richwar
rye init
rye sync
git clone https://github.com/taylormonacelli/ringgem
python process_scriptspy --basedir=./ringgem
```

# devbox might render this nonsense unnecessary

Today though I discovered [devbox](https://www.jetpack.io/devbox) which might obsolete the need for this stuff.
