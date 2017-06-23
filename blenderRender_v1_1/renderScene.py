import bpy
import math
import sys
import json

bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'

so=open(sys.argv[4],'r')


# Uses the user specified input
class sceneOptions():
  def __init__(self):
     self.path2scene='def'
     self.horizonColor=[0.8,0.8,0.8]
     # If orientation=none
     self.focusPoint=(0,0,0)
     self.camLocation=(0,0,0)
     # Else:
     # Camera orientation:
     # iso, front, back, top, bottom, left, right, none
     self.orientation='none'
     # Camera distance
     # Zero value will trigger the default option
     self.distance=0
     # Camera will look towards the focus object (imported volume)
     self.focus='def'
  def setCamera(self,focusOb):
     if self.orientation!='none':
        shellSize=focusOb.dimensions
        shellLocation=focusOb.location
        p1=-(shellLocation[0]+shellSize[0])/2
        p2=(shellLocation[1]+shellSize[1])/2
        p3=(shellLocation[2]+shellSize[2])/2
        self.focusPoint=(p1,p2,p3)
        if self.distance==0:
           self.distance=3*max(shellLocation[0]+shellSize[0],shellLocation[1]+shellSize[1],shellLocation[2]+shellSize[2])
        self.camLocation=(p1,p2,self.distance)
        if self.orientation=='iso':
           cos45=math.cos(math.pi/4)
           self.camLocation=(-self.distance*cos45,self.distance*cos45,self.distance*cos45)
        elif self.orientation=='front':
           self.camLocation=(p1,p2,self.distance)
        elif self.orientation=='back':
           self.camLocation=(p1,p2,-self.distance)
        elif self.orientation=='right':
           self.camLocation=(p1,self.distance,p3)
        elif self.orientation=='left':
           self.camLocation=(p1,-self.distance,p3)
        elif self.orientation=='up':
           self.camLocation=(-self.distance,p2,p3)
        elif self.orientation=='down':
           self.camLocation=(self.distance,p2,p3)
     else: # User defined focusPoint and camLocation --> calc distance
        r=0
        for i in range(3):
           aux=self.focusPoint[i]-self.camLocation[i]
           r=r+aux*aux
        self.distance=math.sqrt(r)
        
def assignColorMaterial(diffuse, specular, alpha, ob):
    mat = bpy.data.materials.new('colorMat')
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = 1.0
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
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
    links.new(node_glass.outputs[0], node_out.inputs[0])
    return waterObject


def setMaterial(ob, mat):
    me = ob.data
    if len(me.materials):
       ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
    return ob 


## This class stores and updates the position of the camera
# Note 1: The process of updating the camera orientation is not affected by its previous orientation
# Note 2: The function will only work if the following options are selected for importing the mesh:
#         axis_forward='X', axis_up='Z'. Otherwise, changes need to be made to it.          
class camOrientation():
  def __init__(self):
     # Distance in the (y,z) plane from the camLocation to focusPoint
     self.radius=0
     # Distance to the (y,z) plane along the x axis
     self.height=0
     # The angles are defined using the aircraft convention where the
     # (y,z) plane is the ground and x is the vertical axis
     self.yaw=0
     self.pitch=0
     self.roll=math.pi/2
  # Orientates the camera so that that it looks from the camLocation to focusPoint
  # External Input
  # - focusPoint: The camera will be looking at this point
  # - camLocation: Position of the camera
  def update(self,focusPoint,camLocation):
     r=0
     for i in range(2):
         aux=focusPoint[i+1]-camLocation[i+1]
         r=r+aux*aux
     self.radius=math.sqrt(r)
     x=camLocation[2]-focusPoint[2]
     y=camLocation[1]-focusPoint[1]
     z=camLocation[0]-focusPoint[0]
     self.yaw=math.atan2(y,x)
     self.height=z
     self.pitch=math.atan2(self.height,self.radius)

## Keeps track and renames the current number of objects according to their type and 
# the order in wich they are imported.
# Note 1: When a mesh is imported into blender it comes with default lights and camera
# Note 2: In the current version of the code imported cameras are deleted
class objectList():
  def __init__(self):
    self.N_Object=0 # Total number of objects
    self.N_Camera=0 # Total number of cameras (Should remain =0 in current version)
    self.N_Lamp=0  # Total number of lamps
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
      self.N_Lamp=self.N_Lamp+1
      oldDefName=item.name
      print(("Previous default name: %s") % item.name)
      newDefName="Lamp%s" % self.N_Lamp
      bpy.data.objects[oldDefName].name = newDefName
      print(("Current default name: %s") % item.name)
    else:
      print(("WARNING - Unrecognized item type: %s") % item.name)
      print('\n')
    return item

# Defines the path to the .x3d files and the assigned material
class mesh():
  def __init__(self):
     self.path2mesh='def'
     self.material='def'
     self.diffuse=(0,0,0)
     self.specular=(0,0,0)
     self.alpha=0


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
OL=objectList() # Keeps track of the current number of objects and their names
cmesh=mesh() # Stores the properties of the current mesh object
# The first line in the json file defines the scene. Each following lines defines an
# imported .x3d mesh.
for line in so:
    if k==0: # Read general options
       sceneOp.__dict__= json.loads(line)
       path2blended=sceneOp.path2blended
       print(sceneOp.horizonColor)
       # Defining the background color
       w=bpy.data.worlds['World']
       w.horizon_color = sceneOp.horizonColor
       # Should transition color from horizon to zenith but is not working
       #w.use_sky_blend=True
       #w.zenith_color = (1.0, 0.0, 1.0)
    else: # Read mesh options
       cmesh.__dict__= json.loads(line)
       ############################################################
       # Loading mesh objects and assigning default names to them #
       ############################################################
       file=cmesh.path2mesh
       print('Render %s' % file)
       bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
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
       name="Mesh%s" %k
       print(("%s ---> Material: %s") %(name,cmesh.material))
       bpy.data.objects[name].select = True
       bpy.ops.object.shade_smooth()
       ob=bpy.data.objects[name]
       if cmesh.material=="glass":    
          ob=assignGlassMaterial(ob)
       elif cmesh.material=="water":
          ob=assignWaterMaterial(ob)
       elif cmesh.material=="color":
          ob=assignColorMaterial(cmesh.diffuse,cmesh.specular,cmesh,alpha, ob)
    k=k+1      
############################
# Setting camera position  #
############################
# The camera position is set in two setps:
# Step 1: Use camera options "sceneOptions()" to decide the location of the focus point and the camera
# Step 2: Use "camOrientation()" to point the camera towards the focus point
# Note 1: The initial position of the camera is irrelevant 
# Seting desired camera and focus positions
focusOb=bpy.data.objects[sceneOp.focus]
sceneOp.setCamera(focusOb) # uses input to calculate both positions
# Camera will look at focusPoint from camLocation
focusPoint=sceneOp.focusPoint
camLocation=sceneOp.camLocation
# Seting desired camera orientation
camOr=camOrientation()
camOr.update(focusPoint,camLocation)
camRotation_euler=(camOr.pitch,camOr.yaw,camOr.roll)
# Creating a new camera
bpy.ops.object.camera_add(location=(0,0,0))
bpy.data.objects["Camera"].rotation_euler=camRotation_euler
bpy.data.objects["Camera"].location =camLocation
cam=bpy.data.objects['Camera']
# The camera ONLY records objects located at a distance between clip_start and clip_end!!!
cam.data.clip_start=0
cam.data.clip_end=sceneOp.distance*2 # WARNING: readjust if objects are very large or far away from each-other

    
###################
# Rendering Scene #
###################
bpy.context.scene.camera = cam
bpy.context.scene.cycles.samples = 100
bpy.data.scenes['Scene'].render.filepath = path2blended
bpy.ops.render.render(write_still = True)

bpy.ops.object.select_all()
bpy.ops.object.select_all()
bpy.ops.object.delete()
