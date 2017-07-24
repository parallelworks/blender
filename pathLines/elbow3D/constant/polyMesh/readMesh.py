import numpy as np

path2case="~/alvaro/blenderInConstruction/blenderRender4/elbow3D"
path2faces="faces"
ffaces=open(path2faces,'r')
faces=[]

startReading=0
f=0
Nfaces=0
for line in ffaces:
    if startReading==0:
      if '(' in line:
        startReading=1
        Nfaces=int(prevLine)
#        print(Nfaces)
    elif f<Nfaces:
        line=line[line.find("(")+1:line.find(")")]
        strPoints=line.split(' ')
        intPoints=[]
        for p in strPoints:
           intPoints.append(int(p))
        faces.append(intPoints)
        f=f+1
    prevLine=line



path2faces="points"
fpoints=open(path2faces,'r')
points=[]

startReading=0
f=0
Npoints=0
for line in fpoints:
    if startReading==0:
      if '(' in line:
        startReading=1
        Npoints=int(prevLine)
    elif f<Npoints:
        line=line[line.find("(")+1:line.find(")")]
        strCoord=line.split(' ')
        floatCoord=[]
        for c in strCoord:
           floatCoord.append(float(c))
        points.append(floatCoord)
        f=f+1
    prevLine=line



path2faces='boundary'
fboundary=open(path2faces,'r')
startReading=0
b=0
Nbc=0
for line in fboundary:
    print(line)
    if startReading==0:
      if '(' in line:
        startReading=1
        print('prevLine')
        print(prevLine)
        Nbc=int(prevLine)
        boundary=np.zeros((Nbc,2),dtype=np.integer)
    elif 'nFaces' in line:
        nFaces=''
        for c in line:
          if c.isdigit() or c=='.':
            nFaces=nFaces+c
    elif 'startFace' in line:
        startFace=''
        for c in line:
          if c.isdigit() or c=='.':
            startFace=startFace+c
        boundary[b,0]=int(nFaces)
        boundary[b,1]=int(startFace)
        b=b+1
    prevLine=line
print(boundary)




kp=0
for i in range(Nfaces-70319):
     j=i+70319
     pts=faces[j]
     for p in pts:
       kp=kp+1
