import bpy
import math
import sys

bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'
start_frame=0
end_frame=0

### - Parameters for the position of the camera
##  - Angle
# - Fixed camera to produce an isometric-like view
camOption='iso'
# - Moving camera rotating around the domain
camOption='rotating'
# Angular velocity of the camera in radians per time-step
#angVel=(3.14159/4)/19
angVel=(3.14159/19)

##  - Location
# Distance to the origin in the z=0 plane
r=2
# Height of the camera z=H
H=1.5


def makeMaterial(name, diffuse, specular, alpha):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT' 
    mat.diffuse_intensity = 1.0 
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat


def setMaterial(ob, mat):
    me = ob.data
    if len(me.materials):
       ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)


## This class stores and updates the position of the camera
# Note 1: The process of updating the camera position is not affected by its previous position
# Note 2: The function will only work if the following options are selected for importing the mesh:
#         axis_forward='X', axis_up='Z'. Otherwise, changes need to be made to it.          
class camPosition():
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
  # Sets the camera position to camLocation and modifies its angles
  # so that it is looking towards focusPoint
  # External Input
  # - focusPoint: The camera will be looking at this point
  # - camLocation: Position of the camera
  # - cam: bpy camera object
  def update(self,focusPoint,camLocation,cam):
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
     cam.location=(self.height,self.radius*math.sin(self.yaw),self.radius*math.cos(self.yaw))
     cam.rotation_euler=(self.pitch,self.yaw,self.roll)
     return cam

## Keeps track and renames the current number of objects according to their type and 
# the order in wich they are imported.
# Note 1: When a mesh is imported into blender it comes with default lights and camera
class objectList():
  def __init__(self):
    self.N_Object=0 # Total number of objects
    self.N_Camera=0 # Toral number of cameras
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
      self.N_Camera=self.N_Camera+1
      oldDefName=item.name
      print(("Previous default name: %s") % item.name)
      newDefName="Camera%s" % self.N_Camera
      bpy.data.objects[oldDefName].name = newDefName
      print(("Current default name: %s") % item.name)
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



# Deleteing all objects
# Note 1: Sometimes blender is initialized with default objects: cube, light and camera
print('Deleting the following default objects:')
for item in bpy.data.objects:
    print(item.type)
    bpy.data.objects[item.name].select = True
    bpy.ops.object.delete()

# Defining the background color
# Currently light grey
w=bpy.data.worlds['World']
w.horizon_color = (0.8, 0.8, 0.8)
# Should transition color from horizon to zenith but is not working
#w.use_sky_blend=True
#w.zenith_color = (1.0, 0.0, 1.0)



for num in range(start_frame,end_frame+1):
    # Loading shell: Boundary of the domain in the simulation
    file="/home/ubuntu/alvaro/x3dFiles/domain.x3d"
    print('Render %s' % file)
    bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
    # Loading isoVolume: Volume of a paraview exported property.
             # Example 1: Water volume in a water-air multiphase flow
             # Example 2: 3D Streamlines
    file="/home/ubuntu/alvaro/x3dFiles/t%s.x3d" %(num)
    print('Render %s' % file)
    bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
    # Renaming imported items
    bpy.ops.object.select_all(action='TOGGLE')
    print('\n')
    print('Imported items:\n')
    OL=objectList()
    for item in bpy.data.objects:
      item=objectList.rename(OL,item)
    
    # Items are renamed depending on the order in which they are imported
    # See objectList.rename for more info.
    bpy.data.objects["Mesh1"].name = 'shell'
    # Saving shell dimensions for iso-view option
    bpy.data.objects['shell'].select = True
    shellSize=bpy.data.objects['shell'].dimensions
    shellLocation=bpy.data.objects['shell'].matrix_world.to_translation()
    print('Size:')
    print(shellSize[0])
    print(shellSize[1])
    print(shellSize[2])
    print('Location:')
    print(shellLocation[0])
    print(shellLocation[1])
    print(shellLocation[2])
  
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active =bpy.data.objects["shell"]
    shell=bpy.data.objects['shell']

    mat2=bpy.data.materials.new(name="MaterialGround")
    setMaterial(shell,mat2)
    cmat=shell.active_material

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
    #node_Toon.inputs[0].default_value = (0.488,0.66,0.58,1)  # green RGBA
    node_Toon.inputs[1].default_value = 0.00  # green RGBA
    node_Toon.inputs[2].default_value = 0.00  # green RGBA
  #  node_Toon.inputs[3].default_value = 0.00  # green RGBA

    # Connect the guys
    links.new(node_Toon.outputs[0], node_out.inputs[0])


    bpy.data.objects["Mesh2"].name = 'Water'
    bpy.data.objects['Water'].select = True
    bpy.ops.object.shade_smooth()
    bpy.context.scene.objects.active = None
    # MAKE SOLID MATERIALS
    #blue = makeMaterial('BlueSemi', (0,0,1), (0.5,0.5,0), 0.5)
    #ob=bpy.data.objects['Water']
    #setMaterial(ob,mat)
    
    # MAKE NODE-BASED MATERIAL FOR CYCLES_RENDER
    mat = bpy.data.materials.new(name="MaterialWater")
    ob=bpy.data.objects['Water']
    setMaterial(ob,mat)
    cmat=ob.active_material
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




    # Moving camera
    #cam=bpy.ops.object.camera_add(location=(0,0,0))
    #bpy.data.objects['Camera'].select = True

    cam = bpy.data.objects["Camera1"]
    water = bpy.data.objects["Water"]
    print('camera location')
    print(cam.matrix_world.to_translation())
    print('water location')
    print(water.matrix_world.to_translation())
    
    if camOption=='iso':
       angle=3.14159/4
    elif camOption=='rotating':
       angle=num*angVel
    

    #H=num
    #water.location(-H,r*math.sin(angle),r*math.cos(angle))
    #pointLocation=water.matrix_world.to_translation()
    #camLocation=(-H,r*math.sin(angle),r*math.cos(angle))
    #camLocation=(-H,0,8-num)
    # Roll Below
    #camLocation=(r*math.sin(angle),0,r*math.cos(angle))
    # Roll over
    #camLocation=(-r*math.sin(angle),0,r*math.cos(angle))

    pointLocation=shellLocation
    #radius=2*math.sqrt(math.pow(shellLocation[0]+shellSize[0],2)+math.pow(shellLocation[1]+shellSize[1],2)+math.pow(shellLocation[2]+shellSize[2],2))
    radius=7*max(shellLocation[0]+shellSize[0],shellLocation[1]+shellSize[1],shellLocation[2]+shellSize[2])
    print('radius')
    print(radius)
    cos45=math.cos(math.pi/4)
    camLocation=(radius*cos45,radius*cos45,radius*cos45)
    camPos=camPosition()
    cam=camPosition.update(camPos,pointLocation,camLocation,cam)
    
    #cam.location=(rp.height,rp.r*math.sin(rp.polarAngle),rp.r*math.cos(rp.polarAngle))
    #cam.rotation_euler=(rp.elevationAngle,rp.polarAngle,1.571) # De frente
 
    bpy.context.scene.camera = cam
    bpy.context.scene.cycles.samples = 100
    bpy.data.scenes['Scene'].render.filepath = '/home/ubuntu/alvaro/blendedFiles/blended_%d.png' % num
    bpy.ops.render.render(write_still = True)
    
    bpy.ops.object.select_all()
    bpy.ops.object.select_all()
    bpy.ops.object.delete()
