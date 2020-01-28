import sys
import argparse
from os import listdir
from os.path import isfile, join
import matplotlib.pyplot as plt
from GLContext import *

parser = argparse.ArgumentParser()
parser.add_argument('--images', default='./images', type=str, help='path to image files')

class Data():
    def __init__(self, images):
        self.images = images
        self.files = [f for f in listdir(self.images) if isfile(join(self.images, f))]
        self.files.sort()
        self.currentIndex = 0
        self.lastFrameReached = len(self.files) <= self.currentIndex

        self.width, self.height = 0, 0
        if not self.lastFrameReached:
            image = self.openFile(join(self.images, self.files[self.currentIndex]))
            self.height = image.shape[0]
            self.width =image.shape[1]
        else:
            sys.exit(0)

    def openFile(self, file):
        image = np.flip(plt.imread(file), 0).astype(np.float32) / 255.0
        return image[..., :3]

    def nextFrame(self):
        if not self.lastFrameReached:
            image = self.openFile(join(self.images, self.files[self.currentIndex]))
            self.currentIndex += 1
            self.lastFrameReached = len(self.files) <= self.currentIndex
        return image

class Program():
    def __init__(self, argv):
        args = parser.parse_args(argv[1:])
        self.data = Data(args.images)
        print(self.data.width, self.data.height)

        self.context = GLContext(int(self.data.width), int(self.data.height))
        self.canvas = Mesh(join('./meshes', 'quad_uv.obj'))

        # framebuffer
        self.fb_default = FrameBuffer(width=self.data.width, height=self.data.height, default=True)
        self.fb_gaussian = FrameBuffer(width=self.data.width, height=self.data.height)
        self.fb_gaussian_2 = FrameBuffer(width=self.data.width, height=self.data.height)
        self.fb_scene = FrameBuffer(width=self.data.width, height=self.data.height)
        self.fb_scene_previous = FrameBuffer(width=self.data.width, height=self.data.height)
        self.fb_gradient_t = FrameBuffer(width=self.data.width, height=self.data.height)
        self.fb_gradient_s = FrameBuffer(width=self.data.width, height=self.data.height, attachments=2)
        self.fb_optical_flow = FrameBuffer(width=self.data.width, height=self.data.height, attachments=2)
        self.fb_optical_flow_smooth = FrameBuffer(width=self.data.width, height=self.data.height, attachments=2)

        # shaders
        self.shader_gaussian = self.context.createShader('shaders/gaussian.vert', 'shaders/gaussian.frag')
        glUseProgram(self.shader_gaussian)
        glUniform1i(glGetUniformLocation(self.shader_gaussian, "scene"), 0)
        glUniform1i(glGetUniformLocation(self.shader_gaussian, "width"), self.data.width)
        glUniform1i(glGetUniformLocation(self.shader_gaussian, "height"), self.data.height)
        glUseProgram(0)

        self.shader_passthrough = self.context.createShader('shaders/passthrough.vert', 'shaders/passthrough.frag')
        glUseProgram(self.shader_passthrough)
        glUniform1i(glGetUniformLocation(self.shader_passthrough, 'scene'), 0)
        glUseProgram(0)

        self.shader_gradient_t = self.context.createShader('shaders/passthrough.vert', 'shaders/gradient_t.frag')
        glUseProgram(self.shader_gradient_t)
        glUniform1i(glGetUniformLocation(self.shader_gradient_t, 'scene'), 0)
        glUniform1i(glGetUniformLocation(self.shader_gradient_t, 'scene_previous'), 1)
        glUseProgram(0)

        self.shader_gradient_s = self.context.createShader('shaders/passthrough.vert', 'shaders/gradient_s.frag')
        glUseProgram(self.shader_gradient_s)
        glUniform1i(glGetUniformLocation(self.shader_gradient_s, 'scene'), 0)
        glUniform1i(glGetUniformLocation(self.shader_gradient_s, 'width'), self.data.width)
        glUniform1i(glGetUniformLocation(self.shader_gradient_s, 'height'), self.data.height)
        glUseProgram(0)

        self.shader_optical_flow = self.context.createShader('shaders/optical_flow.vert', 'shaders/optical_flow.frag')
        glUseProgram(self.shader_optical_flow)
        glUniform1i(glGetUniformLocation(self.shader_optical_flow, "gradient_t"), 0)
        glUniform1i(glGetUniformLocation(self.shader_optical_flow, "gradient_s_x"), 1)
        glUniform1i(glGetUniformLocation(self.shader_optical_flow, "gradient_s_y"), 2)
        glUniform1i(glGetUniformLocation(self.shader_optical_flow, "width"), self.data.width)
        glUniform1i(glGetUniformLocation(self.shader_optical_flow, "height"), self.data.height)
        glUseProgram(0)

        self.shader_passthrough_of = self.context.createShader('shaders/passthrough.vert', 'shaders/passthrough_of.frag')
        glUseProgram(self.shader_passthrough_of)
        glUniform1i(glGetUniformLocation(self.shader_passthrough_of, "color_in"), 0)
        glUniform1i(glGetUniformLocation(self.shader_passthrough_of, "data_in"), 1)
        glUseProgram(0)

        self.currentTexture = self.nextTexture()

    def nextTexture(self):
        image = self.data.nextFrame()
        shape = image.shape
        texture = Texture(height=shape[0], width=shape[1], data=image)
        return texture

    def render(self):
        if not self.data.lastFrameReached:
            image = self.data.nextFrame()
            self.currentTexture.setData(image)
            glDisable(GL_DEPTH_TEST)

            # previous image
            self.translateRender(self.shader_passthrough)
            self.fb_scene_previous.init([self.fb_gaussian.getTexture(0)])
            self.canvas.draw(self.shader_passthrough)

            # current image
            self.fb_scene.init([self.currentTexture.texture])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_gaussian)
            self.fb_gaussian.init([self.fb_scene.getTexture(0)])
            self.canvas.draw(self.shader_gaussian)
            for i in range(0):
                # gaussian blur
                self.fb_gaussian_2.init([self.fb_gaussian.getTexture(0)])
                self.canvas.draw(self.shader_gaussian)
                # current image
                self.fb_gaussian.init([self.fb_gaussian_2.getTexture(0)])
                self.canvas.draw(self.shader_gaussian)

            # temporal gradient
            self.translateRender(self.shader_gradient_t)
            self.fb_gradient_t.init([self.fb_gaussian.getTexture(0), self.fb_scene_previous.getTexture(0)])
            self.canvas.draw(self.shader_gradient_t)

            # spatial gradients
            self.translateRender(self.shader_gradient_s)
            self.fb_gradient_s.init([self.fb_gaussian.getTexture(0)])
            self.canvas.draw(self.shader_gradient_s)

            # render optical flow
            self.translateRender(self.shader_optical_flow)
            self.fb_optical_flow.init([self.fb_gradient_t.getTexture(0), self.fb_gradient_s.getTexture(0), self.fb_gradient_s.getTexture(1)])
            self.canvas.draw(self.shader_optical_flow)

            self.translateRender(self.shader_passthrough_of)
            self.fb_optical_flow_smooth.init([self.fb_optical_flow.getTexture(0), self.fb_optical_flow.getTexture(1)], mipmaps=True)
            self.canvas.draw(self.shader_passthrough_of)

            # final display
            self.fb_default.init()
            self.translateRender(self.shader_passthrough)
            self.fb_default.bindTextures([self.currentTexture.texture])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_passthrough, vec3(0.8, 0.8, 0.0), 0.19)
            self.fb_default.bindTextures([self.fb_gradient_s.getTexture(0)])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_passthrough, vec3(0.8, 0.4, 0.0), 0.19)
            self.fb_default.bindTextures([self.fb_gradient_s.getTexture(1)])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_passthrough, vec3(0.8, 0.0, 0.0), 0.19)
            self.fb_default.bindTextures([self.fb_gradient_t.getTexture(0)])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_passthrough, vec3(0.8, -0.4, 0.0), 0.19)
            self.fb_default.bindTextures([self.fb_optical_flow_smooth.getTexture(0)])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_passthrough, vec3(0.8, -0.8, 0.0), 0.19)
            self.fb_default.bindTextures([self.fb_optical_flow_smooth.getTexture(1)])
            self.canvas.draw(self.shader_passthrough)

            self.translateRender(self.shader_passthrough)
        else:
            sys.exit(0)

    def translateRender(self, shader, translation=vec3(0, 0, 0), scale=1):
        glUseProgram(shader)
        modelMatrix = translationMatrix(translation) @ scaleMatrix(scale)
        glUniformMatrix4fv(glGetUniformLocation(shader, "modelMatrix"), 1, GL_TRUE, modelMatrix)
        glUseProgram(0)

    def loop(self):
        self.render()
        glfw.swap_buffers(self.context.window)
        while not glfw.window_should_close(self.context.window):
            if glfw.get_key(self.context.window, glfw.KEY_RIGHT):
                print('next Frame')
                self.render()
                glfw.swap_buffers(self.context.window)
            glfw.poll_events()
        glfw.terminate()

if __name__ == '__main__':
    program = Program(sys.argv)
    program.loop()