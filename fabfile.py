from fabric import Connection, task


@task
def deploy(ctx):
    c = Connection('xrmass.org')

    c.run('git -C /home/src/extinctionr/ pull')
    c.run('supervisorctl restart xr')

