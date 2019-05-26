import os.path
from datetime import datetime
from django.core.serializers import get_serializer
from django.utils.timezone import make_aware, now
from dulwich import repo, objects
from extinctionr.circles.models import Circle


def commit_circles_to_git(repo_path='/tmp/circles/', committer=b''):
    if os.path.exists(repo_path):
        rep = repo.Repo(repo_path)
    else:
        rep = repo.Repo.init(repo_path, True)
    try:
        head = rep.head()
    except KeyError:
        last_time = 0
    else:
        last_commit = rep[rep.head()]
        last_time = last_commit.commit_time

    last_time = make_aware(datetime.fromtimestamp(last_time))

    qset = Circle.objects.filter(modified__gt=last_time)
    index = rep.open_index()
    num_changed = 0
    ser = get_serializer('yaml')()
    commit_message = []
    for obj in qset:
        data = ser.serialize([obj]).encode('utf8')
        blob = objects.Blob.from_string(data)
        rep.object_store.add_object(blob)
        entry = (obj.created.timestamp(), obj.modified.timestamp(), 1, 1, 33188, 100, 100, len(data), blob.id, 0)
        index[obj.get_path()] = entry
        num_changed += 1
        commit_message.append('Changed {}'.format(obj))

    if num_changed:
        tree = index.commit(rep.object_store)
        message = '\n'.join(commit_message).encode('utf8')
        print(rep.do_commit(message=message, committer=committer, commit_timestamp=now().timestamp(), tree=tree))
