from django.core.serializers import get_serializer
from dulwich import repo, objects
from extinctionr.circles.models import Circle
import os.path
from datetime import datetime


def commit_circles_to_git(repo_path='/tmp/circles/', committer=b'Dave St.Germain <dave@st.germa.in>'):
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

    last_time = datetime.utcfromtimestamp(last_time)
    qset = Circle.objects.filter(modified__gte=last_time)
    index = rep.open_index()
    num_changed = 0
    ser = get_serializer('yaml')()
    for obj in qset:
        data = ser.serialize([obj]).encode('utf8')
        blob = objects.Blob.from_string(data)
        rep.object_store.add_object(blob)
        entry = (obj.created.timestamp(), obj.modified.timestamp(), 1, 1, 33188, 100, 100, len(data), blob.id, 0)
        index[obj.get_path()] = entry
        num_changed += 1
    if num_changed:
        tree = index.commit(rep.object_store)
        message = b'Changed %d entries' % num_changed
        now = datetime.utcnow().timestamp()
        print(rep.do_commit(message=message, committer=committer, commit_timestamp=now, tree=tree))
