"""
/*******************************************************************************
 *
 *            #, #,         CCCCCC  VV    VV MM      MM RRRRRRR
 *           %  %(  #%%#   CC    CC VV    VV MMM    MMM RR    RR
 *           %    %## #    CC        V    V  MM M  M MM RR    RR
 *            ,%      %    CC        VV  VV  MM  MM  MM RRRRRR
 *            (%      %,   CC    CC   VVVV   MM      MM RR   RR
 *              #%    %*    CCCCCC     VV    MM      MM RR    RR
 *             .%    %/
 *                (%.      Computer Vision & Mixed Reality Group
 *
 ******************************************************************************/
/**          @copyright:   Hochschule RheinMain,
 *                         University of Applied Sciences
 *              @author:   Prof. Dr. Ulrich Schwanecke
 *             @version:   0.91
 *                @date:   07.06.2022
 ******************************************************************************/
/**         oglTemplate.py
 *
 *          Simple Python OpenGL program that uses PyOpenGL + GLFW to get an
 *          OpenGL 3.2 core profile context and animate a colored triangle.
 ****
"""

import sys
import glfw
import numpy as np

from OpenGL.GL import *
from OpenGL.arrays.vbo import VBO
from OpenGL.GL.shaders import *

from mat4 import *

from utils import lade_obj, projectOnSphere

EXIT_FAILURE = -1

progname = sys.argv[0]
args = sys.argv[1:]

class Scene:
    """
    OpenGL scene class: .obj mit Wireframe / Gouraud / Phong.
    """

    def __init__(self, width, height, scenetitle="Cooles Modell"):
        self.scenetitle = scenetitle
        self.width = width
        self.height = height
        self.angle = 0
        self.angle_increment = 1
        self.animate = False
        self.shading_mode = 0  # 0=Wireframe, 1=Gouraud, 2=Phong
        self.projection_mode = 0  # 0 = Perspective, 1 = Orthographic
        self.rotation_matrix = np.identity(4)
        self.mouse_pressed = False
        self.p1 = None
        self.arcball_radius = min(self.width, self.height) / 2.0
        self.zoom_factor = 1.0
        self.last_y = None
        self.zoom_pressed = False
        self.pan_offset = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.pan_pressed = False
        self.last_pan_x = None
        self.last_pan_y = None
        self.keyboard_rotation_angle = 5.0  # Grad pro Tastendruck







    def init_GL(self):
        # setup buffer (vertices, normals)
        self.gen_buffers()

        # <<< VAO binden >>>
        glBindVertexArray(self.vertex_array)

        self.load_shaders()

        # <<< wieder entbinden >>>
        glBindVertexArray(0)

    def load_shaders(self):
        # Wireframe
        vs = compileShader(open("shader.vert").read(), GL_VERTEX_SHADER)
        fs = compileShader(open("shader.frag").read(), GL_FRAGMENT_SHADER)
        self.shader_wireframe = compileProgram(vs, fs)

        # Gouraud
        vs = compileShader(open("gouraud.vert").read(), GL_VERTEX_SHADER)
        fs = compileShader(open("gouraud.frag").read(), GL_FRAGMENT_SHADER)
        self.shader_gouraud = compileProgram(vs, fs)

        # Phong
        vs = compileShader(open("phong.vert").read(), GL_VERTEX_SHADER)
        fs = compileShader(open("phong.frag").read(), GL_FRAGMENT_SHADER)
        self.shader_phong = compileProgram(vs, fs)

    def gen_buffers(self):
        vertices, indices, faces, normals = lade_obj(args[0])

        # zentrieren & normalisieren
        center = vertices.mean(axis=0)
        vertices -= center
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)
        extent = max_coords - min_coords
        max_extent = np.max(extent)
        vertices /= max_extent
        vertices *= 1.5  # optional größer

        # VAO
        self.vertex_array = glGenVertexArrays(1)
        glBindVertexArray(self.vertex_array)

        # Vertices -> Attrib 0
        pos_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, pos_buffer)
        glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)
        glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)

        # Normals -> Attrib 1 (immer!)
        norm_buffer = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, norm_buffer)
        glBufferData(GL_ARRAY_BUFFER, normals.nbytes, normals, GL_STATIC_DRAW)
        glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)

        # Indices
        self.indices = indices
        ind_buffer = glGenBuffers(1)
        glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ind_buffer)
        glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_STATIC_DRAW)

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def set_size(self, width, height):
        self.width = width
        self.height = height

    def draw(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if self.animate:
            self.angle += self.angle_increment

        # Kamera & Transformationen
        aspect = self.width / self.height

        if self.projection_mode == 0:
            # Perspektivisch
            projection = perspective(45.0, aspect, 1.0, 10.0)
        else:
            # Orthografisch
            ortho_scale = 1.5  # kannst du nach Geschmack anpassen
            if aspect >= 1.0:
                projection = ortho(-ortho_scale*aspect, ortho_scale*aspect, -ortho_scale, ortho_scale, 1.0, 10.0)
            else:
                projection = ortho(-ortho_scale, ortho_scale, -ortho_scale/aspect, ortho_scale/aspect, 1.0, 10.0)


        view = look_at(0, 0, 3, 0, 0, 0, 0, 1, 0)
        if self.animate:
            # Animation aktiv → dreht weiter um Y-Achse
            model = rotate_y(self.angle) @ self.rotation_matrix
        else:
            # nur Arcball-Rotation
            model = self.rotation_matrix

        model = translate(self.pan_offset[0], self.pan_offset[1], 0.0) @ model

        model = scale(self.zoom_factor, self.zoom_factor, self.zoom_factor) @ model

        mvp_matrix = projection @ view @ model
        mv_matrix = view @ model
        normal_matrix = np.linalg.inv(mv_matrix[:3, :3]).T

        # Shader wählen
        if self.shading_mode == 0:
            shader = self.shader_wireframe
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
        else:
            shader = self.shader_gouraud if self.shading_mode == 1 else self.shader_phong
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        glUseProgram(shader)

        # Uniforms setzen
        loc_mvp = glGetUniformLocation(shader, "modelview_projection_matrix")
        glUniformMatrix4fv(loc_mvp, 1, GL_TRUE, mvp_matrix)

        loc_mv = glGetUniformLocation(shader, "modelview_matrix")
        glUniformMatrix4fv(loc_mv, 1, GL_TRUE, mv_matrix)

        loc_nm = glGetUniformLocation(shader, "normal_matrix")
        glUniformMatrix3fv(loc_nm, 1, GL_TRUE, normal_matrix)

        loc_shiny = glGetUniformLocation(shader, "shininess")
        glUniform1f(loc_shiny, 64.0)  # oder 64.0 für noch engeren Glanzpunkt


        # Zeichnen
        glBindVertexArray(self.vertex_array)
        glDrawElements(GL_TRIANGLES, len(self.indices), GL_UNSIGNED_INT, None)

        # Aufräumen
        glBindVertexArray(0)
        glUseProgram(0)
        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)



class RenderWindow:
    """
        GLFW Rendering window class
    """

    def __init__(self, scene):
        # initialize GLFW
        if not glfw.init():
            sys.exit(EXIT_FAILURE)

        # request window with old OpenGL 3.2
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, glfw.TRUE)
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 2)

        # make a window
        self.width, self.height = scene.width, scene.height
        self.aspect = self.width / self.height
        self.window = glfw.create_window(self.width, self.height, scene.scenetitle, None, None)
        if not self.window:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        # Make the window's context current
        glfw.make_context_current(self.window)

        # initialize GL
        self.init_GL()

        # set window callbacks
        glfw.set_mouse_button_callback(self.window, self.on_mouse_button)
        glfw.set_key_callback(self.window, self.on_keyboard)
        glfw.set_window_size_callback(self.window, self.on_size)
        glfw.set_cursor_pos_callback(self.window, self.on_mouse_move)


        # create scene
        self.scene = scene  
        if not self.scene:
            glfw.terminate()
            sys.exit(EXIT_FAILURE)

        self.scene.init_GL()

        # exit flag
        self.exitNow = False

    def on_mouse_move(self, win, xpos, ypos):
        if self.scene.mouse_pressed:
            # Arcball …
            p2 = np.array(
                projectOnSphere(xpos, ypos, self.scene.arcball_radius, self.scene.width, self.scene.height)
            )
            axis = np.cross(self.scene.p1, p2)
            if np.linalg.norm(axis) < 1e-6:
                return
            axis /= np.linalg.norm(axis)
            angle = np.arccos(np.clip(np.dot(self.scene.p1, p2), -1.0, 1.0))
            angle_deg = np.degrees(angle)
            rot = rotate(angle_deg, axis)
            self.scene.rotation_matrix = rot @ self.scene.rotation_matrix
            self.scene.p1 = p2

        if self.scene.zoom_pressed:
            _, y = glfw.get_cursor_pos(win)
            dy = y - self.scene.last_y
            self.scene.zoom_factor *= 1.0 + dy * 0.002  # <<< HIER: kleiner Faktor für weicher
            self.scene.zoom_factor = max(0.1, min(self.scene.zoom_factor, 10.0))
            self.scene.last_y = y

        if self.scene.pan_pressed:
            x, y = glfw.get_cursor_pos(win)
            dx = x - self.scene.last_pan_x
            dy = y - self.scene.last_pan_y

            # Skaliere für feinfühliges Panning
            self.scene.pan_offset[0] += dx * 0.002
            self.scene.pan_offset[1] -= dy * 0.002

            self.scene.last_pan_x = x
            self.scene.last_pan_y = y




    def init_GL(self):
        # debug: print GL and GLS version
        # print('Vendor       : %s' % glGetString(GL_VENDOR))
        # print('OpenGL Vers. : %s' % glGetString(GL_VERSION))
        # print('GLSL Vers.   : %s' % glGetString(GL_SHADING_LANGUAGE_VERSION))
        # print('Renderer     : %s' % glGetString(GL_RENDERER))

        # set background color to black
        glClearColor(0, 0, 0, 0)     

        # Enable depthtest
        glEnable(GL_DEPTH_TEST)
        


    def on_mouse_button(self, win, button, action, mods):
        print("mouse button: ", win, button, action, mods)
        # TODO: realize arcball metaphor for rotations as well as
        #       scaling and translation paralell to the image plane,
        #       with the mouse. 
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.scene.mouse_pressed = True
                x, y = glfw.get_cursor_pos(win)
                self.scene.p1 = np.array(projectOnSphere(x, y, self.scene.arcball_radius, self.scene.width, self.scene.height))
            elif action == glfw.RELEASE:
                self.scene.mouse_pressed = False
        if button == glfw.MOUSE_BUTTON_MIDDLE:
            if action == glfw.PRESS:
                self.scene.zoom_pressed = True
                _, y = glfw.get_cursor_pos(win)
                self.scene.last_y = y
            elif action == glfw.RELEASE:
                self.scene.zoom_pressed = False
        if button == glfw.MOUSE_BUTTON_RIGHT:
            if action == glfw.PRESS:
                self.scene.pan_pressed = True
                x, y = glfw.get_cursor_pos(win)
                self.scene.last_pan_x = x
                self.scene.last_pan_y = y
            elif action == glfw.RELEASE:
                self.scene.pan_pressed = False



    def on_keyboard(self, win, key, scancode, action, mods):
        print("keyboard: ", win, key, scancode, action, mods)
        if action == glfw.PRESS:
            # ESC to quit
            if key == glfw.KEY_ESCAPE:
                self.exitNow = True
            if key == glfw.KEY_A:
                self.scene.animate = not self.scene.animate
            if key == glfw.KEY_P:
                self.scene.projection_mode = (self.scene.projection_mode + 1) % 2
                mode = "Orthographic" if self.scene.projection_mode else "Perspective"
                print(f"Projection mode: {mode}")
            if key == glfw.KEY_S:
                self.scene.shading_mode = (self.scene.shading_mode + 1) % 3
                modes = ["Wireframe", "Gouraud", "Phong"]
                print(f"Shading mode: {modes[self.scene.shading_mode]}")
            if key == glfw.KEY_X:
                rot = rotate_x(self.scene.keyboard_rotation_angle)
                self.scene.rotation_matrix = rot @ self.scene.rotation_matrix
                print("Rotated around X axis")
            if key == glfw.KEY_Y:
                rot = rotate_y(self.scene.keyboard_rotation_angle)
                self.scene.rotation_matrix = rot @ self.scene.rotation_matrix
                print("Rotated around Y axis")
            if key == glfw.KEY_Z:
                rot = rotate_z(self.scene.keyboard_rotation_angle)
                self.scene.rotation_matrix = rot @ self.scene.rotation_matrix
                print("Rotated around Z axis")



    def on_size(self, win, width, height):
        self.scene.set_size(width, height)


    def run(self):
        while not glfw.window_should_close(self.window) and not self.exitNow:
            # poll for and process events
            glfw.poll_events()

            # setup viewport
            width, height = glfw.get_framebuffer_size(self.window)
            glViewport(0, 0, width, height);

            # call the rendering function
            self.scene.draw()
            
            # swap front and back buffer
            glfw.swap_buffers(self.window)

        # end
        glfw.terminate()



# main function
if __name__ == '__main__':

    print("presse 'a' to toggle animation...")

    # set size of render viewport
    width, height = 640, 480

    # instantiate a scene
    scene = Scene(width, height)

    # pass the scene to a render window ... 
    rw = RenderWindow(scene)

    # ... and start main loop
    rw.run()
