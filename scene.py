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

# Site, terraces and recessed swimming pool.
cube('Earth plinth',(0,1,-.38),(43,37,.6),grass,.1)
cube('Main travertine terrace',(0,5,.03),(25,10,.36),stone,.06)
cube('Pool basin',(0,-4,-.30),(12,6.7,.38),pooltile,.05)
for x in [-6.15,6.15]:cube('Pool side wall',(x,-4,-.12),(.3,7,.72),pooltile)
for y in [-7.45,-.55]:cube('Pool end wall',(0,y,-.12),(12.6,.3,.72),pooltile)
cube('Still water with small ripples',(0,-4,.055),(12,6.6,.025),water)
for x in [-6.48,6.48]:cube('Limestone pool coping',(x,-4,.20),(.65,6.86,.24),stone,.035)
for y in [-7.72,-.28]:cube('Limestone pool coping',(0,y,.20),(13.6,.55,.24),stone,.035)
for i in range(34):cube('Pool front deck board',(-6.65+i*.40,-9,.11),(.38,2.0,.18),woodlight,.015)
for i in range(19):cube('Side sun deck board',(8.55,-7.1+i*.39,.12),(3.5,.37,.20),woodlight,.012)
# Large format terrace joints.
for x in range(-12,13,2):cube('Terrace stone joint',(x,5,.214),(.012,9.9,.004),roofmat)
for y in range(0,10,2):cube('Terrace stone joint',(0,y,.214),(24.7,.012,.004),roofmat)

def pavilion(cx,cy,w,d,main=False):
    floor=.38; height=3.6
    cube('Raised pavilion floor',(cx,cy,.28),(w,d,.24),stone,.04)
    cube('Back limewashed wall',(cx,cy+d/2-.15,2.05),(w,.30,3.5),plaster)
    cube('Side limestone wall',(cx-w/2+.15,cy,2.05),(.30,d,3.5),stone)
    for px in [cx-w/2+.32,cx+w/2-.32]:
        for py in [cy-d/2+.25,cy+d/2-.25]:cube('Solid teak column',(px,py,2.10),(.24,.24,3.6),wood,.025)
    cube('Open front teak lintel',(cx,cy-d/2+.22,3.8),(w,.26,.26),wood)
    cube('Timber soffit',(cx,cy,3.83),(w+.5,d+.5,.12),woodlight)
    for xx in range(int(w/.45)):
        cube('Exposed ceiling rafter',(cx-w/2+xx*.45,cy,3.71),(.085,d,.14),wood)
    hiproof(cx,cy,w+1.5,d+1.5,4.02,2 if main else 1.6)
    # Stacked pocket screens keep the facade open to the garden.
    for edge in [-1,1]:
        bx=cx+edge*(w/2-.8)
        for i in range(8):cube('Vertical teak screen',(bx+(i-3.5)*.15,cy-d/2+.15,2.05),(.055,.10,3.22),wood,.012)
    if main:
        cube('Living room rug',(cx,cy-.35,.419),(4.7,3.3,.035),fabric,.04)
        cube('Sofa teak base',(cx,cy+1,.69),(4.1,1.10,.42),wood,.06)
        cube('Linen sofa back',(cx,cy+1.43,1.18),(4.1,.23,.85),fabric,.12)
        for xx in [-1.32,0,1.32]:
            cube('Deep linen seat',(cx+xx,cy+.94,.96),(1.28,.91,.25),fabric,.10)
            p=cube('Loose sofa cushion',(cx+xx,cy+1.23,1.35),(.64,.18,.52),terra if xx==0 else fabric,.09); p.rotation_euler[1]=.1
        cube('Low stone coffee table',(cx,cy-.7,.77),(2.3,1.1,.14),stone,.07)
        for xx in [-.8,.8]:cube('Coffee table leg',(cx+xx,cy-.7,.57),(.15,.7,.36),wood)
        ball('Ceramic bowl',(cx,cy-.7,.88),(.3,.3,.10),terra)
        for xx in [-2.7,2.7]:
            cube('Lounge chair seat',(cx+xx,cy-.45,.8),(.85,.9,.20),fabric,.07)
            cube('Lounge chair back',(cx+xx,cy-.02,1.15),(.85,.14,.65),wood,.03)
            for dx in [-.34,.34]:
                for dy in [-.34,.34]:rod('Chair leg',(cx+xx+dx,cy-.45+dy,.4),(cx+xx+dx,cy-.45+dy,.77),.04,wood)
        cube('Art panel bronze frame',(cx,cy+d/2-.33,2.22),(2.5,.06,1.6),wood)
        cube('Woven art',(cx,cy+d/2-.38,2.22),(2.3,.04,1.4),fabric)
        for i in range(7):ball('Abstract wall relief',(cx-.85+i*.29,cy+d/2-.42,2.22+.25*math.sin(i)),(.09,.03,.36),woodlight)
    else:
        cube('Bed timber platform',(cx,cy+.3,.63),(2.8,2.5,.40),wood,.04)
        cube('Crisp linen duvet',(cx,cy+.15,.95),(2.7,2.35,.35),fabric,.14)
        cube('Teak headboard',(cx,cy+1.5,1.25),(3.3,.16,1.6),wood,.02)
        for xx in [-.7,.7]:cube('Bed pillow',(cx+xx,cy+.9,1.19),(1,.65,.2),fabric,.1)
        cube('Ochre bed runner',(cx,cy-.55,1.14),(2.72,.65,.06),terra,.025)

pavilion(-.8,4.6,8.3,5.6,True)
pavilion(-8.1,3.6,5.0,5.4)
pavilion(7,5.5,5.6,5.5)
# Stone feature wall in the garden.
cube('Garden feature wall',(11.3,5,1.45),(.5,9,2.6),roofmat)
for row in range(10):
    for j in range(14):cube('Hand laid volcanic stone',(10.99,.6+j*.63+(row%2)*.22,.30+row*.245),(.16,.58,.21),stone if random.random()<.12 else roofline,.025)
# Pool steps, stepping stones and loungers.
for i in range(3):cube('Submerged entry stair',(-4.6,-1.05-i*.40,-.02-i*.11),(2.0,.43,.18),pooltile,.025)
cube('Pavilion broad entry stair',(-.8,.30,.28),(7.1,.6,.18),stone,.03)
for j in range(6):cube('Garden stepping stone',(-9.3,-2.1-j*1.28,.02),(1.4,.87,.14),stone,.035)
for y in [-5.5,-2.8]:
    cube('Sun lounger teak frame',(8.4,y,.48),(2.55,1.02,.20),wood,.06)
    cube('Sun lounger linen pad',(8.18,y,.64),(1.95,.91,.18),fabric,.09)
    o=cube('Inclined lounger back',(9.25,y,.93),(.85,.91,.17),fabric,.07); o.rotation_euler[1]=-.48
    for x in [7.45,9.3]:cube('Lounger feet',(x,y,.31),(.15,.85,.32),wood,.025)
rod('Round side table pedestal',(8.4,-4.15,.21),(8.4,-4.15,.68),.08,wood)
bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.38,depth=.08,location=(8.4,-4.15,.72)); bpy.context.object.data.materials.append(stone)

def leaf(name,start,angle,length,width,lift,material):
    verts=[]; steps=10
    for k in range(steps+1):
        t=k/steps; spread=width*math.sin(math.pi*t)**.65; dist=length*t
        center=Vector(start)+Vector((math.cos(angle)*dist,math.sin(angle)*dist,lift*math.sin(math.pi*t*.8)-length*.21*t*t))
        side=Vector((-math.sin(angle),math.cos(angle),0))
        verts += [tuple(center-side*spread),tuple(center+Vector((0,0,.055*math.sin(math.pi*t)))),tuple(center+side*spread)]
    faces=[]
    for k in range(steps):
        a=k*3; faces.extend([(a,a+3,a+4,a+1),(a+1,a+4,a+5,a+2)])
    return mesh(name,verts,faces,material)
def palm(x,y,h,lean=.6):
    path=[]
    for k in range(15):
        t=k/14; path.append((x+lean*t*t,y+.22*t*t,.1+h*t))
    for i in range(14):
        rod('Curved coconut palm trunk',path[i],path[i+1],.20-.085*i/14,trunkmat,.20-.085*(i+1)/14)
        p=path[i]; rod('Palm bark ring',(p[0],p[1],p[2]-.015),(p[0],p[1],p[2]+.025),.21-.085*i/14,woodlight)
    top=Vector(path[-1])
    for n in range(11):
        ang=n*math.tau/11+random.random()*.3; length=random.uniform(2.6,3.8)
        end=top+Vector((math.cos(ang)*length,math.sin(ang)*length,-.7))
        # Each frond is a curved rachis with paired fine leaflets.
        prev=top
        for k in range(1,14):
            t=k/13; p=top+Vector((math.cos(ang)*length*t,math.sin(ang)*length*t,1.0*math.sin(math.pi*t)-.7*t*t))
            rod('Palm frond rib',prev,p,.017,green2); prev=p
            for side in [-1,1]:leaf('Palm leaflet',p,ang+side*1.0,.85*math.sin(math.pi*t)**.5+.12,.065,.05,green if n%3 else green2)
    for n in range(4):ball('Coconut',top+Vector((random.uniform(-.22,.22),random.uniform(-.22,.22),-.18)),(.15,.15,.19),trunkmat)
for args in [(-12,1,7.1,.65),(-12,9,8.5,.8),(12,9,9,-.6),(13,-3,7.8,-.8),(-7,12,8,.3),(4,12,8.6,.5)]:palm(*args)
def plant(x,y,size=1):
    for j in range(9):leaf('Broad tropical foliage',(x,y,.14),j*2.4,random.uniform(.6,1.2)*size,.17*size,random.uniform(.5,1.1)*size,green if j%2 else green2)
for x,y in [(-11,-2),(-11,-4),(-11,-6),(-12,5),(11,-1),(11,1),(11,3),(-5,10),(2,10),(10,10),(-13,8)]:
    for k in range(4):plant(x+random.uniform(-.7,.7),y+random.uniform(-.6,.6),random.uniform(.8,1.4))
for x,y in [(-5.5,1), (4.1,2)]:
    bpy.ops.mesh.primitive_cone_add(vertices=40,radius1=.28,radius2=.43,depth=.68,location=(x,y,.56)); bpy.context.object.data.materials.append(terra)
    for i in range(8):leaf('Potted greenery',(x,y,.88),i*2.4,1,.18,1.1,green)
for x,y in [(-6.8,-7.5),(6.9,-7.5),(-5.2,.3),(4.3,.3),(-10,-1)]:
    cube('Garden lantern stone base',(x,y,.35),(.43,.43,.40),roofmat,.04)
    cube('Lantern glowing glass',(x,y,.68),(.28,.28,.29),glow,.015)
    cube('Lantern cap',(x,y,.88),(.45,.45,.09),dark,.02)
    for dx in [-.17,.17]:
        for dy in [-.17,.17]:rod('Lantern metal corner',(x+dx,y+dy,.48),(x+dx,y+dy,.85),.018,dark)
for x,y in [(-.8,4.4),(-8.1,3.4),(7,5.5)]:
    rod('Pendant cable',(x,y,3.75),(x,y,3.08),.016,dark)
    ball('Woven rattan pendant',(x,y,2.92),(.55,.55,.32),woodlight)
    ball('Pendant light',(x,y,2.77),(.22,.22,.10),glow)
    bpy.ops.object.light_add(type='AREA',location=(x,y,3.1)); bpy.context.object.data.energy=180; bpy.context.object.data.color=(1,.69,.40); bpy.context.object.data.shape='DISK'; bpy.context.object.data.size=3

# A garden hedge with small irregular clusters behind the architecture.
for i in range(95):
    x=random.uniform(-20,20); y=random.uniform(12,16)
    ball('Distant tropical canopy',(x,y,random.uniform(.5,1.2)),(random.uniform(.5,1.1),.8,random.uniform(.5,1.1)),green)

world=bpy.data.worlds.new('Tropical late afternoon'); bpy.context.scene.world=world; world.use_nodes=True
nodes=world.node_tree.nodes; sky=nodes.new('ShaderNodeTexSky'); sky.sky_type='MULTIPLE_SCATTERING'; sky.sun_elevation=math.radians(24); sky.sun_rotation=math.radians(220); sky.altitude=.1; sky.air_density=1.2
nodes.get('Background').inputs['Color'].default_value=(.48,.65,.83,1); nodes.get('Background').inputs['Strength'].default_value=.45
cube('Landscape to horizon',(0,0,-.73),(2000,2000,.1),grass)
bpy.ops.object.light_add(type='SUN',location=(-12,-10,15)); sun=bpy.context.object; sun.rotation_euler=(math.radians(32),math.radians(-28),math.radians(-35)); sun.data.energy=2.4; sun.data.angle=math.radians(6); sun.data.color=(1,.83,.64)
bpy.ops.object.camera_add(location=(22,-32,15.4)); cam=bpy.context.object; cam.rotation_euler=(Vector((0,2.1,2.1))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='PERSP'; cam.data.lens=47
scene=bpy.context.scene; scene.camera=cam; scene.render.engine='CYCLES'; scene.cycles.samples=48; scene.cycles.use_denoising=True
scene.render.resolution_x=1600; scene.render.resolution_y=1100; scene.render.resolution_percentage=100
scene.world.color=(.3,.3,.3); scene.view_settings.view_transform='AgX'
scene.render.image_settings.file_format='PNG'; scene.render.filepath=os.path.join(OUT,'modern_balinese_villa.png')
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'modern_balinese_villa.blend'))
bpy.ops.render.render(write_still=True)
