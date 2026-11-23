"""Seeded randomized checks over synthetic metadata; no audited filesystem access."""
from collections import defaultdict
import copy
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0,str(ROOT))
from lumen.assistant import model_context
from lumen.demo import demo_reports
from lumen.rules import category, describe_file, findings_for, summarize, uid
from lumen.store import compare

rng=random.Random(286104)
cases=2000
started=time.perf_counter()
template=demo_reports()[0]
sizes=[0,1,1024,1024**2,10*1024**2,500*1024**2,512*1024**2,1024**3]
for case in range(cases):
    files=[]
    groups=defaultdict(list)
    for i in range(rng.randint(1,180)):
        signature=rng.randint(0,35)
        size=sizes[signature % len(sizes)]
        generated=rng.choice([None,None,"node_modules",".venv","__pycache__"])
        folder=f"C:/fixture/project-{i%4}/{generated or 'data'}"
        path=f"{folder}/item-{i}{rng.choice(['.txt','.msi','.bin','.js'])}"
        file={"id":uid(path),"name":Path(path).name,"path":path,"root":"C:/fixture","relative":path[11:],"folder":"project", "size":size,"modified":template["created"]-rng.randint(-10,500)*86400,"accessed":None,"last_opened":None,"category":category(Path(path)),"generated":[folder,generated] if generated else None}
        file.update(describe_file(file))
        files.append(file)
        if size and size<=512*1024**2:
            groups[signature].append(file)
    duplicates=[]
    for signature, members in groups.items():
        if len(members)>1:
            digest=hashlib.sha256(str(signature).encode()).hexdigest()
            duplicates.append({"id":digest[:20],"hash":digest,"files":members,"size":members[0]["size"],"potential_bytes":members[0]["size"]*(len(members)-1)})
    findings=findings_for(files,duplicates,template["created"])
    summary=summarize(files,findings)
    assert 0<=summary["duplicate_bytes"]<=summary["review_bytes"]<=summary["bytes"],case
    assert sum(item["bytes"] for item in summary["categories"])==summary["bytes"],case
    claimed=set()
    for finding in findings:
        assert not claimed.intersection(finding["paths"]),(case,finding)
        claimed.update(finding["paths"])
    report={**template,"files":files,"findings":findings,"duplicates":duplicates,"summary":summary,"roots":["C:/fixture"]}
    context, references=model_context(report,findings[:20])
    assert len(context)<=24000 and "C:/fixture" not in context
    assert references=={item["id"] for item in json.loads(context)["findings"]}
    after=copy.deepcopy(report)
    after["created"]+=1
    for file in rng.sample(after["files"],k=min(5,len(files))):
        file["size"]+=rng.randint(-file["size"],100000)
        file["modified"]+=1
    after["summary"]=summarize(after["files"],[])
    delta=compare(report,after)
    assert delta["delta"]==sum(item["delta"] for item in delta["changes"]),case
    assert delta["added"]==delta["removed"]==0,case
result={"seed":286104,"cases":cases,"seconds":round(time.perf_counter()-started,3),"checks":["review-byte conservation","category-byte conservation","disjoint review membership","bounded masked model context","snapshot delta conservation"],"passed":True}
qa=ROOT / ".qa"
qa.mkdir(exist_ok=True)
(qa / "property-results.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
