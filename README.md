# richwar

Adding install scripts to ringgem is tedious, so I'd like to move
to using single yaml file from which I can generate scripts using
jinja2.

richwar is an effort to cleanup the install scripts from [ringgem(https://github.com/taylormonacelli/ringgem)].

# Usage:

```bash
cd richwar
rye init
rye sync
git clone https://github.com/taylormonacelli/ringgem
python process_scriptspy --basedir=./ringgem
```

# devbox might rinder this nonsense unnecessary

Today though I discover devbox might obsolete the need for this stuff.

- https://www.jetpack.io/devbox
- https://www.youtube.com/watch?v=WiFLtcBvGMU
- https://www.youtube.com/watch?v=0ulldVwZiKA

