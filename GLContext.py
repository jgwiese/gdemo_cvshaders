import glfw
import math
import numpy as np
from OpenGL.GL import *
import OpenGL.GL.shaders

def vec3(x, y, z):
    return np.array([x, y, z], dtype=np.float32)

def perspective(fovy, aspect, zNear, zFar):
    tanHalfFovy = math.tan(fovy / 2)
    matrix = np.array([
        [1 / (aspect * tanHalfFovy), 0, 0, 0],
        [0, (1 / tanHalfFovy), 0, 0],
        [0, 0, -((zFar + zNear) / (zFar - zNear)), -1],
        [0, 0, -((2 * zFar * zNear) / (zFar - zNear)), 0]])
    return matrix.transpose()

def normalize(v):
    absolute = np.linalg.norm(v)
    if absolute != 0:
        return v / absolute
    else:
        return v

def lookAt(eye, center, up):
    f = normalize(center - eye)
    u = normalize(up)
    s = normalize(np.cross(f, u))

    matrix = np.array([
        [s[0], u[0], -f[0], 0],
        [s[1], u[1], -f[1], 0],
        [s[2], u[2], -f[2], 0],
        [-np.dot(s, eye), -np.dot(u, eye), np.dot(f, eye), 1]])
    return matrix.transpose()

def scaleMatrix(value):
    matrix = np.array([[value, 0, 0, 0], [0, value, 0, 0], [0, 0, value, 0], [0, 0, 0, 1]], dtype=np.float32)
    return matrix

def translationMatrix(v):
    matrix = np.array([[1, 0, 0, v[0]], [0, 1, 0, v[1]], [0, 0, 1, v[2]], [0, 0, 0, 1]])
    return matrix

def rotationMatrixX(angle):
    matrix = np.array(
        [[1, 0, 0, 0], [0, math.cos(angle), -math.sin(angle), 0], [0, math.sin(angle), math.cos(angle), 0],
         [0, 0, 0, 1]])
    return matrix

def rotationMatrixY(angle):
    matrix = np.array(
        [[math.cos(angle), 0, math.sin(angle), 0], [0, 1, 0, 0], [-math.sin(angle), 0, math.cos(angle), 0],
         [0, 0, 0, 1]])
    return matrix

def rotationMatrixZ(angle):
    matrix = np.array(
        [[math.cos(angle), -math.sin(angle), 0, 0], [math.sin(angle), math.cos(angle), 0, 0], [0, 0, 1, 0],
         [0, 0, 0, 1]])
    return matrix

identityMat = np.eye(4)


class GLContext:
    window = None

    def __init__(self, width=512, height=512):
        if not glfw.init():
            return

        glfw.window_hint(glfw.SAMPLES, 4);
        glfw.window_hint(glfw.RESIZABLE, GL_FALSE);
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3);
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3);
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE);

        self.window = glfw.create_window(width, height, "-", None, None)

        if not self.window:
            glfw.terminate()
            return

        glfw.make_context_current(self.window)

        # OpenGL settings
        glEnable(GL_CULL_FACE)
        glDepthFunc(GL_LESS)

    def createShader(self, vsFilename, fsFilename):
        with open(vsFilename, 'r') as vsFile:
            vsString = vsFile.read()

        vs = OpenGL.GL.shaders.compileShader(vsString, GL_VERTEX_SHADER)

        with open(fsFilename, 'r') as fsFile:
            fsString = fsFile.read()
        fs = OpenGL.GL.shaders.compileShader(fsString, GL_FRAGMENT_SHADER)

        sp = OpenGL.GL.shaders.compileProgram(vs, fs)
        return sp

class Texture():
    def __init__(self, width, height, data=None):
        self.width = width
        self.height = height
        self.texture = glGenTextures(1)
        self.setData(data)

    def setData(self, data):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, self.width, self.height, 0, GL_RGB, GL_FLOAT, data)
        glGenerateMipmap(GL_TEXTURE_2D)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

    def getBuffer(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        buf = glGetTexImage(GL_TEXTURE_2D, 0, GL_RGB, GL_FLOAT)
        glBindTexture(GL_TEXTURE_2D, 0)
        buf = np.frombuffer(buf, np.float32).reshape((self.width, self.height, 4))
        buf[:,:,3] = 1
        return buf

    def deleteTexture(self):
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glDeleteTextures(1, self.texture)
        glBindTexture(GL_TEXTURE_2D, 0)

class DepthTexture():
    def __init__(self, width, height, data=None):
        self.texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32, width, height, 0, GL_DEPTH_COMPONENT,
                     GL_UNSIGNED_BYTE, data)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0)

class FrameBuffer():
    def __init__(self, width, height, attachments=1, clear_color=np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float32), default=False):
        self.clear_color = clear_color

        self.fb = 0
        if not default:
            self.fb = glGenFramebuffers(1)

            glBindFramebuffer(GL_FRAMEBUFFER, self.fb)
            self.color_buffer_textures = []
            self.color_buffers = []
            for i in range(attachments):
                texture = Texture(width, height)
                self.color_buffer_textures.append(texture)
                self.color_buffers.append(GL_COLOR_ATTACHMENT0 + i)
                glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0 + i, GL_TEXTURE_2D, self.color_buffer_textures[i].texture, 0)
            glDrawBuffers(len(self.color_buffers), self.color_buffers)

            self.depth_buffer = DepthTexture(width, height)
            glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_buffer.texture, 0)
            glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def getTexture(self, i):
        return self.color_buffer_textures[i].texture

    def bindTextures(self, color_buffer, mipmaps=False):
        for i in range(len(color_buffer)):
            assert (i < 16)
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(GL_TEXTURE_2D, color_buffer[i])
            if mipmaps:
                glGenerateMipmap(GL_TEXTURE_2D)

    def unbindTextures(self, color_buffer):
        for i in range(len(color_buffer)):
            assert (i < 16)
            glActiveTexture(GL_TEXTURE0 + i)
            glBindTexture(GL_TEXTURE_2D, 0)

    def init(self, color_buffer=[], clear=True, mipmaps=False):
        glBindFramebuffer(GL_FRAMEBUFFER, self.fb)
        if clear:
            glClearColor(self.clear_color[0], self.clear_color[1], self.clear_color[2], self.clear_color[3])
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.bindTextures(color_buffer, mipmaps)

class Mesh:
    def __init__(self, meshPath):

        # Parsing custom .mesh fileformat
        self.vertices = []
        self.normals = []
        self.uvs = []
        self.vertexIndices = []
        self.normalIndices = []
        self.uvIndices = []
        self.vboData = []
        self.indices = []
        with open(meshPath, 'r') as meshFile:
            for line in meshFile:
                sLine = line.split()
                if not len(sLine):
                    continue
                if sLine[0] == "v":
                    #self.vertexData = self.vertexData + sLine[1:]
                    self.vertices = self.vertices + sLine[1:]
                if sLine[0] == "vt":
                    self.uvs = self.uvs + sLine[1:]
                if sLine[0] == "vn":
                    self.normals = self.normals + sLine[1:]
                if sLine[0] == "f":
                    for element in sLine[1:]:
                        indices = element.split('/')
                        self.vertexIndices.append(indices[0])
                        self.uvIndices.append(indices[1])
                        self.normalIndices.append(indices[2])

        self.vertices = np.array(self.vertices, dtype=np.float32)
        self.normals = np.array(self.normals, dtype=np.float32)
        self.uvs = np.array(self.uvs, dtype=np.float32)
        self.vertexIndices = np.array(self.vertexIndices, dtype=np.uint32) - 1
        self.normalIndices = np.array(self.normalIndices, dtype=np.uint32) - 1
        self.uvIndices = np.array(self.uvIndices, dtype=np.uint32) - 1
        tmp = -np.ones((int(len(self.vertices)/3), int(len(self.uvs)/2), int(len(self.normals)/3)))

        for v, t, n in zip(self.vertexIndices, self.uvIndices, self.normalIndices):
            if tmp[v, t, n] == -1:
                tmp[v, t, n] = int(len(self.vboData) / 8)
                self.vboData.append(self.vertices[v * 3])
                self.vboData.append(self.vertices[v * 3 + 1])
                self.vboData.append(self.vertices[v * 3 + 2])
                self.vboData.append(self.uvs[t * 2])
                self.vboData.append(self.uvs[t * 2 + 1])
                self.vboData.append(self.normals[n * 3])
                self.vboData.append(self.normals[n * 3 + 1])
                self.vboData.append(self.normals[n * 3 + 2])
            index = tmp[v, t, n]
            self.indices.append(index)
        self.vboData = np.array(self.vboData, dtype=np.float32)
        self.indices = np.array(self.indices, dtype=np.uint32)


        # OpenGL related calls
        self.vao = glGenVertexArrays(1)
        self.vbo = glGenBuffers(1)
        self.ibo = glGenBuffers(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, self.vboData, GL_STATIC_DRAW)

        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, self.indices, GL_STATIC_DRAW)

        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, self.vboData[0].nbytes*8, None)
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, self.vboData[0].nbytes * 8, ctypes.c_void_p(self.vboData[0].nbytes * 3))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(2, 3, GL_FLOAT, GL_FALSE, self.vboData[0].nbytes*8, ctypes.c_void_p(self.vboData[0].nbytes*5))
        glEnableVertexAttribArray(2)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def printData(self):
        for v in self.vboData:
            print(v)
        print(self.indices)

    def draw(self, shader, style=GL_TRIANGLES):
        glUseProgram(shader)
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, self.ibo)
        glDrawElements(style, len(self.indices), GL_UNSIGNED_INT, None)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        glUseProgram(0)