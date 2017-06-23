import bpy
import math

bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'
start_frame=0
end_frame=10

### - Parameters for the position of the camera
##  - Angle
# - Fixed camera to produce an isometric-like view
camOption='iso'
# - Moving camera rotating around the domain
#camOption='rotating'
# Angular velocity of the camera in radians per time-step
angVel=(3.14159/4)/19
##  - Location
# Distance to the origin in the z=0 plane
r=2
# Height of the camera z=H
H=1.5

def makeMaterial(name, diffuse, specular, alpha):
    mat = bpy.data.materials.new(name)
    #mat2.diffuse_color = diffuse
    #mat.diffuse_shader = 'LAMBERT' 
    #mat.diffuse_intensity = 1.0 
    #mat2.specular_color = specular
    #mat.specular_shader = 'COOKTORR'
    #mat.specular_intensity = 0.5
    mat.use_transparency = True
    mat.transparency_method = 'Z_TRANSPARENCY'
    mat.alpha = alpha
    #mat.ambient = 1
    return mat
def setMaterial(ob, mat):
    me = ob.data
    if len(me.materials):
       ob.data.materials[0] = mat
    else:
        ob.data.materials.append(mat)
 


print('Deleting the following default objects:')
for item in bpy.data.objects:
    print(item.type)
    bpy.data.objects[item.name].select = True
    bpy.ops.object.delete()

# bpy.data.words["world"].horizon_color

file="/home/ubuntu/alvaro/x3dFiles/domain.x3d"
print('Render %s' % file)
bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')

for num in range(start_frame,end_frame+1):
    file="/home/ubuntu/alvaro/x3dFiles/t%s.x3d" %(num)
    print('Render %s' % file)
    bpy.ops.import_scene.x3d(filepath=file, axis_forward='X', axis_up='Z')
    bpy.ops.object.select_all(action='TOGGLE')
    
    # Renaming imported items
    print('\n')
    print('Imported items:\n')
    k=0
    N_Camera=0 # Number of imported cameras
    N_Lamp=0  # Number of imported lamps
    N_Mesh=0   # Number of imported meshes
    for item in bpy.data.objects:
        k=k+1
        print(("Object %s") % k)
        print(("Type: %s") % item.type)
        if item.type=='MESH':
           N_Mesh=N_Mesh+1
           oldDefName=item.name
           print(("Previous default name: %s") % item.name)
           newDefName="Mesh%s" % N_Mesh
           bpy.data.objects[oldDefName].name = newDefName
           print(("Current default name: %s") % item.name)
        elif item.type=='CAMERA':
           N_Camera=N_Camera+1
           oldDefName=item.name
           print(("Previous default name: %s") % item.name)
           newDefName="Camera%s" % N_Camera
           bpy.data.objects[oldDefName].name = newDefName
           print(("Current default name: %s") % item.name)        
        elif item.type=='LAMP':
           N_Lamp=N_Lamp+1
           oldDefName=item.name
           print(("Previous default name: %s") % item.name)
           newDefName="Lamp%s" % N_Lamp
           bpy.data.objects[oldDefName].name = newDefName
           print(("Current default name: %s") % item.name)
        else:
           print(("Unrecognized item type: %s") % item.name)

        print('\n')   
     


    bpy.data.objects["Mesh1"].name = 'Domain'
    bpy.data.objects['Domain'].select = True
    
    bpy.context.scene.objects.active = None
    bpy.context.scene.objects.active =bpy.data.objects["Domain"]
    Domain=bpy.data.objects['Domain']

    mat2=bpy.data.materials.new(name="MaterialGround")
    setMaterial(Domain,mat2)
    cmat=Domain.active_material

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

    #mat2.use_transparency = True
    #mat2.transparency_method = 'Z_TRANSPARENCY'
    #mat2.alpha = 0.00












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
    cam = bpy.data.objects["Camera1"]
    # cam.rotation_euler = (1.57,0,0) # No se ve nada
    # cam.rotation_euler = (0,1.57,0) # No se ve nada
    #cam.rotation_euler = (0,0,1.57) # Pone la camara en la posicion normal

    water = bpy.data.objects["Water"]

    #obj_camera.location = (5.0, 2.0, 3.0)

    print('camera location')
    print(cam.matrix_world.to_translation())
    print('water location')
    print(water.matrix_world.to_translation())
    #look_at(cam, water.matrix_world.to_translation())
    if camOption=='iso':
       angle=3.14159/4
    elif camOption=='rotating':
       angle=num*angVel

    cam.location=(-H,r*math.sin(angle),r*math.cos(angle))
    ang1=math.atan(H/r)
    cam.rotation_euler = (-ang1,angle,1.571) # De frente
 
    bpy.context.scene.camera = cam
    bpy.context.scene.cycles.samples = 120
    bpy.data.scenes['Scene'].render.filepath = '/home/ubuntu/alvaro/blendedFiles/blended_%d.png' % num
    bpy.ops.render.render(write_still = True)
    
    bpy.ops.object.select_all()
    bpy.ops.object.select_all()
    bpy.ops.object.delete()
