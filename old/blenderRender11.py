import bpy

bpy.ops.object.select_all()
bpy.ops.object.delete()
bpy.context.scene.render.engine = 'CYCLES'
start_frame=0
end_frame=0

def look_at(obj_camera, point):
    loc_camera = obj_camera.matrix_world.to_translation()

    direction = point - loc_camera
    # point the cameras '-Z' and use its 'Y' as up
    rot_quat = direction.to_track_quat('-Z', 'Y')
    print('angle')
    print(rot_quat)
    #rot_quat = direction.to_track_quat('-Y', 'Z')

    # assume we're using euler rotation
    obj_camera.rotation_euler = rot_quat.to_euler()


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
 
for num in range(start_frame,end_frame+1):
    print('Deleting the following default objects:')
    for item in bpy.data.objects:
        print(item.type)
        bpy.data.objects[item.name].select = True
        bpy.ops.object.delete()

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
     
    #bpy.data.objects["ShapeIndexedFaceSet"].data.name = 'WaterMesh'
    bpy.data.objects["Mesh1"].name = 'Water'
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
    look_at(cam, water.matrix_world.to_translation())
    
    for i in range(10)
    cam.rotation_euler = (0,0,1.57) # De frente

    #cam.location=(0.2920,0.5920,3) # La tercera es la distancia al plano frontal
    # La segunda es izquierda derecha mirando al plano frontal

    # Alzado a una distancia de 3
#    cam.rotation_euler = (0,0,1.57) # De frente
 #   cam.location=(0,0,3)    
    
    # Perfil a una distancia de 3
    #cam.rotation_euler = (-1.57,1.57,0)
    #cam.location=(0,3,0)


    # Planta a una distancia de 3
#    cam.rotation = (0,1.57,0) 
 #   cam.location=(3,0,0)



    #cam = bpy.data.objects['Camera1']
    bpy.context.scene.camera = cam
    bpy.context.scene.cycles.samples = 120
    bpy.data.scenes['Scene'].render.filepath = '/home/ubuntu/alvaro/blendedFiles/blended_%d.png' % num
    bpy.ops.render.render( write_still = True )
    
    bpy.ops.object.select_all()
    bpy.ops.object.select_all()
    bpy.ops.object.delete()
