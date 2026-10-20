"""Build four distinct Blender characters from the shared fitted Eliber base."""
import bpy,os,sys,math,random
from mathutils import Vector
sys.path.insert(0,os.path.dirname(__file__))
from character_asset_builder import Character,ROOT
from math import sin,cos,pi
DOWNLOADS=r'C:\Users\cody_\Downloads'
def palette(c):
 return {
 'skin':c.mat('warm skin',(.47,.29,.19),rough=.71,kind='skin'),
 'leather':c.mat('weathered saddle leather',(.13,.072,.039),rough=.77,kind='leather'),
 'black':c.mat('charcoal cloth',(.042,.041,.045),rough=.94),
 'ivory':c.mat('stained ivory linen',(.48,.405,.285),rough=.96),
 'red':c.mat('faded oxblood cloth',(.20,.021,.028),rough=.95),
 'steel':c.mat('weathered steel',(.36,.365,.35),metal=.74,rough=.56,kind='metal'),
 'darksteel':c.mat('blackened iron',(.065,.075,.082),metal=.76,rough=.45,kind='metal'),
 'bronze':c.mat('old bronze',(.27,.155,.055),metal=.72,rough=.47,kind='metal'),
 'mail':c.mat('interlinked dark mail',(.13,.145,.15),metal=.65,rough=.66,kind='mail'),
 'thread':c.mat('worn ochre stitching',(.30,.20,.08),rough=.94),
 'shadow':c.mat('deep seams',(.009,.007,.006),rough=.91,kind='skin')}
def shoulders(c,p,heavy=False):
 for s,side in [(1,'R'),(-1,'L')]:
  for j in range(3):
   cx=s*(.27+j*.035);z=1.61-j*.061;rx=(.14 if heavy else .123)-j*.012;ry=.127-j*.008
   vs=[];fs=[];rows=6;n=24
   for row in range(rows):
    t=.07+row/(rows-1)*1.48
    for k in range(n):
     a=k/n*math.tau;vs.append((cx+rx*sin(t)*cos(a),ry*sin(t)*sin(a),z+.093*cos(t)))
   fs.append(tuple(range(n-1,-1,-1)))
   for row in range(rows-1):
    for k in range(n):fs.append((row*n+k,row*n+(k+1)%n,(row+1)*n+(k+1)%n,(row+1)*n+k))
   o=c.mesh('Overlapping forged shoulder.'+side,vs,fs,p['steel'],'upper_arm.'+side);sol=o.modifiers.new('Forged shell thickness','SOLIDIFY');sol.thickness=.008
   pts=[(cx+rx*cos(k/32*math.tau),ry*sin(k/32*math.tau),z+.001) for k in range(33)]
   c.tube('Shoulder rolled bronze rim',pts,[.003]*len(pts),p['bronze'],'upper_arm.'+side,7)
   for k in range(4):
    a=pi+(k+.5)/4*pi;c.ell('Shoulder rivet',(cx+rx*.88*cos(a),ry*.96*sin(a)-.002,z+.021),(.006,.004,.006),p['bronze'],'upper_arm.'+side)
def bracers_boots(c,p,heavy=False):
 for s,side in [(1,'R'),(-1,'L')]:
  fore='forearm.'+side;shin='shin.'+side;foot='foot.'+side
  c.tube('Leather bracer foundation',[(s*.39,-.012,1.278),(s*.43,-.028,1.16),(s*.47,-.045,1.055)],[.073,.073,.055],p['leather'],fore,18)
  for j in range(3):
   x=s*(.411+j*.025);z=1.235-j*.072
   poly=[(x-.049,-.107,z+.022),(x+.049,-.107,z+.022),(x+.048,-.115,z-.020),(x,-.131,z-.029),(x-.048,-.115,z-.020)]
   c.plate('Articulated bracer splint',poly,(x,-.140,z),p['steel'],fore,p['bronze'])
  c.tube('Tall strapped boot shaft',[(s*.18,.005,.16),(s*.175,.002,.35),(s*.166,-.005,.55)],[.075,.079,.075],p['leather'],shin,20)
  for j in range(4):
   z=.21+j*.073
   for k in [-1,1]:c.ell('Boot eyelet',(s*.175+k*.027,-.077,z),(.004,.003,.004),p['bronze'],shin)
   c.line('Boot crossed lace',(s*.175-.026,-.084,z),(s*.175+.026,-.084,z+.052),.0022,p['thread'],shin)
   c.line('Boot crossed lace',(s*.175+.026,-.084,z),(s*.175-.026,-.084,z+.052),.0022,p['thread'],shin)
  if heavy:
   x=s*.17;poly=[(x,-.11,.73),(x+.08,-.10,.65),(x+.058,-.132,.57),(x,-.153,.53),(x-.058,-.132,.57),(x-.08,-.10,.65)]
   c.plate('Dished knee guard',poly,(x,-.17,.64),p['steel'],shin,p['bronze'])
   poly=[(x-.064,-.10,.56),(x+.064,-.10,.56),(s*.231,-.095,.235),(s*.18,-.142,.155),(s*.125,-.095,.235)]
   c.plate('Ridged steel greave',poly,(s*.175,-.16,.39),p['steel'],shin,p['bronze'])
   for j in range(3):
    y=-.075-j*.057;z=.15-j*.027
    poly=[(s*.18-.072,y+.023,z-.012),(s*.18,y+.027,z+.02),(s*.18+.072,y+.023,z-.012),(s*.18+.072,y-.028,z-.020),(s*.18,y-.044,z-.008),(s*.18-.072,y-.028,z-.020)]
    c.plate('Overlapping steel toe plate',poly,(s*.18,y-.006,z+.025),p['steel'],foot,p['bronze'])
  else:
   c.ell('Rounded knee armour',(s*.165,-.10,.637),(.082,.052,.088),p['steel'],shin)
def hood(c,mat,lining,trim):
 rings=[(1.65,.145,.115,1.0),(1.72,.149,.128,1.04),(1.82,.151,.140,1.02),(1.91,.140,.136,.90),(1.968,.109,.113,.64),(1.998,.059,.071,.35)]
 n=49;vs=[];fs=[]
 for j,(z,rx,ry,opening) in enumerate(rings):
  for k in range(n):
   a=opening+(math.tau-2*opening)*k/(n-1);r=.003*sin(a*5+j*.5);vs.append(((rx+r)*sin(a),.018-(ry+r)*cos(a),z))
 for j in range(len(rings)-1):
  for k in range(n-1):fs.append((j*n+k,j*n+k+1,(j+1)*n+k+1,(j+1)*n+k))
 top=len(vs);vs.append((0,.015,2.018))
 for k in range(n-1):fs.append(((len(rings)-1)*n+k,(len(rings)-1)*n+k+1,top))
 o=c.mesh('Deep folded pilgrim hood',vs,fs,mat,'head');o.data.materials.append(lining);sol=o.modifiers.new('Hood cloth and lining','SOLIDIFY');sol.thickness=.003;sol.offset=-1;sol.material_offset=1
 for k in [0,n-1]:
  pts=[vs[j*n+k] for j in range(len(rings))];c.tube('Hood stitched opening',pts,[.0025]*len(pts),trim,'head',7)
def wrap_mask(c,mat):
 rows=25;cols=49;vs=[];fs=[]
 for j in range(rows):
  t=j/(rows-1)
  for k in range(cols):
   u=k/(cols-1)*2-1;a=u*1.34;top=1.804-.014*abs(u);bottom=1.687+.042*abs(u)**1.3
   nose=.026*math.exp(-(u/.34)**2)*math.exp(-((t-.19)/.28)**2);fold=.0035*sin(t*pi*5+u*2)*sin(t*pi)
   vs.append((.105*sin(a),-(.098-.006*t+nose+fold)*cos(a),top*(1-t)+bottom*t))
 for j in range(rows-1):
  for k in range(cols-1):fs.append((j*cols+k,(j+1)*cols+k,(j+1)*cols+k+1,j*cols+k+1))
 o=c.mesh('Soft fitted lower-face cloth wrap',vs,fs,mat,'head');sol=o.modifiers.new('Thin face fabric','SOLIDIFY');sol.thickness=.0014
def hair(c,mat,short=False):
 # A compact scalp and overlapping curved locks, suitable for a hood or wavy short hair.
 vs=[];fs=[];rows=12;n=40
 for j in range(rows):
  t=j/(rows-1)
  for k in range(n):
   a=k/n*math.tau;phi=.04+t*(1.62-.46*max(0,-sin(a))+.40*max(0,sin(a)))
   vs.append((.108*sin(phi)*cos(a),.015+.101*sin(phi)*sin(a),1.851+.133*cos(phi)))
 for j in range(rows-1):
  for k in range(n):fs.append((j*n+k,(j+1)*n+k,(j+1)*n+(k+1)%n,j*n+(k+1)%n))
 c.mesh('Hair scalp coverage',vs,fs,mat,'head')
 for j in range(9):
  x=-.075+j*.019
  controls=[Vector((x+.025,.028,1.951)),Vector((x+.006,-.049,1.975)),Vector((x-.015,-.100,1.934)),Vector((x-.028,-.099,1.858+random.uniform(-.013,.019)))]
  pts=[];radii=[]
  for k in range(19):
   t=k/18;a,b,cc,d=controls;pts.append((1-t)**3*a+3*(1-t)**2*t*b+3*(1-t)*t*t*cc+t**3*d)
   w=(.015+.003*sin(t*pi))*max(.02,(1-t)**.6);radii.append((w,.007*max(.06,(1-t)**.5)))
  c.tube('Swept brown fringe',pts,radii,mat,'head',12)
 if not short:
  for j in range(12):
   a=.03+j/11*(pi-.06)
   pts=[(.09*cos(a),.015+.084*sin(a),1.94),(.117*cos(a),.015+.110*sin(a),1.91),(.125*cos(a),.018+.122*sin(a),1.84),(.129*cos(a),.020+.125*sin(a),1.788+random.uniform(-.012,.012))]
   c.tube('Wavy side and nape lock',pts,[(.020,.009),(.023,.010),(.016,.008),(.001,.001)],mat,'head',12)
def capelet(c,mat):
 n=57;rows=11;vs=[];fs=[]
 for j in range(rows):
  t=j/(rows-1)
  for k in range(n):
   a=.65+(math.tau-1.3)*k/(n-1);rx=.125+.300*sin(t*pi/2);ry=.115+.160*sin(t*pi/2)
   z=1.64-.43*t+.018*sin(a*7)*t
   if j==rows-1:z+=random.uniform(0,.04)
   vs.append((rx*sin(a),.012-ry*cos(a)+.013*sin(a*7)*t,z))
 for j in range(rows-1):
  for k in range(n-1):
   if j>rows-3 and k%13==0:continue
   fs.append((j*n+k,(j+1)*n+k,(j+1)*n+k+1,j*n+k+1))
 o=c.mesh('Frayed ivory shoulder mantle',vs,fs,mat);sol=o.modifiers.new('Soft mantle thickness','SOLIDIFY');sol.thickness=.004
def sister():
 c=Character('forsaken_sister','Forsaken Sister','ForsakenSister',os.path.join(DOWNLOADS,'Forsaken Sister Lantern Sprite Atlas.png'));p=palette(c)
 c.set_base(p['ivory'],p['leather'],p['skin'])
 # A softer face and shorter, narrower overall figure distinguish the Sister from the shared base.
 for v in c.face.data.vertices:
  world=c.face.matrix_world@v.co
  if world.z<1.78:world.x*=.90
  else:world.x*=.94
  v.co=c.face.matrix_world.inverted()@world
 for o in c.collection.objects:
  if o.name.startswith('Natural blond eyebrow'):o.data.materials.clear();o.data.materials.append(p['leather'])
 hairmat=c.mat('chestnut hair',(.13,.061,.025),rough=.74,kind='hair');hair(c,hairmat,True)
 c.sleeves(p['mail'],.074);c.robe('Long stained pilgrim dress',p['ivory'],.27,1.07,.32)
 # The burgundy insert and torn capelet sit over mail cuffs and a fitted leather corset.
 c.panel('Torn burgundy devotion panel',p['red'],[(.04,-.159,1.08),(.045,-.18,.86),(.08,-.205,.51),(.12,-.21,.33)],.095)
 capelet(c,p['ivory']);c.cowl(p['ivory']);hood(c,p['red'],p['black'],p['thread']);c.harness(p['leather'],p['bronze']);c.belt(p['leather'],p['bronze'])
 for sign,side in [(1,'R'),(-1,'L')]:
  for j in range(5):
   z=1.07+j*.035;x=sign*(.466-j*.013)
   c.tube('Ivory wrist wrapping',[(x-sign*.040,-.04,z),(x,-.091,z+.006),(x+sign*.040,-.035,z)],[.005]*3,p['ivory'],'forearm.'+side)
  for z in [.18,.25]:
   c.tube('Leather boot strap',[(sign*.11,.015,z),(sign*.14,-.08,z),(sign*.21,-.08,z),(sign*.25,.015,z)],[.005]*4,p['leather'],'shin.'+side)
 c.line('Sun medallion hanging chain',(.10,-.16,1.09),(.115,-.20,.89),.0022,p['bronze'],'pelvis');c.sun('Sun pendant',(.115,-.205,.87),.042,p['bronze'],'pelvis')
 c.sun('Burgundy panel sun embroidery',(.085,-.216,.64),.045,p['thread'],'tabard_front.01')
 # Lantern and staff are editable non-weapon equipment, following the right hand.
 wood=c.mat('aged lantern staff wood',(.10,.056,.024),rough=.86,kind='leather');glow=c.mat('warm lantern glass',(.42,.13,.006),rough=.28,kind='glass',emission=.45)
 glow.node_tree.nodes.get('Principled BSDF').inputs['Transmission Weight'].default_value=.65
 c.tube('Lantern staff',[(.49,-.061,.10),(.49,-.061,1.90)],[.018,.018],wood,'hand.R',14,True)
 center=Vector((.49,-.061,1.875));radius=.098
 for z,r in [(1.697,.070),(1.72,.103),(2.025,.103),(2.05,.07)]:
  pts=[(.49+r*cos(k/32*math.tau),-.061+r*sin(k/32*math.tau),z) for k in range(33)];c.tube('Lantern iron ring',pts,[.007]*len(pts),p['darksteel'],'hand.R',8,True)
 for k in range(6):
  a=k/6*math.tau;x=.49+radius*cos(a);y=-.061+radius*sin(a)
  c.line('Lantern bronze cage bar',(x,y,1.72),(x,y,2.025),.006,p['bronze'],'hand.R',True)
  a2=(k+1)/6*math.tau;vs=[(x,y,1.745),(.49+radius*cos(a2),-.061+radius*sin(a2),1.745),(.49+radius*cos(a2),-.061+radius*sin(a2),2.003),(x,y,2.003)]
  c.mesh('Lantern amber glass pane',vs,[(0,1,2,3)],glow,'hand.R',equipment=True)
 c.ell('Lantern peaked cap',(.49,-.061,2.045),(.108,.108,.046),p['darksteel'],'hand.R',True)
 c.sun('Lantern front sun filigree',(.49,-.166,1.875),.033,p['bronze'],'hand.R',True)
 flame=c.mat('living candle flame',(.90,.30,.018),rough=.6,kind='glass',emission=6)
 c.ell('Visible inner candle flame',(.49,-.061,1.87),(.019,.019,.080),flame,'hand.R',True)
 for k in range(6):
  a=(k+.5)/6*math.tau;rr=.101;x=.49+rr*cos(a);y=-.061+rr*sin(a)
  c.tube('Lantern curled bronze filigree',[(x,y,1.77),(.49+rr*cos(a+.12),-.061+rr*sin(a+.12),1.815),(.49+rr*cos(a-.10),-.061+rr*sin(a-.10),1.90),(x,y,1.97)],[.0032]*4,p['bronze'],'hand.R',8,True)
 c.tube('Lantern tapered dome',[(.49,-.061,2.03),(.49,-.061,2.075),(.49,-.061,2.105)],[.103,.065,.025],p['darksteel'],'hand.R',24,True)
 pts=[(.49+.027*cos(k/32*math.tau),-.061,2.128+.027*sin(k/32*math.tau)) for k in range(33)];c.tube('Lantern top hanging ring',pts,[.004]*len(pts),p['bronze'],'hand.R',8,True)
 data=bpy.data.lights.new('Lantern practical warm light','POINT');data.energy=7;data.color=(1,.39,.055);data.shadow_soft_size=.16;o=bpy.data.objects.new(data.name,data);c.equipment.objects.link(o);o.location=center
 c.finish((.91,.96,.95))
def ninja():
 c=Character('masked_ninja','Masked Ninja','MaskedNinja',os.path.join(DOWNLOADS,'Masked Ninja 16-Frame Sprite Atlas.png'));p=palette(c)
 gray=c.mat('weathered slate linen',(.115,.112,.105),rough=.95);edgecloth=c.mat('faded ash cloth hems',(.23,.217,.181),rough=.96)
 c.set_base(p['black'],p['leather'],p['skin']);c.sleeves(p['black'],.078);shoulders(c,p);bracers_boots(c,p)
 c.cowl(gray);c.harness(p['leather'],p['bronze']);c.belt(p['leather'],p['bronze'])
 c.robe('Layered split gray tunic skirt',edgecloth,.64,1.06,.28)
 for sign in [-1,1]:
  panel=c.panel('Tattered charcoal tunic flap',gray,[(sign*.11,-.16,1.055),(sign*.15,-.18,.91),(sign*.20,-.19,.76),(sign*.26,-.17,.65)],.10)
  for v in panel.data.vertices:
   t=max(0,min(1,(1.06-v.co.z)/.42));rx=.20+.08*t;ry=.142+.10*t;v.co.y=-ry*math.sqrt(max(.025,1-(v.co.x/rx)**2))-.011
  panel.data.materials.append(edgecloth)
  for poly in panel.data.polygons:
   if any(panel.data.loops[i].vertex_index%13 in [0,1,11,12] for i in poly.loop_indices):poly.material_index=1
  poly=[c.front(sign*x,z,.009) for x,z in [(.02,1.56),(.155,1.53),(.17,1.45),(.11,1.34),(.025,1.37)]]
  c.plate('Fitted leather ninja chest panel',poly,c.front(sign*.09,1.45,.017),p['leather'],'chest',p['bronze'],True)
 c.panel('Trailing dark back coat',gray,[(0,.14,1.58),(.04,.22,1.25),(.11,.29,.85),(.22,.30,.64)],.17,['scarf_back.00','scarf_back.01','scarf_back.02','scarf_back.03'])
 wrap_mask(c,p['black'])
 # Layered cloth cap leaves an eye slit instead of a hood opening.
 vs=[];fs=[];n=48;rows=13
 for j in range(rows):
  phi=.035+j/(rows-1)*1.49
  for k in range(n):
   a=k/n*math.tau;z=1.835+.132*cos(phi);vs.append((.112*sin(phi)*cos(a),.012+.106*sin(phi)*sin(a),z))
 for j in range(rows-1):
  for k in range(n):fs.append((j*n+k,(j+1)*n+k,(j+1)*n+(k+1)%n,j*n+(k+1)%n))
 c.mesh('Fitted ninja headcloth',vs,fs,p['black'],'head')
 for z,rx,ry in [(1.866,.110,.105),(1.898,.098,.094),(1.928,.080,.077)]:
  pts=[(rx*cos(k/48*math.tau),.012+ry*sin(k/48*math.tau),z+.003*sin(k/48*math.tau*3)) for k in range(49)]
  c.tube('Wrapped headband seam',pts,[.003]*len(pts),gray,'head',7)
 c.ell('Bandana tied knot',(0,.122,1.855),(.032,.027,.027),p['black'],'head')
 for j in range(2):
  pts=[(0,.129,1.86-j*.02),(-.12,.16,1.84-j*.03),(-.25,.20,1.86-j*.04),(-.39+j*.03,.23,1.80-j*.04)]
  c.tube('Loose tied headcloth tail',pts,[(.020,.004),(.025,.004),(.024,.003),(.001,.001)],p['black'],'head',12)
 c.finish((.98,1,1))
def branched_cross(c,name,pos,size,mat,bone='chest',equipment=False):
 x,y,z=pos
 c.line(name+' upright',(x,y,z-size),(x,y,z+size),size*.075,mat,bone,equipment)
 c.line(name+' crossbar',(x-size*.63,y,z+size*.22),(x+size*.63,y,z+size*.22),size*.065,mat,bone,equipment)
 for sign in [-1,1]:
  c.line(name+' fork',(x+sign*size*.55,y,z+size*.22),(x+sign*size*.72,y,z+size*.51),size*.042,mat,bone,equipment)
  c.line(name+' root',(x,y,z-size*.55),(x+sign*size*.36,y,z-size*.79),size*.045,mat,bone,equipment)
 c.line(name+' crown fork',(x,y,z+size*.65),(x-size*.24,y,z+size*.92),size*.045,mat,bone,equipment)
def knight():
 c=Character('broken_oath_knight','Broken Oath Knight','BrokenOathKnight',os.path.join(DOWNLOADS,'Broken Oath Knight Sprite Atlas.png'));p=palette(c)
 blue=c.mat('faded oath blue wool',(.035,.096,.165),rough=.96)
 c.set_base(p['mail'],p['leather']);c.sleeves(p['mail'],.092);shoulders(c,p,True);bracers_boots(c,p,True)
 for o in list(c.collection.objects):
  if o.type!='MESH':continue
  if o.name.startswith(('Unmasked','Natural','Blue grey','Eye pupil','Upper eyelid','Lower eyelid','Inset nostril','Upper lip','Lower lip','Mouth seam','Face |')):bpy.data.objects.remove(o,do_unlink=True)
  elif o.name.startswith(('Human hand','Fingerless glove','Fingernail','Soft glove')):o.data.materials.clear();o.data.materials.append(p['steel'])
 for sign in [-1,1]:
  poly=[c.front(sign*x,z,.012) for x,z in [(.015,1.56),(.165,1.54),(.205,1.43),(.145,1.27),(.025,1.25)]]
  c.plate('Forged breastplate half',poly,c.front(sign*.09,1.43,.025),p['steel'],'chest',p['bronze'],True)
  for j in range(3):
   x=sign*(.11+j*.035);z=1.05-j*.055
   poly=[(x-.045,-.15,z),(x+.045,-.15,z),(x+.050,-.17,z-.13),(x,-.19,z-.17),(x-.045,-.17,z-.13)]
   c.plate('Layered steel hip tasset',poly,(x,-.20,z-.05),p['steel'],'pelvis',p['bronze'])
 c.robe('Torn ivory surcoat lining',p['ivory'],.60,1.075,.30)
 c.panel('Blue front oath tabard',blue,[(0,-.160,1.56),(0,-.169,1.35),(.02,-.185,.95),(.05,-.20,.61)],.142,['chest','pelvis','tabard_front.00','tabard_front.01'])
 c.panel('Frayed blue oath cape',blue,[(0,.14,1.62),(.025,.21,1.32),(.10,.29,.89),(.17,.31,.48)],.235,['scarf_back.00','scarf_back.01','scarf_back.02','scarf_back.03'])
 c.cowl(blue);c.belt(p['leather'],p['bronze'])
 branched_cross(c,'Front oath crest',(0,-.186,1.43),.065,p['ivory'])
 # Great helm: oval forged shell, narrow eye slit and a vented front plate.
 vs=[];fs=[];rings=[(1.715,.120,.108),(1.79,.129,.115),(1.90,.127,.116),(1.988,.105,.099),(2.018,.068,.068)];n=24
 for z,rx,ry in rings:
  for k in range(n):
   a=k/n*math.tau;vs.append((rx*cos(a),.010+ry*sin(a),z))
 for j in range(len(rings)-1):
  for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 fs.append(tuple((len(rings)-1)*n+k for k in range(n)))
 helm=c.mesh('Closed forged great helm',vs,fs,p['steel'],'head',smooth=False)
 bevel=helm.modifiers.new('Rounded helm edges','BEVEL');bevel.width=.003;bevel.segments=2
 for z,rx,ry in [(1.728,.123,.111),(1.918,.125,.115)]:
  pts=[(rx*cos(k/48*math.tau),.01+ry*sin(k/48*math.tau),z) for k in range(49)];c.tube('Helm riveted band',pts,[.0035]*len(pts),p['bronze'],'head',7)
 c.box('Deep horizontal visor slit',(0,-.111,1.887),(.165,.010,.012),p['shadow'],'head',.003)
 c.plate('Nasal reinforcing plate',[(-.015,-.118,1.962),(.015,-.118,1.962),(.020,-.127,1.77),(0,-.134,1.744),(-.020,-.127,1.77)],(0,-.139,1.855),p['bronze'],'head')
 for sign in [-1,1]:
  for row in range(3):
   for col in range(3):
    x=sign*(.038+col*.020);z=1.802+row*.019;y=.01-.116*math.sqrt(max(.1,1-(x/.129)**2))-.004
    c.ell('Helm dark breathing vent',(x,y,z),(.0045,.002,.0055),p['shadow'],'head')
  for z in [1.76,1.91,1.96]:c.ell('Helm bronze rivet',(sign*.087,-.079,z),(.0045,.003,.0045),p['bronze'],'head')
 # A removable shield is separate defensive equipment; no sword is created.
 sx=-.595;poly=[(sx-.18,-.14,1.52),(sx+.18,-.14,1.52),(sx+.19,-.15,1.10),(sx+.13,-.17,.79),(sx,-.18,.62),(sx-.14,-.17,.79),(sx-.19,-.15,1.10)]
 c.plate('Removable blue heater shield',poly,(sx,-.245,1.12),blue,'forearm.L',p['bronze'],equipment=True)
 c.line('Shield leather grip',(sx-.07,-.080,1.05),(sx+.07,-.080,1.05),.018,p['leather'],'forearm.L',True)
 branched_cross(c,'Shield broken oath heraldry',(sx,-.258,1.16),.155,p['ivory'],'forearm.L',True)
 for j in range(24):
  x=sx+random.uniform(-.15,.15);z=random.uniform(.83,1.47)
  c.line('Shield paint abrasion',(x,-.246,z),(x+.009,-.247,z+.024),.002,p['steel'],'forearm.L',True)
 c.finish((1.06,1.025,1.02))
def scholar():
 c=Character('ash_scholar','Ash Scholar','AshScholar',os.path.join(DOWNLOADS,'Ash Scholar Walking Sprite Atlas.png'));p=palette(c)
 ash=c.mat('ash-stained wool',(.069,.061,.055),rough=.97)
 hairmat=c.mat('dark wavy hair and beard',(.048,.023,.011),rough=.76,kind='hair')
 copper=c.mat('aged alchemical copper',(.27,.115,.033),metal=.72,rough=.49,kind='metal')
 ember=c.mat('smouldering ember edges',(.78,.092,.006),rough=.8,kind='cloth',emission=2.0)
 charskin=c.mat('ash-darkened forearm',(.16,.075,.037),rough=.83,kind='skin')
 c.set_base(ash,p['leather'],p['skin']);c.sleeves(ash,.091);c.cowl(p['black'])
 robe=c.robe('Scorched scholar robe',ash,.27,1.075,.38)
 c.panel('Scorched scholar back mantle',ash,[(0,.14,1.57),(.035,.20,1.25),(.11,.28,.80),(.19,.31,.38)],.24,['scarf_back.00','scarf_back.01','scarf_back.02','scarf_back.03'])
 c.harness(p['leather'],copper);c.belt(p['leather'],copper);hair(c,hairmat,False)
 for o in c.collection.objects:
  if o.name.startswith('Natural blond eyebrow'):o.data.materials.clear();o.data.materials.append(hairmat)
 # Beard follows the actual shared face surface, preserving its jaw and mouth shape.
 beard=c.face.copy();beard.data=c.face.data.copy();c.collection.objects.link(beard);beard.name='Short scholar beard surface'
 import bmesh
 bm=bmesh.new();bm.from_mesh(beard.data);remove=[]
 for face in bm.faces:
  q=beard.matrix_world@face.calc_center_median()
  if not (1.672<q.z<1.762 and q.y<-.018 and not (q.z>1.740 and abs(q.x)<.027)):remove.append(face)
 bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(beard.data);bm.free()
 for v in beard.data.vertices:v.co+=v.normal*.0016
 beard.data.materials.clear();beard.data.materials.append(hairmat)
 for mod in list(beard.modifiers):
  if mod.type=='ARMATURE':beard.modifiers.remove(mod)
 c.bind(beard,'head')
 for j in range(7):
  x=-.045+j*.015;c.tube('Short beard tuft',[(x,-.069,1.704),(x,-.072,1.691),(x+.002,-.070,1.678)],[.007,.006,.0005],hairmat,'head',10)
 # A copper circular apparatus and pendulum details sit behind the upper torso.
 centre=Vector((0,.205,1.52));r=.285
 pts=[centre+Vector((r*cos(k/64*math.tau),0,r*sin(k/64*math.tau))) for k in range(65)];c.tube('Removable copper back apparatus',pts,[.015]*len(pts),copper,'chest',12,True)
 for k in range(10):
  a=k/10*math.tau;root=centre+Vector((r*cos(a),0,r*sin(a)));tip=centre+Vector(((r+.045)*cos(a),0,(r+.045)*sin(a)))
  c.tube('Alchemical frame radial point',[root,tip],[.017,.0015],copper,'chest',10,True)
 for x in [-.18,.18]:
  c.line('Back apparatus mounting leather',(x,.137,1.37),(x,.205,1.59),.016,p['leather'],'chest',True)
 # Closed grimoire, pages, spine bands and a sun seal, held at the left hand.
 bp=Vector((-.505,-.103,1.045))
 c.box('Removable grimoire pages',bp,(.17,.060,.235),p['ivory'],'hand.L',.006,True)
 for y in [-.143,-.065]:c.box('Grimoire leather cover',(bp.x,y,bp.z),(.19,.014,.255),p['leather'],'hand.L',.004,True)
 c.box('Grimoire bound spine',(-.607,-.103,1.045),(.020,.092,.259),p['leather'],'hand.L',.004,True)
 for z in [.958,1.125]:c.box('Grimoire raised spine band',(-.620,-.103,z),(.009,.101,.018),copper,'hand.L',.002,True)
 c.sun('Grimoire sun seal',(-.505,-.155,1.045),.052,copper,'hand.L',True)
 for dx in [-.075,.075]:
  for dz in [-.104,.104]:c.box('Grimoire brass corner',(-.505+dx,-.155,1.045+dz),(.025,.008,.028),copper,'hand.L',.003,True)
 # Belt scroll cases and a copper astrolabe are distinct from future weapons.
 for sign in [-1,1]:
  x=sign*.229
  c.tube('Belt scroll case',[(x,-.012,.83),(x,-.012,1.075)],[.025,.025],p['leather'],'pelvis',16,True)
  for z in [.835,1.073]:c.ell('Scroll case copper cap',(x,-.012,z),(.030,.030,.012),copper,'pelvis',True)
 c.line('Astrolabe hanging chain',(.03,-.17,1.085),(.03,-.195,.91),.002,copper,'pelvis');c.sun('Belt astrolabe',(.03,-.20,.89),.041,copper,'pelvis')
 # Broken glowing lines follow the actual ragged hem rather than an oversized fire effect.
 verts=robe.data.vertices;cols=64;row=17
 for start in range(0,64,8):
  pts=[verts[row*cols+(start+k)%cols].co+Vector((0,0,.003)) for k in range(5)]
  c.tube('Scorched glowing hem',pts,[.0018]*len(pts),ember,'pelvis',6)
 lower=bpy.data.objects.get('Fitted lower sleeve.R')
 if lower:bpy.data.objects.remove(lower,do_unlink=True)
 c.tube('Ash-marked exposed forearm',[(.386,-.006,1.29),(.43,-.028,1.16),(.47,-.045,1.055)],[.067,.063,.047],charskin,'forearm.R',20)
 for j in range(6):
  z=1.09+j*.03;x=.461-j*.011
  c.tube('Glowing forearm fissure',[(x-.018,-.087,z),(x+.003,-.100,z+.014),(x+.023,-.083,z+.009)],[.001,.002,.0007],ember,'forearm.R',6)
 c.finish((.98,1,1))
if __name__=='__main__':
 args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['all']
 builders={'sister':sister,'ninja':ninja,'knight':knight,'scholar':scholar}
 if args[0]=='all':
  for build in builders.values():build()
 else:builders[args[0]]()
