import sys
import numpy as np

progname = sys.argv[0]
args = sys.argv[1:]

def lade_obj(filename):
    vertices = []
    faces = []
    indices = []
    normals = []
    with open(filename, 'r') as file:
        for zeile in file:
            if zeile.startswith('v '):
                teile = zeile.strip().split()
                vertex = list(map(float, teile[1:4]))
                vertices.append(vertex)
            elif zeile.startswith('vn '):
                teile = zeile.strip().split()
                normal = list(map(float, teile[1:4]))
                normals.append(normal)
            elif zeile.startswith('f '):
                teile = zeile.strip().split()[1:]
                face = []
                for part in teile:
                    vals = part.split('/')
                    v_index = int(vals[0]) - 1
                    face.append(v_index)
                faces.append(face)
                
    indices = np.array(faces).flatten()
    vertices = np.array(vertices, dtype=np.float32)
    indices = np.array(indices, dtype=np.uint32)

    if not normals:
        normals = compute_normals(vertices, faces)
    else:
        normals = np.array(normals, dtype=np.float32)

    return vertices, indices, faces, normals

def compute_normals(vertices, faces):
    normals = np.zeros_like(vertices, dtype=np.float32)

    for face in faces:
        i0, i1, i2 = face
        v0 = vertices[i0]
        v1 = vertices[i1]
        v2 = vertices[i2]

        # Kantenvektoren
        e1 = v1 - v0
        e2 = v2 - v0

        # Flächen-Normale
        face_normal = np.cross(e1, e2)

        # Summe der Normale auf die beteiligten Vertices
        normals[i0] += face_normal
        normals[i1] += face_normal
        normals[i2] += face_normal

    # Alle Normale normieren
    norms = np.linalg.norm(normals, axis=1)
    norms[norms == 0] = 1.0  # vermeide Division durch 0
    normals /= norms[:, np.newaxis]

    return normals

def projectOnSphere(x, y, r, width, height):
    x, y = x - width/2.0, height/2.0 - y
    a = min(r*r, x**2 + y**2)
    z = np.sqrt(r*r - a)
    l = np.sqrt(x**2 + y**2 + z**2)
    return x/l, y/l, z/l


vertices,indices,faces, normals = lade_obj("obj_files/cow.obj")
print("hallo")
