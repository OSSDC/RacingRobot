import math
from collections import namedtuple

import bpy
import numpy as np
import matplotlib.pyplot as plt
import seaborn
import mathutils

class Position(object):
    def __init__(self, x, y, theta=0):
        super(Position, self).__init__()
        self.x, self.y = x, y
        self.theta = theta

    def norm(self):
        return np.linalg.norm([self.x, self.y])

    def update(self, norm, theta):
        self.x = norm * np.cos(theta)
        self.y = norm * np.sin(theta)

class Speed(Position):
    def __init__(self, vx, vy):
        super(Speed, self).__init__(vx, vy)

class Acceleration(Position):
    def __init__(self, ax, ay):
        super(Acceleration, self).__init__(ax, ay)

U_MAX_ACC = 25
ANGLE_OFFSET = 0
dt = 0.01

def convertToDegree(angle):
    return (angle * 180) / np.pi

def convertToRad(angle):
    return (angle * np.pi) / 180

def constrain(x, a, b):
    return np.max([a, np.min([x, b])])



class Car(object):
    def __init__(self, start_pos, mass, friction_coeff=1, dt=0.01):
        super(Car, self).__init__()
        self.pos = start_pos
        self.speed = Speed(0,0)
        self.acc = Acceleration(0,0)
        self.mass = mass
        # TODO: add air drag
        self.friction =  friction_coeff * mass
        self.dt = dt
        self.v = 0
        self.acc_norm = 0

    def stepSpeed(self, u_speed):
        sign_speed = np.sign(self.v)
        if self.v == 0:
            self.acc_norm = np.max([0, u_speed - self.friction]) if  u_speed >= 0 else np.min([0, u_speed + self.friction])
        else:
            self.acc_norm = u_speed - self.friction if sign_speed >= 0 else u_speed + self.friction
        new_speed = self.v + self.acc_norm * self.dt
        if np.sign(self.v) * np.sign(new_speed) == -1:
            self.v = 0
        else:
            self.v = new_speed

    def step(self, u_speed, u_angle, skip_speed=False):
        if not skip_speed:
            self.stepSpeed(u_speed)
        theta = car.pos.theta
        car.pos.x += self.v * np.cos(theta)
        car.pos.y += self.v * np.sin(theta)
        car.pos.theta += u_angle

def compute_bezier_curve(matrix_world, spline):
    # Draw the bezier
    if len(spline.bezier_points) >= 2:
        r = spline.resolution_u + 1
        segments = len(spline.bezier_points)
        if not spline.use_cyclic_u:
            segments -= 1

        points = []
        for i in range(segments):
            inext = (i + 1) % len(spline.bezier_points)

            knot1 = spline.bezier_points[i].co
            handle1 = spline.bezier_points[i].handle_right
            handle2 = spline.bezier_points[inext].handle_left
            knot2 = spline.bezier_points[inext].co

            _points = mathutils.geometry.interpolate_bezier(knot1, handle1, handle2, knot2, r)
            _points = [matrix_world * vec for vec in _points]
            points.extend(_points)
    return points

if __name__ == '__main__':
    # Blender objects
    track = bpy.data.objects['track_curve']
    cam = bpy.data.objects['car_camera']
    ANGLE_OFFSET = cam.rotation_euler[2]
    # Render options
    bpy.context.scene.render.resolution_x = 960
    bpy.context.scene.render.resolution_y = 540

    # Init Camera angle/position
    # cam.location[1] = 3.5

    car = Car(Position(cam.location[0], cam.location[1], 0),
              mass=10, friction_coeff=2, dt=dt)

    traj = [[],[], []]

    spline = track.data.splines[0]
    matrix_world = track.matrix_world
    points = compute_bezier_curve(matrix_world, spline)

    for i, point in enumerate(points):
        car.pos.x = point[0]
        car.pos.y = point[1]

        vec = points[(i + 1) % len(points)] - points[i]
        # Dirty FIX for ref trajectory
        if abs(vec[0]) < 1e-4:
            vec[0] = 1e-4

        car.pos.theta = np.arctan2(vec[1], vec[0])

        # Update Blender
        cam.location[0] = car.pos.x
        cam.location[1] = car.pos.y
        cam.rotation_euler[2] = ANGLE_OFFSET + car.pos.theta


        # Trajectory
        traj[0].append(car.pos.x)
        traj[1].append(car.pos.y)
        traj[2].append(convertToDegree(car.pos.theta))
        # Write Blender images
        image_path = 'render/{}.png'.format(i)
        bpy.context.scene.render.filepath = image_path
        bpy.ops.render.render(write_still=True)  # render


    plt.plot(traj[0], traj[1])
    ax = plt.axes()
    for idx, a in enumerate(traj[2]):
        if idx % 1 == 0:
            v = 5
            x,y = traj[0][idx], traj[1][idx]
            ax.arrow(x,y, v*np.cos(convertToRad(a)), v*np.sin(convertToRad(a)), head_width=0.1)

    plt.show()