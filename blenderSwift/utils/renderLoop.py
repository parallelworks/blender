import bpy
import math
import sys
import json
import random
import numpy as np

bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'

# File containing the json formated input
so=open(sys.argv[4],'r')
# Path for the output file
path2blended=sys.argv[5]
sceneNumber=int(sys.argv[6])
Nloop=int(sys.argv[7])
camTraject=np.load(sys.argv[8])

# Defines the relative position between an object's location and its focus point
class relativePosition():
  def __init__(self):
    # If options='none' specify:
     self.focus=(0,0,0)
     self.location=(0,0,0)
    # Else:
     # Camera options:
     # iso1, iso2, iso3, iso4, front, back, top, bottom, left, right, none
     self.option='none'
     # Relative distance distance
     # Zero value will trigger the default option
     self.distance=0
     # Object will look towards the focus object (imported volume)
     self.focusObject='def'
  # Moves the object to the (x,y,z) location calculated from relativePosition.self
  def setLocation(self,ob):
     if self.option!='none':
        focusOb=bpy.data.objects[lightPos.focusObject]
        objectSize=focusOb.dimensions
        objectLocation=focusOb.location
        p1=-(objectLocation[0]+objectSize[0])/2
        p2=(objectLocation[1]+objectSize[1])/2
        p3=(objectLocation[2]+objectSize[2])/2
        self.focus=(p1,p2,p3)
        # Determining distance option
        if self.distance==0:
           self.distance=3*max(objectLocation[0]+objectSize[0],objectLocation[1]+objectSize[1],objectLocation[2]+objectSize[2])
        # Determining location option
        if self.option=='iso1':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,self.distance*cos45,self.distance*cos45)
        elif self.option=='iso2':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,-self.distance*cos45,self.distance*cos45)
        elif self.option=='iso3':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,-self.distance*cos45,-self.distance*cos45)
        elif self.option=='iso4':
           cos45=math.cos(math.pi/4)
           self.location=(-self.distance*cos45,self.distance*cos45,-self.distance*cos45)
        elif self.option=='front':
           self.location=(p1,p2,self.distance)
        elif self.option=='back':
           self.location=(p1,p2,-self.distance)
        elif self.option=='right':
           self.location=(p1,self.distance,p3)
        elif self.option=='left':
           self.location=(p1,-self.distance,p3)
        elif self.option=='up':
           self.location=(-self.distance,p2,p3)
        elif self.option=='down':
           self.location=(self.distance,p2,p3)
     else: # User defined focusPoint and camLocation --> calc distance
        r=0
        for i in range(3):
           aux=self.focus[i]-self.location[i]
           r=r+aux*aux
        self.distance=math.sqrt(r)
     ob.location=self.location
     return ob
  # Orientates the object such that that it looks from the self.location to self.focus
  # The angles are defined using the aircraft convention where the (y,z) plane is the 
  # ground and x is the vertical axis
  def setOrientation(self,ob):
     roll=math.pi/2 # Always parallel to the ground
     rr=0
     for i in range(2):
         aux=self.focus[i+1]-self.location[i+1]
         rr=rr+aux*aux
     # Distance in the (y,z) plane from the self.focus to self.location
     radius=math.sqrt(rr)
     x=self.location[2]-self.focus[2]
     y=self.location[1]-self.focus[1]
     z=self.location[0]-self.focus[0]
     yaw=math.atan2(y,x)
     # Distance to the (y,z) plane along the x axis
     height=z
     pitch=math.atan2(height,radius)
     ob.rotation_euler=(pitch,yaw,roll)
     return ob
        

def assignMaterial(ob,matOption,color,lightIntensity):
    if matOption=="glass":
       ob=assignGlassMaterial(ob)
    elif matOption=="water":
       ob=assignWaterMaterial(ob)
    elif matOption=="mirror":
       ob=assignMirrorMaterial(ob)
    elif matOption=="color":
       ob=assignColorMaterial(ob,color)
    elif matOption=="light":
       ob=assignColorMaterial(ob,color,lightIntensity)
    elif matOption=="image":
       ob=assignGrassMaterial(ob)
    elif matOption=="original":
       ob=assignOriginalMaterial(ob)
    return ob

def assignGrassMaterial(waterObject):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=waterObject
    mat = bpy.data.materials.new(name="Water")
    setMaterial(waterObject,mat)
    cmat=waterObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    node_glass = TreeNodes.nodes.new(type='ShaderNodeBsdfDiffuse')
    links.new(node_glass.outputs[0], node_out.inputs[0])
    node_grass = TreeNodes.nodes.new(type="ShaderNodeTexImage")
    newimg=bpy.data.images.load('inputs/grass.jpg')
    node_grass.image = newimg
    links.new(node_grass.outputs[0],node_glass.inputs[0])
    node_noise = TreeNodes.nodes.new(type="ShaderNodeTexNoise")
    links.new(node_noise.outputs[0],node_out.inputs[2])
    return waterObject

def assignOriginalMaterial(waterObject):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=waterObject
    mat = bpy.data.materials.new(name="Water")
    setMaterial(waterObject,mat)
    cmat=waterObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    node_glass = TreeNodes.nodes.new(type='ShaderNodeBsdfDiffuse')
    links.new(node_glass.outputs[0], node_out.inputs[0])
    #node_Attribute = TreeNodes.nodes.new(type='Attribute')
    node_Attribute = TreeNodes.nodes.new(type='ShaderNodeAttribute')
    node_Attribute.attribute_name='Col'
    #node_Attribute.inputs[0].attribute_name='Col'
#    node_light.inputs[0].default_value= color #(1,1,1,0)
    links.new(node_Attribute.outputs[0], node_glass.inputs[0])
    return waterObject


def assignColorMaterial(ob,color):
    mat = bpy.data.materials.new('colorMat')
    mat.diffuse_color = color
    setMaterial(ob,mat)
    return ob

# MAKE NODE-BASED MATERIAL FOR CYCLES_RENDER
def assignGlassMaterial(glassObject):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=glassObject 
    mat=bpy.data.materials.new(name="Glass")
    setMaterial(glassObject,mat)
    cmat=glassObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    # Remove nodes (clean it)
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    # Add the guy to the node view
    # Output node
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    # Toon
    #node_Toon = TreeNodes.nodes.new(type='ShaderNodeBsdfTransparent')
    node_Toon = TreeNodes.nodes.new(type='ShaderNodeBsdfGlass')
    node_Toon.location = 0,0
    # Activate to select color
    #node_Toon.inputs[0].default_value = (0.488,0.66,0.58,1)  # green RGBA
    node_Toon.inputs[1].default_value = 0.00  
    node_Toon.inputs[2].default_value = 0.00 
    # Connect the guys
    links.new(node_Toon.outputs[0], node_out.inputs[0])
    return glassObject

def assignMirrorMaterial(mirrorObject):
    matName = 'planeGlass'
    bpy.data.materials.new(matName)
    bpy.data.materials[matName].use_nodes = True
    bpy.data.materials[matName].node_tree.nodes.new(type='ShaderNodeBsdfGlass')
    inp = bpy.data.materials[matName].node_tree.nodes['Material Output'].inputs['Surface']
    outp = bpy.data.materials[matName].node_tree.nodes['Glass BSDF'].outputs['BSDF']
    bpy.data.materials[matName].node_tree.links.new(inp,outp)
    mirrorObject.active_material = bpy.data.materials[matName]
    return mirrorObject


def assignWaterMaterial(waterObject):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=waterObject
    mat = bpy.data.materials.new(name="Water")
    setMaterial(waterObject,mat)
    cmat=waterObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    node_glass = TreeNodes.nodes.new(type='ShaderNodeBsdfGlass')
    node_glass.location =0,180
    node_glass.distribution = 'GGX'
    node_glass.inputs['Color'].default_value= (0.619,0.727,0.8,1)
    node_glass.inputs['Roughness'].default_value=0.34
    node_glass.inputs['IOR'].default_value=1.333
    links.new(node_glass.outputs[0], node_out.inputs[0])
    return waterObject

def assignLightMaterial(lightObject,color,intensity):
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active=lightObject
    mat = bpy.data.materials.new(name="Light")
    setMaterial(lightObject,mat)
    cmat=lightObject.active_material
    cmat.use_nodes=True
    TreeNodes=cmat.node_tree
    links = TreeNodes.links
    for node in TreeNodes.nodes:
        TreeNodes.nodes.remove(node)
    node_out = TreeNodes.nodes.new(type='ShaderNodeOutputMaterial')
    node_out.location = 200,0
    node_light = TreeNodes.nodes.new(type='ShaderNodeEmission')
    node_light.location =0,0
    # First 3 values select color. Last one not sure.
    node_light.inputs[0].default_value= color #(1,1,1,0)
    node_light.inputs[1].default_value=intensity #
    links.new(node_light.outputs[0],node_out.inputs[0])
    return lightObject



def setMaterial(ob, mat):
    me = ob.data
    if len(me.materials):
       ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    return ob 


## Keeps track and renames or eliminates the imported objects according to their type and 
# the order in wich they are imported.
# Note 1: When a mesh is imported into blender it comes with default lamps and camera
# Note 2: In the current version of the code imported cameras and lamps are deleted
class objectList():
  def __init__(self):
    self.N_Object=0 # Total number of objects
    self.N_Camera=0 # Total number of cameras (Should remain =0 in current version)
    self.N_Lamp=0  # Total number of lamps (Should reamin =0 in current version)
    self.N_Mesh=0 # Total number of meshes
  # Renames the objects according to their type and the order in which they are imported
  # such that their name is Type.order
  def rename(self,item):
    self.N_Object=self.N_Object+1
    print(("Object %s") % self.N_Object)
    print(("Type: %s") % item.type)
    if item.type=='MESH':
      self.N_Mesh=self.N_Mesh+1
      oldDefName=item.name
      print(("Previous default name: %s") % item.name)
      newDefName="Mesh%s" % self.N_Mesh
      bpy.data.objects[oldDefName].name = newDefName
      print(("Current default name: %s") % item.name)
    elif item.type=='CAMERA':
      bpy.data.objects[item.name].select = True
      print(("Deleted: %s") % item.name)
      bpy.ops.object.delete() # Deletes cameras
      self.N_Object=self.N_Object-1
    elif item.type=='LAMP':
      bpy.data.objects[item.name].select = True
      print(("Deleted: %s") % item.name)
      bpy.ops.object.delete() # Deletes lamps
      self.N_Object=self.N_Object-1
    else:
      print(("WARNING - Unrecognized item type: %s") % item.name)
      print('\n')
    return item

# Defines the path to the .x3d files and the assigned material
class mesh():
  def __init__(self):
     self.path2mesh='def'
     self.material='def'
     self.color=(0,0,0)
     self.lightIntensity=0
class sceneOptions():
  def __init__(self):
     # Ground options
     self.groundSize=0
     self.groundMaterial='def'
     self.groundColor=(0.8,0.8,0.8)
     # Light options
     # First 3 numbers define color. Not sure what the last number does.
     self.lightSize=0
     self.lightColor=(1,1,1,1)
     self.lightIntensity=25
     # Horizon options
     self.horizonColor=(0.8,0.8,0.8)


# Deleting all objects
# Note 1: Sometimes blender is initialized with default objects: cube, light and camera
print('Deleting the following default objects:')
for item in bpy.data.objects:
    print(item.type)
    bpy.data.objects[item.name].select = True
    bpy.ops.object.delete()

sceneOp=sceneOptions()
# Reading input from json file
k=0 # Line number in the json file
OL=objectList() # Keeps track of the imported objects and their names
cmesh=mesh() # Stores the properties of the current mesh object
camPos=relativePosition() # Initialize the relative position of the camera
lightPos=relativePosition() # Initialize the relative position of the light plane
# - Each line in the json file defines a different aspect of the scene
# Line 1: General options
# Line 2: Camera position
# Line 3: Light position
# Lines >3: Options for each imported .x3d mesh object
for line in so:
    if k==0: # Read general options
       sceneOp.__dict__= json.loads(line)
       # Defining the background color
       w=bpy.data.worlds['World']
       w.horizon_color=sceneOp.horizonColor
    elif k==1:
       camPos.__dict__=json.loads(line)
    elif k==2:
       lightPos.__dict__=json.loads(line)
    else: # Read mesh options
       cmesh.__dict__= json.loads(line)
       ############################################################
       # Loading mesh objects and assigning default names to them #
       ############################################################
       file=cmesh.path2mesh
       print('Render %s' % file)
       #bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
       bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='-Y')

       # Renaming imported items
       bpy.ops.object.select_all(action='TOGGLE')
       print('\n')
       print('Imported items:\n')
       # Items are renamed depending on the order in which they are imported
       # See objectList.rename for more info.
       j=1
       for item in bpy.data.objects:
          if j>OL.N_Object:
             item=OL.rename(item)
          j=j+1
       ######################################################
       # Renaming imported mesh and assigning it a material #
       ######################################################
       meshNumber=k-2
       name="Mesh%s" %meshNumber
       print(("%s ---> Material: %s") %(name,cmesh.material))
       bpy.data.objects[name].select = True
       bpy.ops.object.shade_smooth()
       ob=bpy.data.objects[name]
       ob=assignMaterial(ob,cmesh.material,cmesh.color,cmesh.lightIntensity)
    k=k+1      

#######################
# Adding ground plane #
#######################
# Creating ground
bpy.ops.mesh.primitive_plane_add()
bpy.data.objects['Plane'].name="Ground"
ground=bpy.data.objects['Ground']
ground=assignColorMaterial(ground,(0.5,0.5,0.5))
# Parallel to the ground
bpy.data.objects['Ground'].rotation_euler=(0,math.pi/2,0)
ground=assignMaterial(ground,sceneOp.groundMaterial,sceneOp.groundColor,0)
######################
# Adding light plane #
######################
# Creating lights
bpy.ops.mesh.primitive_plane_add()
bpy.data.objects['Plane'].name="Light"
lightPlane=bpy.data.objects['Light']
lightPlane=assignLightMaterial(lightPlane,sceneOp.lightColor,sceneOp.lightIntensity)
lightPlane=lightPos.setLocation(lightPlane)
lightPlane=lightPos.setOrientation(lightPlane)
lightPlane.dimensions=(sceneOp.lightSize,sceneOp.lightSize,sceneOp.lightSize)
############################
# Setting camera position  #
############################
# Creating a new camera
bpy.ops.object.camera_add(location=(0,0,0))
cam=bpy.data.objects['Camera']
cam=camPos.setLocation(cam)
cam=camPos.setOrientation(cam)
camPos.option='none' # Set stuff manually

k=1
# The camera ONLY records objects located at a distance between clip_start and clip_end!!!
cam.data.clip_start=0
cam.data.clip_end=camPos.distance*200 # WARNING: readjust if objects are very large or far away from each-other

# Setting position and dimensions of the ground plane as a function of the camera distance and focus
if sceneOp.groundSize==0:
  dim=camPos.distance
  bpy.data.objects['Ground'].dimensions=(dim,dim,dim)
else:
  bpy.data.objects['Ground'].dimensions=(sceneOp.groundSize*2,sceneOp.groundSize*2,sceneOp.groundSize*2)
bpy.data.objects['Ground'].location=(2,camPos.focus[1],camPos.focus[2])

###################
# Rendering Scene #
###################
name=camPos.focusObject
focusOb=bpy.data.objects[name]

# Focus object in-plane coordinates
focusX=camPos.focus[1]
focusZ=camPos.focus[2]
# Distance from the beginning of the camera's trajectory along the streamlines
# to the the focus object
Dx=camTraject[0,1]-focusX
Dz=camTraject[0,2]-focusZ
R=math.sqrt(Dx*Dx+Dz*Dz)
# Relative angle to the beginning of the trayectory from the focus object point
startAngle=math.atan2(Dz,Dx)
# Maximum height that the camera reaches
H=camPos.distance/1.5
# Will calcule the camera angle for each scene
t=sceneNumber
# Chosen such that the camera loops around once per Nloop scenes
camAngVel=(2*math.pi)/Nloop
# Calculates the angle corresponding to the current scene
ang=camAngVel*t+startAngle
# Camera extra rise corresponding to this scene
camRise=H*math.sin((ang-startAngle)/2)*math.sin((ang/2-startAngle)/2)
# Camera extra radius corresponding to this scene
camR=R+R*math.sin((ang-startAngle)/2)*math.sin((ang/2-startAngle)/2)
# Sets the new location and focus
camPos.location=(camTraject[0,0]-2-camRise,camR*math.cos(ang)+focusX,camR*math.sin(ang)+focusZ)
camPos.focus=(0,focusX,focusZ)
# Assigns these to the camera
cam=camPos.setLocation(cam)
cam=camPos.setOrientation(cam)
# Let's render!
bpy.context.scene.camera = cam
bpy.context.scene.cycles.samples = 100
bpy.data.scenes['Scene'].render.filepath = path2blended
#bpy.data.scenes['Scene'].render.filepath = path2blended
bpy.ops.render.render(write_still = True)

bpy.ops.object.select_all()
bpy.ops.object.select_all()
bpy.ops.object.delete()
