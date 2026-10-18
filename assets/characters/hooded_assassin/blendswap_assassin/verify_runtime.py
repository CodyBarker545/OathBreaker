"""Headless Panda3D animation import smoke check; run with project .venv Python."""
from pathlib import Path
import json
import sys
import gltf
from panda3d.core import NodePath
from direct.actor.Actor import Actor

root=Path(__file__).resolve().parent
model=root/(sys.argv[1] if len(sys.argv)>1 else 'assassin_animated.glb')
actor=Actor(NodePath(gltf.load_model(str(model))))
expected={'Idle','Walk','Arm_Motion_Test'}
assert expected.issubset(actor.getAnimNames()),actor.getAnimNames()
report={}
for clip in sorted(expected):
    frames=actor.getNumFrames(clip)
    assert frames>10,(clip,frames)
    for frame in [0,frames//2,frames-1]:
        actor.pose(clip,frame)
        actor.update(force=True)
    report[clip]={'frames':frames,'fps':actor.getFrameRate(clip),'pose_check':'passed'}
actor.cleanup()
report_path='refined_runtime_validation.json' if 'refined' in model.stem else 'runtime_validation.json'
with (root/report_path).open('w') as f: json.dump(report,f,indent=2)
print(json.dumps(report))
