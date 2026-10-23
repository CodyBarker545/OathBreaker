import bpy,json
from collections import defaultdict
hair=[o for o in bpy.data.collections['Outfit_Head'].objects if o.name.startswith('Hair_')]
hood=bpy.data.objects['Hood_Fitted_Over_Hair_Closed_Crown']
rows=defaultdict(lambda:[0,0])
for v in hood.data.vertices:
    row=rows[round(v.co.z,4)];row[0]=max(row[0],abs(v.co.x));row[1]=max(row[1],abs(v.co.y+.045))
result={'hair_bounds':{o.name:[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)] for o in hair},'hood_rows':dict(rows)}
