import bpy, math, random, os
from mathutils import Vector
random.seed(28)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
OUT=os.path.dirname(os.path.abspath(__file__))

def mat(name, color, rough=.5, noise=0, scale=5):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1); p.inputs['Roughness'].default_value=rough
    if noise:
        t=n.new('ShaderNodeTexNoise'); t.inputs['Scale'].default_value=scale; t.inputs['Detail'].default_value=3
        r=n.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color=(*(c*.7 for c in color),1); r.color_ramp.elements[1].color=(*(min(1,c*1.15) for c in color),1)
        m.node_tree.links.new(t.outputs['Fac'],r.inputs[0]); m.node_tree.links.new(r.outputs[0],p.inputs['Base Color'])
        b=n.new('ShaderNodeBump'); b.inputs['Strength'].default_value=noise; b.inputs['Distance'].default_value=.07
        m.node_tree.links.new(t.outputs['Fac'],b.inputs['Height']); m.node_tree.links.new(b.outputs[0],p.inputs['Normal'])
    return m
stone=mat('Warm ivory • honed limestone',(.66,.61,.48),.8,.2,8)
plaster=mat('Lime plaster',(.84,.79,.66),.85,.09,5)
wood=mat('Oiled teak',(.25,.105,.039),.4,.13,4)
woodlight=mat('Teak decking',(.40,.23,.11),.55,.1,6)
roofmat=mat('Charcoal volcanic roof tiles',(.105,.125,.125),.72,.25,12)
roofline=mat('Tile raised seams',(.155,.17,.16),.7)
dark=mat('Blackened bronze',(.032,.040,.038),.3)
green=mat('Palm green',(.065,.22,.057),.48)
green2=mat('Fresh tropical leaves',(.17,.32,.055),.5)
trunkmat=mat('Palm bark',(.29,.21,.12),.9,.5,9)
grass=mat('Deep tropical lawn',(.095,.18,.044),.95,.3,34)
fabric=mat('Natural linen',(.89,.83,.68),.95,.15,50)
terra=mat('Terracotta',(.43,.19,.09),.8,.15)
pooltile=mat('Sukabumi green stone',(.09,.30,.27),.45,.18,22)
water=mat('Pool water',(.13,.47,.45),.09)
wp=water.node_tree.nodes.get('Principled BSDF'); wp.inputs['Transmission Weight'].default_value=.7; wp.inputs['IOR'].default_value=1.333
wn=water.node_tree.nodes.new('ShaderNodeTexNoise'); wn.inputs['Scale'].default_value=7; wn.inputs['Roughness'].default_value=.65
wb=water.node_tree.nodes.new('ShaderNodeBump'); wb.inputs['Strength'].default_value=.23; wb.inputs['Distance'].default_value=.065
water.node_tree.links.new(wn.outputs['Fac'],wb.inputs['Height']); water.node_tree.links.new(wb.outputs[0],wp.inputs['Normal'])
glow=mat('Warm lantern diffuser',(.95,.64,.28),.4); gp=glow.node_tree.nodes.get('Principled BSDF'); gp.inputs['Emission Color'].default_value=(1,.52,.18,1); gp.inputs['Emission Strength'].default_value=3

def cube(name,loc,dim,material,bevel=0):
    v=[(loc[0]+x*dim[0]/2,loc[1]+y*dim[1]/2,loc[2]+z*dim[2]/2) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    o=mesh(name,v,[(0,2,6,4),(1,5,7,3),(0,4,5,1),(2,3,7,6),(0,1,3,2),(4,6,7,5)],material)
    # Keep the origin at the centre for furniture rotations.
    for vert in o.data.vertices: vert.co-=Vector(loc)
    o.location=loc
    if bevel: b=o.modifiers.new('Soft crafted edges','BEVEL'); b.width=bevel; b.segments=2; o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return o
def mesh(name,verts,faces,material):
    m=bpy.data.meshes.new(name); m.from_pydata(verts,[],faces); m.update(); o=bpy.data.objects.new(name,m); bpy.context.collection.objects.link(o); o.data.materials.append(material); return o
def rod(name,a,b,r,material,r2=None):
    d=(Vector(b)-Vector(a)).normalized(); u=d.cross(Vector((0,0,1)))
    if u.length<.01:u=d.cross(Vector((0,1,0)))
    u.normalize(); v=d.cross(u); verts=[]
    for p,rad in [(a,r),(b,r if r2 is None else r2)]:
        verts.extend([tuple(Vector(p)+rad*(u*math.cos(i*math.tau/8)+v*math.sin(i*math.tau/8))) for i in range(8)])
    faces=[tuple(reversed(range(8))),tuple(range(8,16))]+[(i,(i+1)%8,(i+1)%8+8,i+8) for i in range(8)]
    return mesh(name,verts,faces,material)
def ball(name,p,s,material):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,location=p); o=bpy.context.object; o.name=name; o.scale=s; o.data.materials.append(material)
    for f in o.data.polygons:f.use_smooth=True
    return o
def hiproof(cx,cy,w,d,z,h):
    ridge=max(.6,(w-d)/2); pts=[(cx-w/2,cy-d/2,z),(cx+w/2,cy-d/2,z),(cx+w/2,cy+d/2,z),(cx-w/2,cy+d/2,z),(cx-ridge,cy,z+h),(cx+ridge,cy,z+h)]
    o=mesh('Broad hipped tile roof',pts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],roofmat); sol=o.modifiers.new('Tile thickness','SOLIDIFY'); sol.thickness=.14
    for a,b in [(0,1),(1,2),(2,3),(3,0),(0,4),(3,4),(1,5),(2,5),(4,5)]:rod('Roof ridge and hip cap',pts[a],pts[b],.065,roofline)
    # Horizontal tile courses trace the four pitched surfaces.
    for k in range(1,15):
        t=k/15; x0=cx-w/2*(1-t)-ridge*t; x1=cx+w/2*(1-t)+ridge*t; yy=d/2*(1-t); zz=z+h*t+.025
        for sy in [-1,1]:rod('Overlapping tile course',(x0,cy+sy*yy,zz),(x1,cy+sy*yy,zz),.023,roofline)
        for sx in [-1,1]:rod('Hip tile course',(cx+sx*(w/2*(1-t)+ridge*t),cy-yy,zz),(cx+sx*(w/2*(1-t)+ridge*t),cy+yy,zz),.023,roofline)
    cube('Teak roof fascia',(cx,cy-d/2,z-.10),(w,.17,.25),wood)

# Refined material palette, with grain measured in world units.
def surface(name,c1,c2,stretch=(1,1,1),rough=.6,bump=.12):
    m=mat(name,c1,rough); n=m.node_tree.nodes; l=m.node_tree.links; p=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord'); vm=n.new('ShaderNodeVectorMath'); vm.operation='MULTIPLY'; vm.inputs[1].default_value=stretch; l.new(tc.outputs['Object'],vm.inputs[0])
    no=n.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value=3; no.inputs['Detail'].default_value=4; no.inputs['Roughness'].default_value=.7; l.new(vm.outputs[0],no.inputs[0])
    ramp=n.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].color=(*c1,1); ramp.color_ramp.elements[1].color=(*c2,1); l.new(no.outputs['Fac'],ramp.inputs[0]); l.new(ramp.outputs[0],p.inputs['Base Color'])
    bu=n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value=bump; bu.inputs['Distance'].default_value=.025; l.new(no.outputs['Fac'],bu.inputs['Height']); l.new(bu.outputs[0],p.inputs['Normal']); return m
stone=surface('TRAVERTINE / warm cut stone',(.40,.35,.27),(.73,.67,.54),(1,1,4),.73,.23)
plaster=surface('MINERAL / hand applied lime',(.64,.61,.53),(.82,.77,.66),(2,2,2),.87,.1)
wood=surface('TEAK / long vertical grain',(.085,.036,.014),(.29,.15,.066),(9,9,.20),.4,.23)
woodlight=surface('TEAK / exterior boards',(.18,.095,.042),(.39,.25,.13),(.15,12,9),.48,.17)
basalt=surface('BASALT / split volcanic stone',(.047,.056,.047),(.16,.17,.14),(5,5,5),.88,.42)
fabric=surface('LINEN / natural ecru',(.68,.63,.52),(.86,.81,.70),(65,65,65),.94,.15)
accent=surface('TEXTILE / muted cinnamon',(.20,.075,.027),(.4,.18,.082),(55,55,55),.95,.1)
soil=surface('GARDEN / dark earth',(.018,.023,.012),(.075,.065,.032),(5,5,5),1,.4)
greens=[mat('Leaf tone %02d'%i,c,.43) for i,c in enumerate([(.022,.072,.015),(.040,.13,.028),(.078,.20,.038),(.13,.25,.053),(.047,.12,.055),(.16,.23,.048)])]
for m in greens:
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Subsurface Weight'].default_value=.045; p.inputs['Roughness'].default_value=.48
glass=mat('GLASS / clear architectural',(.89,.96,.97),.035); p=glass.node_tree.nodes.get('Principled BSDF'); p.inputs['Transmission Weight'].default_value=1; p.inputs['IOR'].default_value=1.46
water=mat('WATER / clear turquoise',(.40,.70,.68),.055); p=water.node_tree.nodes.get('Principled BSDF'); p.inputs['Transmission Weight'].default_value=1; p.inputs['IOR'].default_value=1.333
n=water.node_tree.nodes; l=water.node_tree.links; tc=n.new('ShaderNodeTexCoord'); no=n.new('ShaderNodeTexNoise'); no.inputs['Scale'].default_value=2.8; no.inputs['Detail'].default_value=2; l.new(tc.outputs['Object'],no.inputs[0]); bu=n.new('ShaderNodeBump'); bu.inputs['Strength'].default_value=.18; bu.inputs['Distance'].default_value=.045; l.new(no.outputs['Fac'],bu.inputs['Height']); l.new(bu.outputs[0],p.inputs['Normal'])
poolmats=[surface('SUKABUMI tile %02d'%i,(.045+i*.006,.14+i*.009,.12+i*.008),(.12+i*.007,.29+i*.008,.23+i*.006),(7,7,7),.6,.18) for i in range(6)]
roofmats=[surface('Slate shingle %02d'%i,(.026+i*.004,.032+i*.004,.032+i*.004),(.068+i*.005,.079+i*.005,.074+i*.005),(8,8,8),.75,.22) for i in range(7)]

# Efficient smooth ellipsoids; foliage itself is built from individual leaves.
def ball(name,p,s,material):
    verts=[]; faces=[]; seg=24; rings=12
    for j in range(rings+1):
        a=math.pi*j/rings
        for i in range(seg):
            t=math.tau*i/seg; verts.append((p[0]+s[0]*math.sin(a)*math.cos(t),p[1]+s[1]*math.sin(a)*math.sin(t),p[2]+s[2]*math.cos(a)))
    for j in range(rings):
        for i in range(seg):faces.append((j*seg+i,j*seg+(i+1)%seg,(j+1)*seg+(i+1)%seg,(j+1)*seg+i))
    o=mesh(name,verts,faces,material)
    for f in o.data.polygons:f.use_smooth=True
    return o
def line(name,points,r,m):
    cu=bpy.data.curves.new(name,'CURVE'); cu.dimensions='3D'; cu.bevel_depth=r; cu.bevel_resolution=2; sp=cu.splines.new('POLY'); sp.points.add(len(points)-1)
    for p,co in zip(sp.points,points):p.co=(*co,1)
    o=bpy.data.objects.new(name,cu); bpy.context.collection.objects.link(o); o.data.materials.append(m); return o
def area(name,p,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA'); d.energy=power; d.color=color; d.shape='DISK'; d.size=size; o=bpy.data.objects.new(name,d); bpy.context.collection.objects.link(o); o.location=p; o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def vessel(x,y,z,r=.32,h=.7):
    verts=[]; faces=[]; profile=[(0,.55),(.08,.78),(.35,1),(.65,.93),(.9,.58),(1,.56),(1,.46),(.88,.45)]
    for t,rr in profile:
        for j in range(40):verts.append((x+r*rr*math.cos(j*math.tau/40),y+r*rr*math.sin(j*math.tau/40),z+t*h))
    for k in range(len(profile)-1):
        for j in range(40):faces.append((k*40+j,k*40+(j+1)%40,(k+1)*40+(j+1)%40,(k+1)*40+j))
    o=mesh('Hand thrown ceramic vessel',verts,faces,terra)
    for f in o.data.polygons:f.use_smooth=True

# A continuous lawn with a pool opening, without overlapping ground faces.
lawn=surface('LAWN / fine emerald groundcover',(.028,.065,.016),(.09,.15,.038),(4,4,4),.95,.28)
mesh('Continuous landscaped ground',[(-120,-120,-.12),(120,-120,-.12),(120,120,-.12),(-120,120,-.12),(-6.1,-9.2,-.12),(6.1,-9.2,-.12),(6.1,-.8,-.12),(-6.1,-.8,-.12)],[(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],lawn)
cube('Terrace foundation',(0,5,.08),(24,10,.36),stone,.04)
for ix in range(24):
    for iy in range(10):cube('Travertine paver',(-11.5+ix,.5+iy,.30),(.989,.989,.08),stone,.009)
cube('Pool reinforced base',(0,-5,-1.12),(12.5,8.4,.2),poolmats[0])
for ix in range(40):
    for iy in range(27):cube('Green stone mosaic',(-5.85+ix*.3,-8.9+iy*.3,-1.009),(.295,.295,.025),random.choice(poolmats))
for x in [-6.10,6.10]:cube('Pool retaining side',(x,-5,-.46),(.2,8.2,1.4),poolmats[3])
for y in [-9.1,-.9]:cube('Pool retaining end',(0,y,-.46),(12.4,.2,1.4),poolmats[2])
cube('Pool water volume',(0,-5,-.43),(12,8,1.13),water)
for i in range(27):
    for x in [-6.36,6.36]:cube('Individual pool coping',(x,-8.9+i*.3,.25),(.50,.296,.18),stone,.015)
for i in range(42):
    for y in [-9.35,-.65]:cube('Individual pool coping',(-6.15+i*.3,y,.25),(.296,.50,.18),stone,.015)
for i in range(4):cube('Underwater entrance step',(-4.65,-1.25-i*.40,-.02-i*.22),(2.3,.42,.27),poolmats[4],.015)
for i in range(41):cube('Poolside deck teak board',(8.5,-9.4+i*.255,.21),(3.6,.242,.19),woodlight,.012)
for i in range(54):cube('Foreground deck teak board',(-6.7+i*.255,-10.3,.19),(.242,1.35,.16),woodlight,.012)
for x in [-5,-2,1,4]:
    cube('Pool underwater light',(x,-.995,-.22),(.22,.02,.10),glow,.02)
    area('Underwater light',(x,-1.08,-.15),(x,-5,-.8),18,(.38,.8,.74),.4)

def roof(cx,cy,w,d,z,h):
    # Each shingle follows one pitched roof plane, with alternating staggered joints.
    ridge=(w-d)/2
    pts=[(cx-w/2,cy-d/2,z),(cx+w/2,cy-d/2,z),(cx+w/2,cy+d/2,z),(cx-w/2,cy+d/2,z),(cx-ridge,cy,z+h),(cx+ridge,cy,z+h)]
    mesh('Hipped roof substrate',pts,[(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)],roofmats[0])
    for side in [-1,1]:
        for row in range(24):
            t=row/24; t2=(row+.98)/24; yy=side*d/2*(1-t); yy2=side*d/2*(1-t2); half=w/2*(1-t)+ridge*t; half2=w/2*(1-t2)+ridge*t2
            count=max(1,int(half*2/.32)); step=half*2/count
            for j in range(count):
                a=-half+j*step+.007; b=a+step-.014; a2=max(-half2,a); b2=min(half2,b)
                if b2<=a2:continue
                mesh('Individual slate shingle',[(cx+a,cy+yy,z+h*t+.026),(cx+b,cy+yy,z+h*t+.026),(cx+b2,cy+yy2,z+h*t2+.016),(cx+a2,cy+yy2,z+h*t2+.016)],[(0,1,2,3)],random.choice(roofmats))
        for row in range(24):
            t=row/24;t2=(row+.98)/24; a=d/2*(1-t); b=d/2*(1-t2); xx=side*(w/2*(1-t)+ridge*t); xx2=side*(w/2*(1-t2)+ridge*t2)
            count=max(1,int(a*2/.32))
            for j in range(count):
                y0=-a+j*2*a/count+.007; y1=-a+(j+1)*2*a/count-.007; y2=max(-b,y0); y3=min(b,y1)
                if y3>y2:mesh('Hip slate shingle',[(cx+xx,cy+y0,z+h*t+.025),(cx+xx,cy+y1,z+h*t+.025),(cx+xx2,cy+y3,z+h*t2+.015),(cx+xx2,cy+y2,z+h*t2+.015)],[(0,1,2,3)],random.choice(roofmats))
    for a,b in [(0,4),(1,5),(2,5),(3,4),(4,5)]:rod('Slate ridge cap',pts[a],pts[b],.065,roofmats[2])
    for y in [cy-d/2,cy+d/2]:cube('Deep dark timber fascia',(cx,y,z-.11),(w,.16,.28),wood,.018)
    for x in [cx-w/2,cx+w/2]:cube('Deep dark timber fascia',(x,cy,z-.11),(.16,d,.28),wood,.018)

# Main living pavilion: high hipped roof, solid exposed timber and open glazing.
cx=-1.7; cy=5.3; w=9.4; d=6.5
cube('Living pavilion slab',(cx,cy,.44),(w,d,.22),stone,.025)
cube('Living rear wall',(cx,8.45,2.24),(w,.28,3.6),plaster,.02)
cube('Living west wall',(-6.28,5.3,2.24),(.24,6.5,3.6),plaster,.02)
for x in [-6.0,2.6]:
    for y in [2.3,8.1]:cube('Primary timber post',(x,y,2.37),(.25,.25,3.85),wood,.025)
cube('Structural lintel',(cx,2.3,4.12),(9.0,.30,.32),wood,.015)
cube('Warm timber ceiling',(cx,cy,4.23),(9.9,7,.10),woodlight)
for x in [-6+i*.48 for i in range(19)]:cube('Expressed ceiling beams',(x,cy,4.12),(.095,6.4,.20),wood)
roof(cx,cy,10.8,7.9,4.4,2.45)
# Folded back glass door leaves, slender bronze frames.
for x in [-5.85,-5.15,2.0,2.65]:
    cube('Retracted sliding glass',(x,2.45,2.29),(.63,.025,3.50),glass)
    for dx in [-.33,.33]:cube('Bronze door stile',(x+dx,2.42,2.29),(.036,.065,3.58),dark,.004)
    for z in [.51,4.07]:cube('Bronze door rail',(x,2.42,z),(.68,.065,.035),dark)
cube('Flush sliding door track',(cx,2.3,.565),(8.8,.10,.015),dark)

def curtain(x,y,width,zbase=.56,height=3.43):
    verts=[];faces=[]; steps=42
    for j in range(11):
        t=j/10
        for i in range(steps+1):
            q=i/steps; verts.append((x+(q-.5)*width*(.85+.15*t),y+.065*math.sin(q*math.pi*16),zbase+height*(1-t)+.018*math.sin(q*math.pi*16)*t))
    for j in range(10):
        for i in range(steps):a=j*(steps+1)+i;faces.append((a,a+1,a+steps+2,a+steps+1))
    o=mesh('Soft gathered linen curtain',verts,faces,fabric)
    for f in o.data.polygons:f.use_smooth=True
for x in [-5.45,2.15]:curtain(x,2.65,.78)

def flatwing(x,y,w,d):
    cube('Bedroom raised floor',(x,y,.45),(w,d,.24),stone,.025)
    cube('Bedroom back wall',(x,y+d/2-.15,2.20),(w,.30,3.5),plaster)
    for sx in [-1,1]:cube('Bedroom stone pier',(x+sx*(w/2-.3),y,2.20),(.6,d,3.5),stone,.025)
    cube('Flat roof warm soffit',(x,y,3.99),(w+.65,d+.65,.15),woodlight)
    cube('Modern floating roof',(x,y,4.15),(w+.9,d+.9,.21),plaster,.03)
    cube('Roof shadow reveal',(x,y-d/2-.43,4.02),(w+.8,.04,.08),dark)
    front=y-d/2
    for xx in [x-w/2+.69,x+w/2-.69]:
        cube('Bedroom glass door',(xx,front+.04,2.25),(.7,.027,3.36),glass)
        for dx in [-.36,.36]:cube('Bedroom bronze door stile',(xx+dx,front,2.25),(.04,.075,3.45),dark)
        curtain(xx,front+.2,.65,.58,3.25)
    cube('Bed headboard',(x,y+1.6,1.42),(3.45,.17,1.7),wood,.025)
    cube('Floating bed plinth',(x,y+.20,.78),(2.9,2.5,.30),wood,.055)
    cube('Linen mattress',(x,y+.15,1.02),(2.8,2.4,.30),fabric,.13)
    cube('Folded duvet',(x,y-.1,1.20),(2.85,1.95,.17),fabric,.12)
    for xx in [-.68,.68]:
        o=cube('Linen sleeping pillow',(x+xx,y+1,1.32),(1.08,.62,.23),fabric,.10);o.rotation_euler[2]=random.uniform(-.07,.07)
    cube('Cinnamon bed throw',(x,y-.60,1.30),(2.89,.68,.055),accent,.025)
    for xx in [-1.85,1.85]:
        cube('Bedside stone table',(x+xx,y+1.2,.87),(.52,.55,.6),stone,.055)
        ball('Bedside lamp',(x+xx,y+1.2,1.39),(.20,.20,.24),fabric)
        area('Warm bedroom lamplight',(x+xx,y+1.1,1.8),(x,y,1),35,(1,.64,.33),.6)
    area('Bedroom ceiling light',(x,y,3.7),(x,y,.5),190,(1,.73,.47),3)
flatwing(-8.5,5.1,4.4,6.6)
flatwing(5.55,6.5,5.0,5.8)

# Volcanic feature wall between the bedroom and living volumes.
cube('Volcanic stone monolith',(3.45,5.6,2.50),(.72,7.2,4.35),basalt,.025)
for row in range(27):
    for col in range(4):cube('Split stone cladding',(3.10+col*.17,1.98-random.uniform(0,.025),.48+row*.15),(.162,.10,.14),basalt,.014)
# Right side pergola and dining terrace.
for x in [8.2,11.1]:
    for y in [2.1,7.8]:cube('Pergola teak upright',(x,y,1.98),(.18,.18,3.2),wood,.018)
for x in [8.2,11.1]:cube('Pergola long beam',(x,4.95,3.60),(.16,6.0,.25),wood,.01)
for j in range(22):cube('Pergola shade batten',(9.65,2.05+j*.28,3.76),(3.25,.10,.17),wood,.012)
cube('Outdoor dining table',(9.65,5,1.18),(1.65,2.5,.13),woodlight,.055)
for x in [9.05,10.25]:
    for y in [4.1,5.9]:cube('Dining table leg',(x,y,.77),(.1,.1,.75),wood)
for x in [8.45,10.85]:
    for y in [4.2,5.25,6.3]:
        cube('Dining chair seat',(x,y,.88),(.57,.62,.13),fabric,.065)
        for dx in [-.23,.23]:
            for dy in [-.23,.23]:rod('Dining chair leg',(x+dx,y+dy,.38),(x+dx,y+dy,.9),.028,wood)
        cube('Dining chair back',(x+(-.27 if x<9 else .27),y,1.17),(.09,.62,.58),wood,.045)
vessel(9.65,5,1.26,.14,.34)

# Living area: low sofa, woven rug and sculptural occasional chairs.
cube('Woven jute rug',(-1.7,4.9,.578),(6.4,3.65,.025),fabric,.03)
for i in range(80):cube('Rug woven stripe',(-4.82+i*.079,4.9,.594),(.017,3.54,.004),woodlight)
cube('Sofa low teak frame',(-1.7,6.75,.81),(4.8,1.18,.28),wood,.055)
cube('Sofa upholstered back',(-1.7,7.18,1.35),(4.9,.30,.88),fabric,.13)
for x in [-3.27,-1.7,-.13]:
    cube('Generous sofa cushion',(x,6.68,1.04),(1.52,1,.25),fabric,.105)
    o=cube('Loose linen pillow',(x-.26,7.0,1.53),(.68,.22,.61),accent if x==-1.7 else fabric,.105);o.rotation_euler[1]=-.16;o.rotation_euler[0]=-.12
for x in [-4.15,.75]:cube('Sofa rounded arm',(x,6.70,1.22),(.23,1.15,.58),fabric,.09)
ball('Travertine oval coffee table',(-1.7,4.65,.92),(1.35,.7,.12),stone)
for x in [-2.4,-1]:rod('Coffee table cylindrical base',(x,4.65,.59),(x,4.65,.88),.24,stone)
cube('Coffee table design book',(-1.95,4.55,1.06),(.48,.36,.055),fabric,.008)
vessel(-1.12,4.70,1.03,.15,.28)
for x in [-4.2,1]:
    cube('Lounge chair cushion',(x,3.95,.99),(.85,.92,.22),fabric,.085)
    for dx in [-.47,.47]:
        line('Sculpted teak chair arm',[(x+dx,3.45,.6),(x+dx,3.45,1.19),(x+dx,4.35,1.3),(x+dx,4.40,.58)],.045,wood)
    o=cube('Chair back cushion',(x,4.32,1.34),(.82,.16,.69),fabric,.08);o.rotation_euler[0]=-.15
# Minimal art niche and a textured circular carved panel.
cube('Recessed art niche',(-1.7,8.275,2.43),(3.1,.045,1.9),wood)
cube('Niche lime interior',(-1.7,8.238,2.43),(2.96,.025,1.76),stone)
for i in range(21):
    a=-1+i*.1; h=math.sqrt(max(0,1-a*a))*.70
    cube('Circular carved teak artwork',(-1.7+a*.75,8.20,2.43),(.037,.06,max(.02,2*h)),wood,.008)
area('Living warm fill',(-1.7,5.5,3.8),(-1.7,5,.6),340,(1,.77,.52),4)

# Woven open rattan pendants, with real gaps between ribs.
for x,y,z,r in [(-2.6,5.5,3.22,.48),(-.8,5.8,3.03,.37),(9.65,5,2.85,.40)]:
    rod('Pendant suspension',(x,y,z+.25),(x,y,4.05 if x<5 else 3.6),.012,dark)
    for j in range(36):
        a=j*math.tau/36; pts=[]
        for k in range(17):
            t=k/16; rr=r*(.38+.62*math.sin(math.pi*t)**.8);pts.append((x+rr*math.cos(a),y+rr*math.sin(a),z+.33-.65*t))
        line('Woven rattan pendant rib',pts,.008,woodlight)
    for k in range(8):
        t=k/7; rr=r*(.38+.62*math.sin(math.pi*t)**.8)
        line('Rattan horizontal weave',[(x+rr*math.cos(j*math.tau/64),y+rr*math.sin(j*math.tau/64),z+.33-.65*t) for j in range(65)],.006,woodlight)
    ball('Pendant warm bulb',(x,y,z),(.07,.07,.11),glow)

# Teak sun loungers with cushioned seats, seams and draped towels.
for y in [-6.6,-3.35]:
    cube('Sun lounger base',(8.25,y,.64),(2.7,1.05,.18),wood,.04)
    for x in [7.2,9.2]:
        for dy in [-.40,.40]:cube('Lounger foot',(x,y+dy,.42),(.12,.12,.34),wood,.02)
    cube('Lounger upholstered seat',(7.95,y,.81),(1.85,.94,.17),fabric,.065)
    o=cube('Lounger reclining back',(9.12,y,1.04),(.9,.94,.18),fabric,.065);o.rotation_euler[1]=-.48
    for dy in [-.445,.445]:line('Lounger stitched piping',[(7.08,y+dy,.875),(8.8,y+dy,.875)],.008,fabric)
    # A cloth strip bends down over the edge of the daybed.
    verts=[];faces=[]
    for j in range(20):
        t=j/19; yy=y-.20+t*.95; zz=.91 if t<.68 else .91-(t-.68)*1.30
        for i in range(12):verts.append((7.65+i*.037,yy,zz+.016*math.sin(i*1.6+t*2)))
    for j in range(19):
        for i in range(11):a=j*12+i;faces.append((a,a+1,a+13,a+12))
    mesh('Linen towel draped on lounger',verts,faces,fabric)
rod('Poolside table',(8.3,-4.97,.31),(8.3,-4.97,.86),.21,stone)
ball('Poolside table top',(8.3,-4.97,.88),(.43,.43,.065),stone)
vessel(8.3,-4.97,.94,.085,.19)

# Botanical geometry: curved folded leaves, rich crowns and irregular tree branching.
def blade_data(verts,faces,start,direction,length,width,arch=.25,droop=.3,segments=9):
    forward=Vector(direction).normalized(); side=forward.cross(Vector((0,0,1)))
    if side.length<.01:side=Vector((1,0,0))
    side.normalize(); base=len(verts)
    for i in range(segments+1):
        t=i/segments; c=Vector(start)+forward*length*t+Vector((0,0,arch*math.sin(math.pi*t)-droop*t*t)); widtht=width*math.sin(math.pi*t)**.7
        verts.extend([tuple(c-side*widtht),tuple(c+Vector((0,0,widtht*.18))),tuple(c+side*widtht)])
    for i in range(segments):
        a=base+i*3;faces.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
def foliage(name,verts,faces):
    o=mesh(name,verts,faces,greens[0])
    for m in greens[1:]:o.data.materials.append(m)
    for i,p in enumerate(o.data.polygons):p.material_index=(i//18*7)%len(greens);p.use_smooth=True
    return o
def palm(x,y,h,lean,phase):
    path=[(x+lean*(k/24)**1.5,y+.3*math.sin(k/24*2),.1+h*k/24) for k in range(25)]
    for i in range(24):rod('Coconut palm curved trunk',path[i],path[i+1],.21-.09*i/24,trunkmat,.21-.09*(i+1)/24)
    for i in range(int(h/.13)):
        t=i/(h/.13); p=Vector((x+lean*t**1.5,y+.3*math.sin(t*2),.1+h*t));rod('Close palm bark ring',p,p+Vector((0,0,.027)),.219-.09*t,trunkmat)
    top=Vector(path[-1]);verts=[];faces=[]
    for j in range(21):
        a=j*2.399+phase; length=random.uniform(3.2,4.6); lift=random.uniform(.2,1.7); drop=random.uniform(.8,2.2)
        pts=[]
        for k in range(31):
            t=k/30; p=top+Vector((math.cos(a)*length*t,math.sin(a)*length*t,lift*math.sin(math.pi*t)-drop*t*t));pts.append(tuple(p))
            if k in [0,30]:continue
            for side in [-1,1]:
                aa=a+side*random.uniform(.85,1.2); ll=(.20+.8*math.sin(math.pi*t)**.75)*random.uniform(.85,1.1)
                blade_data(verts,faces,p,(math.cos(aa),math.sin(aa),-.20-.25*t),ll,.038,.045,.20,5)
        line('Palm frond centre rib',pts,.013,greens[3])
    foliage('Dense natural coconut palm crown',verts,faces)
    for j in range(5):ball('Coconut',top+Vector((random.uniform(-.25,.25),random.uniform(-.25,.25),-.28)),(.16,.16,.21),trunkmat)
for args in [(-11.8,1,8.2,1.0,0),(-10,10,9.6,.6,1),(10.8,11,10.1,-.8,2),(12,-2,8.8,-.7,3),(-4,13,10.2,.7,4),(4,14,8.9,1,5)]:palm(*args)
def shrub(x,y,s=1,kind=0):
    verts=[];faces=[]
    for j in range(16 if kind==0 else 23):
        a=j*2.399+random.random()*.4; le=random.uniform(.65,1.35)*s; up=random.uniform(.4,1.4)
        blade_data(verts,faces,(x,y,.05),(math.cos(a),math.sin(a),up),le,(.14 if kind==0 else .07)*s,.16*s,.30*s)
    foliage('Tropical understorey',verts,faces)
def tree(x,y,h,spread):
    rod('Tropical hardwood trunk',(x,y,-.1),(x+.15,y,h*.67),.17,trunkmat,.075)
    verts=[];faces=[]
    for b in range(14):
        a=b*2.399; rr=random.uniform(.5,1)*spread; end=Vector((x+math.cos(a)*rr,y+math.sin(a)*rr,h+random.uniform(-1,1)))
        rod('Natural branching',(x+.15,y,h*.5),end,.06,trunkmat,.017)
        for k in range(420):
            p=end+Vector((random.gauss(0,.62),random.gauss(0,.62),random.gauss(0,.40)));aa=random.random()*math.tau
            blade_data(verts,faces,p,(math.cos(aa),math.sin(aa),random.uniform(-.4,.6)),random.uniform(.22,.40),random.uniform(.055,.10),.02,.06,3)
    foliage('Thousands of individual canopy leaves',verts,faces)
for i in range(15):tree(-22+i*3.15,random.uniform(13,17),random.uniform(5.7,8.5),random.uniform(1.4,2.4))
for x,y in [(-13,-1),(-14,4),(14,4),(15,9),(-16,10)]:tree(x,y,random.uniform(5,7),2)
cube('Private garden enclosure',(0,11.65,1.13),(31,.27,2.5),basalt,.03)
cube('Garden wall coping',(0,11.65,2.40),(31.15,.37,.11),stone,.015)
cube('West garden enclosure',(-14.6,5.1,1.13),(.27,13.1,2.5),basalt,.03)
for x in [-13+i*1.5 for i in range(19)]:shrub(x,10.8,random.uniform(1.2,1.8),1)
# Layered beds frame, rather than cover, the pool and architecture.
for side in [-1,1]:
    for j in range(36):
        x=side*random.uniform(10.9,14.5); y=random.uniform(-10,10);shrub(x,y,random.uniform(.6,1.35),j%2)
for j in range(28):shrub(random.uniform(-14,-7.1),random.uniform(-10,0),random.uniform(.5,1.25),j%2)
for x,y in [(-6.1,1.05),(3.7,1.6),(10.6,1.2)]:
    vessel(x,y,.35,.40,.78)
    verts=[];faces=[]
    for j in range(9):a=j*2.399;blade_data(verts,faces,(x,y,1.04),(math.cos(a),math.sin(a),1.5),1.05,.16,.28,.30)
    foliage('Potted tropical plant',verts,faces)
# Small ground blades and scattered smooth river stones.
verts=[];faces=[]
for j in range(13500):
    x=random.uniform(-19,19);y=random.uniform(-14,14)
    if (-10.9<x<10.5 and y>-.3) or (-7<x<10.6 and -11.1<y<.5):continue
    a=random.random()*math.tau;h=random.uniform(.06,.19);p=(x,y,-.09)
    blade_data(verts,faces,p,(math.cos(a)*.25,math.sin(a)*.25,1),h,.012,.01,.03,2)
foliage('Fine garden groundcover',verts,faces)
for i in range(7):
    cube('Floating garden stepping slab',(-8.4,-1.8-i*1.25,.09),(1.35,.79,.17),stone,.045)
    for j in range(9):
        x=-8.4+random.uniform(-1,1);y=-1.8-i*1.25+random.choice([-1,1])*.53
        ball('River pebble',(x,y,-.03),(random.uniform(.045,.12),random.uniform(.05,.12),random.uniform(.03,.07)),basalt)

# Discreet garden lighting and stone water bowl.
for x,y in [(-7,-8.6),(-9.7,-3),(10.4,-8),(-5.9,1),(3.7,1.1),(10.7,1.2)]:
    cube('Garden lantern plinth',(x,y,.20),(.29,.29,.28),basalt,.02)
    cube('Garden lantern diffuser',(x,y,.45),(.19,.19,.23),glow,.01)
    cube('Garden lantern roof',(x,y,.60),(.33,.33,.055),dark,.01)
    for dx in [-.12,.12]:
        for dy in [-.12,.12]:rod('Lantern corner',(x+dx,y+dy,.30),(x+dx,y+dy,.6),.014,dark)
    area('Garden pool of light',(x,y,.7),(x,y,0),12,(1,.65,.32),.5)
vessel(-10,1.1,.34,.70,.46)

# Cinematic, low architectural camera and soft directional tropical daylight.
world=bpy.data.worlds.new('Warm tropical sky');world.use_nodes=True;bpy.context.scene.world=world
no=world.node_tree.nodes;li=world.node_tree.links; sky=no.new('ShaderNodeTexSky');sky.sky_type='HOSEK_WILKIE';sky.sun_direction=Vector((-.5,-.6,.42)).normalized();sky.turbidity=3;sky.ground_albedo=.25;li.new(sky.outputs[0],no.get('Background').inputs[0]);no.get('Background').inputs['Strength'].default_value=.55
visible_sky=no.new('ShaderNodeBackground');visible_sky.inputs[0].default_value=(.40,.57,.74,1);visible_sky.inputs[1].default_value=.8
lp=no.new('ShaderNodeLightPath');mix=no.new('ShaderNodeMixShader');li.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);li.new(no.get('Background').outputs[0],mix.inputs[1]);li.new(visible_sky.outputs[0],mix.inputs[2]);li.new(mix.outputs[0],no.get('World Output').inputs['Surface'])
sd=bpy.data.lights.new('Late afternoon sun','SUN');so=bpy.data.objects.new('Late afternoon sun',sd);bpy.context.collection.objects.link(so);so.rotation_euler=Vector((.5,.6,-.7)).to_track_quat('-Z','Y').to_euler();sd.energy=3.0;sd.angle=math.radians(3);sd.color=(1,.86,.69)
area('Large soft sky fill',(0,-6,13),(0,3,1),1500,(.72,.84,1),13)
bpy.ops.object.camera_add(location=(15.8,-25.4,7.4));cam=bpy.context.object;cam.name='Camera • poolside hero';cam.rotation_euler=(Vector((-.2,2.4,2.50))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=40;cam.data.clip_end=300
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=True;scene.cycles.max_bounces=10;scene.cycles.transmission_bounces=8;scene.cycles.adaptive_threshold=.025
scene.render.resolution_x=2400;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.6
scene.render.image_settings.file_format='PNG';scene.render.filepath=os.path.join(OUT,'modern_balinese_villa_v2.png')
bpy.ops.object.camera_add(location=(7.5,-13.6,3.35));detail=bpy.context.object;detail.name='Camera • intimate poolside';detail.rotation_euler=(Vector((-1.25,4.3,2.1))-detail.location).to_track_quat('-Z','Y').to_euler();detail.data.lens=32;detail.data.clip_end=300
scene['Design']='Modern Balinese courtyard villa / slate pavilion, travertine, teak and Sukabumi stone'
scene['Views']='Main overview and intimate poolside camera; all materials and vegetation are procedural and self-contained.'
scene.camera=cam
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'modern_balinese_villa_v2.blend'))
bpy.ops.render.render(write_still=True)
scene.camera=detail;scene.render.resolution_x=2000;scene.render.resolution_y=1400;scene.render.filepath=os.path.join(OUT,'modern_balinese_villa_v2_poolside.png')
bpy.ops.render.render(write_still=True)
# Restore the overview as the default view in the editable project.
scene.camera=cam;scene.render.resolution_x=2400;scene.render.resolution_y=1600;scene.render.filepath=os.path.join(OUT,'modern_balinese_villa_v2.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'modern_balinese_villa_v2.blend'))
print('Completed both villa renders and saved the editable scene.',flush=True)
# Avoid PulseAudio teardown hanging in a headless sandbox after all files are saved.
os._exit(0)
