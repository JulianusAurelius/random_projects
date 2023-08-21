"""
███████╗ ██████╗ ██╗      █████╗ ██████╗     ███████╗██╗███╗   ███╗██╗   ██╗██╗      █████╗ ████████╗ ██████╗ ██████╗ 
██╔════╝██╔═══██╗██║     ██╔══██╗██╔══██╗    ██╔════╝██║████╗ ████║██║   ██║██║     ██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗
███████╗██║   ██║██║     ███████║██████╔╝    ███████╗██║██╔████╔██║██║   ██║██║     ███████║   ██║   ██║   ██║██████╔╝
╚════██║██║   ██║██║     ██╔══██║██╔══██╗    ╚════██║██║██║╚██╔╝██║██║   ██║██║     ██╔══██║   ██║   ██║   ██║██╔══██╗
███████║╚██████╔╝███████╗██║  ██║██║  ██║    ███████║██║██║ ╚═╝ ██║╚██████╔╝███████╗██║  ██║   ██║   ╚██████╔╝██║  ██║
╚══════╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝    ╚══════╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝
"""
# credit to textkool.com for the ascii art

import pygame
import math
import copy
import random
# multithreading
import threading
# async
# import asyncio
# import signal
import time
import sys
import numpy as np

# note, I'm not adding curved reflectors. For the time I wanted to invest in this project, that would add almost another day.
# I've done the math, though, and have a few ideas on how to do it if anyone wants to try it out themselves.
# Ultimately, the slope, or angle, of a curved section, say from degree 0 to degree 90 (any more and you create an overhang that actually blocks the light),
# follows a tangent function, meaning if we take the integral for 1 period, we get 0, meaning that for a mirror that goes from 0 to 90 degrees,
# it's less than a linear mirror. Because from degrees 45-90, it reflects the light down, and from 0-45, it reflects the light up.
# Think of the angle of deflection of a photon coming from the top of the screen (270 degrees in the normal cartesian plane), and the angle
# of the tangent of the point it hits. Since half the arc is above 45, and half is below, then, nothing else taken into account, then half the light
# will be reflected right back into the sky. So, any solution with curved mirrors will have to take that into account, and will likely have the point
# touching the solar panels start at a tangent angle of 45 or 46 degrees, making it a non-smooth functions. This may have promise, but I'm not sure,
# there's 3 variables to play around with instead of 2, and it's not necessarily a linear problem anymore, making it more difficult to reason about.
# I would think the 3 variables would be the following:
    # 1. The angle of the tangent at the point of contact with the solar panel, from [45, 90] (or [46, 90] for practical computing purposes)
    # 2. The radius of the circle. This just gives us the center point by calculating the point 'r' away and perpendicular to the tangent line of the
        # point of contact with the solar panel. With 'r' being the radius
    # 3. The arc the mirror covers. This will never be more than 45 degrees, but more accurately will be between [tangent_angle, {90 or 89} - tangent_angle]
# feel free to convert to radians if that's easier for you.
# To let the user modify them, we would need to add a new control mechanism (other than up/down and left/right, maybe w/s or a/d)
# auto would be hard to implement for them, but could be done by allowing the user to 'lock' a single variable, then we can easily calculate the 2nd unlocked
# variable when the user changes the 1st unlocked variable
# to change, the user could perhaps just type 'line' or 'curve', and we could check if they're alread there. We'd probably need to add a member to
# the rotator class to give us the current equation of the circle, so we can easily check if we're on the line, and then modify the 'is_hit' function
# of the rotator class to use 2 different functions based on if it's linear or curved.
# when we change, we could simply keep the endpoint the same, and when going from linear to curved, just throw some default values at it,
# for curved to linear, we just make a line from the end point and and the end of the solar panel, calculate the angle, save it, and recalculate everything

# musings: but, I'm not sure if curved is even beneficial over a properly angled linear reflector. As if it can only compete at angles [45, 90],
# that means for every 1 unit we increase for x, we increase more than 1 angle in y, meaning that it doesn't have the ability to capture more energy,
# which is the whole point, and the amount of energy it's even _able_ to bring to the solar panel is a direct function of the horizontal area it brings.
# maybe, we can do curved, but have a center point that they focus the light on, which then distributes it back onto the panel
# this would reflect the light back at that particular spot, but may allow us to capture far more energy, without drastically increasing the height
# and length of the reflector. Think of the JWST, or those liquid salt solar plants in the desert or something, the ones with the towers, and the
# ones with the tubes. A potential cost of that would then be that center point would need to be suspended somehow, managed by the motors to be able
# to collapse in bad weather, it would need to be able to withstand extremely high temperatures, and it would need to likely be highly polished or something
# this is something that could actually make the curved panels desireable to do.
# it's probably easy to calculate the focal point. We'd likely look at optics, or could even look at 5 examples (angles: {45, 90, 67, 56, 79})
# and see if we can find a pattern. My concern is that it's not the line perpendicular to the tangent line, but the reflection line after
# a photon (coming from the top) strikes the angle. For angles [45, 90], it will go down, so it will either hit the solar panel or the reflector.
# there's a chance that if it's large enough, that it could also hit the other reflector, so that may be a thing we need to play with as well.

# note that in pygame, the unit circle is flipped over the x-axis, so it may be a bit confusing how this works, and it even annoys me,
# it would be so much easier to intuit about problems and the math, without having to translate the final equations


stop_event = threading.Event()

# check if there's a command line argument
global AUTO_ADJUST
AUTO_ADJUST = False
if len(sys.argv) > 1:
    if sys.argv[1] == "auto":
        AUTO_ADJUST = True


pygame.init()
display = (900, 900)
screen = pygame.display.set_mode(display)
pygame.display.set_caption('Solar Panel Simulation')

class reflector:
    def __init__(self, start, angle, size):
        self.start = start
        self.angle = angle
        self.size = (size-1)//2
        self.end = (start[0] - math.cos(math.radians(angle)) * self.size, start[1] - math.sin(math.radians(angle)) * self.size)
    
    def draw(self):
        pygame.draw.line(screen, (255, 255, 255), self.start, self.end, 5)
    
    def is_hit(self, point, tolerance):
        # take the distance of the point to each endpoint, with a tolerance of .1
        # dist_to_p1 = math.sqrt((point[0] - self.start[0])**2 + (point[1] - self.start[1])**2)
        # dist_to_p2 = math.sqrt((point[0] - self.end[0])**2 + (point[1] - self.end[1])**2)
        # if is_between(point, self.start, self.end, tolerance):
        #     return True
        # else:
        #     return False
        closest_point = closest_point_on_line_corrected(self.start, self.end, point)
        # find the distance from the closest point to the point
        dist = math.sqrt((point[0] - closest_point[0])**2 + (point[1] - closest_point[1])**2)
        if dist < tolerance:
            return True

solar_panel_points = [(display[1]/3, display[0]-100), (display[1]/3*2, display[0]-100)]
solar_panel_length = int(solar_panel_points[1][0] - solar_panel_points[0][0])
solar_panel_photon_count = [0 for i in range(solar_panel_length)]
reflector_1_angle = 60
reflector_1 = reflector(solar_panel_points[0], reflector_1_angle, solar_panel_length)
reflector_2 = reflector(solar_panel_points[1], 180-reflector_1_angle, solar_panel_length)
reflectors = [reflector_1, reflector_2]

def calculate_angle_strike(striking_angle, reflector_angle):
    difference = reflector_angle - striking_angle
    if difference < 0:
        difference += 360
    
    final_angle = reflector_angle + difference
    if final_angle > 360:
        final_angle -= 360
    
    return final_angle

def closest_point_on_line_corrected(start_point, end_point, point):
    # Convert points to vectors
    A = start_point
    B = end_point
    P = point
    
    # Calculate vector AB and AP
    AB = (B[0]-A[0], B[1]-A[1])
    AP = (P[0]-A[0], P[1]-A[1])
    
    # Calculate dot products
    AB_dot_AB = AB[0]*AB[0] + AB[1]*AB[1]
    AP_dot_AB = AP[0]*AB[0] + AP[1]*AB[1]
    
    # Calculate projection scalar
    t = AP_dot_AB / AB_dot_AB
    
    # Ensure t is clamped between 0 and 1 to remain on the line segment
    t = max(0, min(1, t))
    
    # Calculate the closest point C on the line segment
    C = [A[0] + t*AB[0], A[1] + t*AB[1]]
    
    return C

def is_between(point, start, end, tolerance=1):
    # # see if the distance from the point to the start and end is the same as the distance from the start to the end
    # d1 = math.sqrt((point[0] - start[0])**2 + (point[1] - start[1])**2)
    # d2 = math.sqrt((point[0] - end[0])**2 + (point[1] - end[1])**2)
    # length = math.sqrt((start[0] - end[0])**2 + (start[1] - end[1])**2)
    # # since comparing them with a tolerance yields more tolerance in the middle than the ends,
    # # we'll use a tolerance related to the difference between the two distances as the difference divided by the total distance
    # # tolerance = max(max(d1, d2)**2 / (length**2), .5)
    # if abs(d1 + d2 - length) < tolerance:
    #     return True
    # else:
    #     return False
    
    # find the equation of the line
    # y = mx + b
    # m = (y2-y1)/(x2-x1)
    m = (end[1] - start[1]) / (end[0] - start[0])
    # b = y - mx
    b = start[1] - m * start[0]
    # plug in the point's x value and see if we're within the tolerance of the point's y value
    y = m * point[0] + b
    if abs(y - point[1]) < tolerance:
        return True
    else:
        return False

x = 0
class photon:
    def __init__(self, start, do_I_add_to_list=True):
        # print("Photon created with start:",start)
        self.start = start
        self.cur_ball = [start, 0]
        self.path = [[start, 0]]
        # straight down
        self.angle = 90 # working for calculating path, and runtime for ball directions
        self.x_accum = 0.0
        self.y_accum = 0.0
        self.angle_list = []
        self.i = 0
        self.flag = False
        self.done = False
        self.do_I_add = do_I_add_to_list
    
    def calculate_path(self):
        cur_p = self.path[0].copy()
        tmp=False
        while True:
            if stop_event.is_set():
                return
            # print("Before:",cur_p)
            # calculate the next point
            self.x_accum += math.cos(math.radians(self.angle))
            self.y_accum += math.sin(math.radians(self.angle))
            # print("x_accum:",self.x_accum)
            # print("y_accum:",self.y_accum)
            # # angle
            # print("Angle:",self.angle)
            if self.x_accum >= 1:
                cur_p[0] += 1
                self.x_accum -= 1
            elif self.x_accum <= -1:
                cur_p[0] -= 1
                self.x_accum += 1
            if self.y_accum >= 1:
                cur_p[1] += 1
                self.y_accum -= 1
            elif self.y_accum <= -1:
                cur_p[1] -= 1
                self.y_accum += 1
            # print("After:",cur_p)
            # check if we've hit the bottom of the screen
            if cur_p[0] > display[1]:
                self.path.append(cur_p)
                cur_p = cur_p.copy()
                # print("Hit the bottom of the screen!")
                self.angle = 90
                return
            # check if we've hit the top of the screen
            if cur_p[0] < 0:
                self.path.append(cur_p)
                cur_p = cur_p.copy()
                # print("Hit the top of the screen!")
                self.angle = 90
                return
            # check if we've hit the left or right of the screen
            if cur_p[1] < 0:
                self.path.append(cur_p)
                cur_p = cur_p.copy()
                # print("Hit the left of the screen!")
                # print("cur_p:",cur_p)
                self.angle = 90
                return
            if cur_p[1] > display[0]:
                self.path.append(cur_p)
                cur_p = cur_p.copy()
                # print("Hit the right of the screen!")
                # print(self.path)
                self.angle = 90
                return
            
            b = True
            # check if we've hit a reflector
            for r in reflectors:
                if r.is_hit(cur_p, .5):
                    if tmp:
                        print("Error! Hit two reflectors at once!")
                        # print ALL the things!
                        print("Photon:",self)
                        print("Photon path:",self.path)
                        print("Photon angle:",self.angle)
                        print("Photon angle list:",self.angle_list)
                        print("Photon x_accum:",self.x_accum)
                        print("Photon y_accum:",self.y_accum)
                        print("Photon cur_p:",cur_p)
                        print("Photon i:",self.i)
                        print("Photon flag:",self.flag)
                        print("Photon done:",self.done)
                        print("Photon start:",self.start)
                        print("Photon cur_ball:",self.cur_ball)
                        print("Reflector:",r.start,r.end,r.size)
                        exit()
                    b = False
                    tmp = True
                    # print("Hit a reflector!")
                    self.path.append(cur_p)
                    # cur_p = cur_p.copy()
                    # set cur_p to the closest point on the reflector
                    cur_p = closest_point_on_line_corrected(r.start, r.end, cur_p)

                    # calculate the new angle
                    reflector_angle = r.angle
                    self.angle = calculate_angle_strike(self.angle, reflector_angle)
                    self.angle_list.append(self.angle)

                    # 10% chance we get absorbed
                    if random.randint(0, 9) == 0:
                        # print("Photon absorbed!")
                        # print("Hit the bottom of the screen!")
                        self.angle = 90
                        return
                    # print("New angle:",self.angle)
                    # print("Angle list:",self.angle_list)
                    # print("Path:",self.path)
                    while (r.is_hit(cur_p, 5)):
                        if stop_event.is_set():
                            return
                        self.x_accum += math.cos(math.radians(self.angle))
                        self.y_accum += math.sin(math.radians(self.angle))
                        # print("x_accum:",self.x_accum)
                        # print("y_accum:",self.y_accum)
                        # angle
                        # print("Angle:",self.angle)
                        if self.x_accum >= 1:
                            cur_p[0] += 1
                            self.x_accum -= 1
                        elif self.x_accum <= -1:
                            cur_p[0] -= 1
                            self.x_accum += 1
                        if self.y_accum >= 1:
                            cur_p[1] += 1
                            self.y_accum -= 1
                        elif self.y_accum <= -1:
                            cur_p[1] -= 1
                            self.y_accum += 1
                        # still check if we've hit the solar panel
                        if abs(cur_p[1] - solar_panel_points[0][1]) < 2:
                            if cur_p[0] >= solar_panel_points[0][0] and cur_p[0] <= solar_panel_points[1][0]:
                                self.path.append(cur_p)
                                cur_p = cur_p.copy()
                                # print("Hit the solar panel!")
                                self.angle = 90
                                # print(cur_p[0])
                                # print(int(solar_panel_points[0][0]))
                                # print(int(cur_p[0]) - int(solar_panel_points[0][0]))
                                # print(solar_panel_photon_count)
                                if self.do_I_add:
                                    # print(int(cur_p[0]))
                                    # print(int(solar_panel_points[0][0]))
                                    solar_panel_photon_count[ int(cur_p[0]) - int(solar_panel_points[0][0]) - 1] += 1
                                return
                    break
            if b:
                tmp=False
            # check if we've hit the solar panel
            # if cur_p[1] == solar_panel_points[0][1]:
            if abs(cur_p[1] - solar_panel_points[0][1]) < 2:
                if cur_p[0] >= solar_panel_points[0][0] and cur_p[0] <= solar_panel_points[1][0]:
                    self.path.append(cur_p)
                    cur_p = cur_p.copy()
                    # print("Hit the solar panel!")
                    self.angle = 90
                    # print(cur_p[0])
                    # print(int(solar_panel_points[0][0]))
                    # print(int(cur_p[0]) - int(solar_panel_points[0][0]))
                    # print(solar_panel_photon_count)
                    if self.do_I_add:
                        index = int(cur_p[0]) - int(solar_panel_points[0][0])
                        index = 0 if index < 0 else index
                        index = solar_panel_length - 1 if index >= solar_panel_length else index
                        solar_panel_photon_count[ index ] += 1
                    return
        
        self.angle = 90
            
    def draw(self):
        if self.done:
            return
        if len(self.path) <= 1:
            return
        # draw a small yellow circle at self.cur_ball
        pygame.draw.circle(screen, (255, 255, 0), self.cur_ball, 5)
        
        self.x_accum += math.cos(math.radians(self.angle))
        self.y_accum += math.sin(math.radians(self.angle))
        if self.x_accum >= 1:
            self.cur_ball[0] += 1
            self.x_accum -= 1
        elif self.x_accum <= -1:
            self.cur_ball[0] -= 1
            self.x_accum += 1
        
        if self.y_accum >= 1:
            self.cur_ball[1] += 1
            self.y_accum -= 1
        elif self.y_accum <= -1:
            self.cur_ball[1] -= 1
            self.y_accum += 1
        
        self.cur_ball[0] = int(self.cur_ball[0])
        self.cur_ball[1] = int(self.cur_ball[1])

        # print("x_accum:",self.x_accum)
        # print("y_accum:",self.y_accum)
        # print("self.ball:",self.cur_ball)
        # print("self.path:",self.path)

        # if self.cur_ball[1] <= -50:
        #     exit()
        if self.cur_ball[1] < 0 or self.cur_ball[1] > display[0] or self.cur_ball[0] < 0 or self.cur_ball[0] > display[1]:
            self.cur_ball = [self.start, 0]
            self.x_accum = 0.0
            self.y_accum = 0.0
            self.angle = 90
            self.i = 0
            self.done = True
            return True

        close_to_point = False
        # print(self.path)
        # print(self.cur_ball)\
        for p in self.path[1:]:
            # print(self.i)
            # print(self.angle_list)
            # print(self.path)
            if p == self.path[-1] and abs(p[0] - self.cur_ball[0]) <= 3 and abs(p[1] - self.cur_ball[1]) <= 3:
                # print("We're at the end of the path!")
                # we're at the end of the path, reset the ball
                self.cur_ball = [self.start, 0]
                self.x_accum = 0.0
                self.y_accum = 0.0
                self.angle = 90
                self.i = 0
                self.done = True
                return True
            if abs(p[0] - self.cur_ball[0]) <= 1 and abs(p[1] - self.cur_ball[1]) <= 1:
                close_to_point = True
                # print("We're at the next point in the path!")
                # print("self.i:",self.i)
                # print("self.flag:",self.flag)
                if self.flag:
                    break
                self.flag = True
                # we're at the next point in the path
                self.cur_ball = p.copy()
                self.angle = self.angle_list[self.i]
                self.i += 1
                # if p == self.path[2]:
                #     exit()
                break
        if not close_to_point:
            self.flag = False

    def draw_all_paths(self):
        old_path = self.path[0]
        # print(self.path)
        for p in self.path[1:]:
            # pygame.draw.line(screen, (255, 255, 0), old_path, p, 5)
            # dark yellow
            pygame.draw.line(screen, (100, 100, 0), old_path, p, 2)
            old_path = p
    
    def calculate2(self):
        # ensure all the points in self.path are not within 5 pixels of each other
        for p1 in self.path:
            for p2 in self.path:
                if p1 == p2:
                    continue
                distance = math.sqrt( (p1[0] - p2[0])**2 + (p1[1] - p2[1])**2 )
                if distance <= 10:
                    # check if the Y is close to 800
                    if abs(p1[1] - 800) <= 1:
                        # see if the x is near either end of the solar panel
                        if abs(p1[0] - solar_panel_points[0][0]) <= 1 or abs(p1[0] - solar_panel_points[1][0]) <= 1:
                            print("Double point near panel")
                            continue
                    if abs(p2[1] - 800) <= 1:
                        # see if the x is near either end of the solar panel
                        if abs(p2[0] - solar_panel_points[0][0]) <= 1 or abs(p2[0] - solar_panel_points[1][0]) <= 1:
                            print("Double point near panel")
                            continue

                    # delete p2 from self.path
                    # print("Deleting a point!")
                    # print("Distance:",distance)
                    # print("p1:",p1)
                    # print("p2:",p2)
                    self.path.remove(p2)

photons = [photon(i, False) for i in range(10, display[0]-10, 25)]
photon_is_done = [False for i in range(len(photons))]
invisible_photon_list = [photon(i, True) for i in range(1, display[0]-1, 1)]
# print(len(invisible_photon_list))

# thread this functions
def calculate_reflector_points():
    global photons
    global invisible_photon_list
    # tmp_working_photons = []
    for p in photons:
        # deep copy
    #     tmp_working_photons.append(copy.deepcopy(p))
    #     if stop_event.is_set():
    #         return
    # for p in tmp_working_photons:
    #     if stop_event.is_set():
    #         return
        p.cur_ball = [p.start, 0]
        p.x_accum = 0.0
        p.y_accum = 0.0
        p.angle = 90
        p.i = 0
        p.done = False
        p.path = [[p.start, 0]]   
        p.angle_list = []
        p.flag = False
        if stop_event.is_set():
            return
        p.calculate_path()
        if stop_event.is_set():
            return
        p.calculate2()
    # this can be killed at any time, so need to make sure there's no locks or anything
    # tmp_working_invisible_photons = []
    for p in invisible_photon_list:
    #     tmp_working_invisible_photons.append(copy.deepcopy(p))
    #     if stop_event.is_set():
    #         return
    # tmp_panel_array = [0 for i in range(solar_panel_length)]
    # for p in tmp_working_invisible_photons:
        if stop_event.is_set():
            return
        p.cur_ball = [p.start, 0]
        p.x_accum = 0.0
        p.y_accum = 0.0
        p.angle = 90
        p.i = 0
        p.done = False
        p.path = [[p.start, 0]]   
        p.angle_list = []
        p.flag = False
        p.calculate_path()
        if stop_event.is_set():
            return
        p.calculate2()
        # check if this thread received a signal, and if so, we stop
    # if we've reached here without exiting (stop_event), then we're safe to replace the actual photons and invisible_photons
    # photons = tmp_working_photons
    # solar_panel_photon_count = tmp_panel_array
    # invisible_photon_list = tmp_working_invisible_photons


thread_list = []

# print(reflector_1.start, reflector_1.end)

# print(photons[0].path)
# print(x)


def draw():
    screen.fill((0, 0, 0))
    for r in reflectors:
        r.draw()
    for p in photons:
        p.draw_all_paths()
        ret = p.draw()
        if ret:
            photon_is_done[photons.index(p)] = True
    # if all photon_is_done are True, then reset them all to False
    if all(photon_is_done):
        # turn all photon_is_done to False
        for i in range(len(photon_is_done)):
            photon_is_done[i] = False
            photons[i].done = False

        # p.draw_all_paths()
    # draw the solar panel, light gray
    pygame.draw.line(screen, (200, 200, 200), solar_panel_points[0], solar_panel_points[1], 5)
    # draw the load among the solar panel, light gray
    panel_points = []
    # index = 0
    panel_points.append(solar_panel_points[0])
    for bins in range(solar_panel_length//5):
        sum = 0
        for pixels in range(bins*5, (bins+1)*5):
            sum += solar_panel_photon_count[pixels]
        panel_points.append((solar_panel_points[0][0] + bins*5, solar_panel_points[0][1] + sum*3))
        panel_points.append((solar_panel_points[0][0] + bins*5 + 5, solar_panel_points[0][1] + sum*3))
    panel_points.append(solar_panel_points[1])
    panel_points.append(solar_panel_points[0])
    pygame.draw.polygon(screen, (100, 200, 200), panel_points, 0)
    # print(panel_points)

    # draw a circle in the middle of the screen, with a line going from the center to the edge at 0 degrees
    # pygame.draw.circle(screen, (255, 255, 0), (display[0]//2, display[1]//2), 50, 5)
    # pygame.draw.line(screen, (255, 255, 0), (display[0]//2, display[1]//2),
    #                     (display[0]//2 + 50 * math.cos(math.radians(0)), display[1]//2 + 50 * math.sin(math.radians(0))), 5)
    # # now 90, but red
    # pygame.draw.line(screen, (255, 0, 0), (display[0]//2, display[1]//2),
    #                     (display[0]//2 + 50 * math.cos(math.radians(90)), display[1]//2 + 50 * math.sin(math.radians(90))), 5)
    
def calculate_third_side(a, b, angle_C_degrees):
    """
    Calculate the third side (c) of a triangle using the Law of Cosines.
    """
    angle_C = np.radians(angle_C_degrees)
    c = np.sqrt(a**2 + b**2 - 2 * a * b * np.cos(angle_C))
    return c

def calculate_other_angles(a, c, angle_C_degrees):
    """
    Calculate the other two angles (A and B) of a triangle.
    Angle A is calculated using the Law of Sines, and
    Angle B is derived from the sum of angles in a triangle.
    """
    angle_C = np.radians(angle_C_degrees)
    
    angle_A_rad = np.arcsin(a * np.sin(angle_C) / c)
    angle_A_degrees = np.degrees(angle_A_rad)
    
    angle_B_degrees = 180 - angle_A_degrees - angle_C_degrees
    
    return angle_A_degrees, angle_B_degrees

def SAS_triangle_info(a, b, angle_C_degrees):
    """
    Calculate the remaining side and angles of a triangle based on SAS input.
    Returns the third side (c) and the other two angles (A and B).
    """
    c = calculate_third_side(a, b, angle_C_degrees)
    angle_A_degrees, angle_B_degrees = calculate_other_angles(a, c, angle_C_degrees)
    
    return c, angle_A_degrees, angle_B_degrees

def calculate_third_angle(angle_A_degrees, angle_B_degrees):
    """
    Calculate the third angle (C) of a triangle given two angles.
    """
    angle_C_degrees = 180 - angle_A_degrees - angle_B_degrees
    return angle_C_degrees

def calculate_other_sides(a, angle_A_degrees, angle_B_degrees, angle_C_degrees):
    """
    Calculate the other two sides (b and c) of a triangle using the Law of Sines.
    """
    # Convert degrees to radians
    angle_A = np.radians(angle_A_degrees)
    angle_B = np.radians(angle_B_degrees)
    angle_C = np.radians(angle_C_degrees)
    
    b = (a * np.sin(angle_B)) / np.sin(angle_A)
    c = (a * np.sin(angle_C)) / np.sin(angle_A)
    
    return b, c

def AAS_triangle_info(a, angle_A_degrees, angle_C_degrees):
    """
    Corrected function to calculate the remaining sides and angle of a triangle based on AAS input.
    Returns the third angle (B) and the other two sides (b and c).
    """
    # Calculate angle B
    angle_B_degrees = 180 - angle_A_degrees - angle_C_degrees
    
    # Convert degrees to radians
    angle_A = np.radians(angle_A_degrees)
    angle_B = np.radians(angle_B_degrees)
    angle_C = np.radians(angle_C_degrees)
    
    # Calculate sides b and c using the Law of Sines
    b = (a * np.sin(angle_B)) / np.sin(angle_A)
    c = (a * np.sin(angle_C)) / np.sin(angle_A)
    
    return angle_B_degrees, b, c

def SSS_triangle_angles(a, b, c):
    """
    Calculate the angles of a triangle based on SSS input.
    Returns the angles A, B, and C.
    """
    # Calculate angle A using the Law of Cosines
    # print args
    # print("a: ", a, "b: ", b, "c: ", c)
    cos_A = (b**2 + c**2 - a**2) / (2 * b * c)
    # print("cos_A: ", cos_A)
    angle_A_degrees = np.degrees(np.arccos(cos_A))
    # print("angle_A_degrees: ", angle_A_degrees)
    
    # Calculate angle B using the Law of Cosines
    cos_B = (a**2 + c**2 - b**2) / (2 * a * c)
    # print("cos_B: ", cos_B)
    angle_B_degrees = np.degrees(np.arccos(cos_B))
    # print("angle_B_degrees: ", angle_B_degrees)
    
    # Calculate angle C using the properties of triangles
    angle_C_degrees = 180 - angle_A_degrees - angle_B_degrees
    # print("angle_C_degrees: ", angle_C_degrees)
    
    return angle_A_degrees, angle_B_degrees, angle_C_degrees


keydown = False
mouse_click = False
func = None

def initial_calc():
    stop_event.set()
    for r in reflectors:
        r.end = (r.start[0] - math.cos(math.radians(r.angle)) * r.size, r.start[1] - math.sin(math.radians(r.angle)) * r.size)

def final_calc():
    global solar_panel_photon_count
    solar_panel_photon_count = [0 for i in range(solar_panel_length)]
    # kill all threads in thread_list
    
    # start a new thread
    stop_event.clear()
    # go through and remove all threads from thread_list
    for t in thread_list:
        t.join()
        thread_list.remove(t)
    # start a new thread
    thread_list.append(threading.Thread(target=calculate_reflector_points))
    # thread_list[0] = threading.Thread(target=calculate_reflector_points)
    thread_list[0].start()

def decrease_angle():
    reflectors[0].angle -= 1
    reflectors[1].angle += 1
    if reflectors[0].angle <= 45:
        reflectors[0].angle = 46
        reflectors[1].angle = 180 - reflectors[0].angle
    if reflectors[0].angle >= 90:
        reflectors[0].angle = 89
        reflectors[1].angle = 180 - reflectors[0].angle
    if AUTO_ADJUST:
        # calculate the new size of the reflectors using the AAS functions, and the current angle, size, and solar panel length
        angle_C_degrees, b, c = AAS_triangle_info(solar_panel_length,
                                                90 - reflectors[1].angle, 180 - reflectors[1].angle)
        reflectors[0].size = abs(b)
        angle_C_degrees, b, c = AAS_triangle_info(solar_panel_length,
                                                90 - reflectors[0].angle, 180 - reflectors[0].angle)
        reflectors[1].size = abs(b)
    # go through all of the photons and recalculate their paths
    initial_calc()

def increase_angle():
    reflectors[0].angle += 1
    reflectors[1].angle -= 1
    if reflectors[0].angle <= 45:
        reflectors[0].angle = 46
        reflectors[1].angle = 180 - reflectors[0].angle
    if reflectors[0].angle >= 90:
        reflectors[0].angle = 89
        reflectors[1].angle = 180 - reflectors[0].angle
    if AUTO_ADJUST:
        # calculate the new size of the reflectors using the AAS functions, and the current angle, size, and solar panel length
        angle_C_degrees, b, c = AAS_triangle_info(solar_panel_length,
                                                90 - reflectors[1].angle, 180 - reflectors[1].angle)
        reflectors[0].size = abs(b)
        angle_C_degrees, b, c = AAS_triangle_info(solar_panel_length,
                                                90 - reflectors[0].angle, 180 - reflectors[0].angle)
        reflectors[1].size = abs(b)
    # go through all of the photons and recalculate their paths
    initial_calc()

def increase_size():
    reflectors[0].size += 1
    reflectors[1].size += 1
    if AUTO_ADJUST:
        # calculate with SAS
        # c, angle_A_degrees, angle_B_degrees = SAS_triangle_info(solar_panel_length,
        #                                                     reflectors[0].size, reflectors[0].angle)
        A, B, C = SSS_triangle_angles(solar_panel_length, reflectors[0].size, math.sqrt((solar_panel_points[1][0] - reflectors[0].end[0])**2 +
                                                                                    (solar_panel_points[1][1] - reflectors[0].end[1])**2))
        # print("A: " + str(A) + " B: " + str(B) + " C: " + str(C))
        reflectors[0].angle = B
        # c, angle_A_degrees, angle_B_degrees = SAS_triangle_info(solar_panel_length,
        #                                                     reflectors[1].size, reflectors[1].angle)
        A, B, C = SSS_triangle_angles(solar_panel_length, reflectors[1].size, math.sqrt((solar_panel_points[0][0] - reflectors[1].end[0])**2 +
                                                                                    (solar_panel_points[0][1] - reflectors[1].end[1])**2))
        reflectors[1].angle = B
        # go through all of the photons and recalculate their paths
        if reflectors[0].angle <= 45:
            # quick hack, also auto adjust angle and size together
            decrease_angle()
        if reflectors[0].angle >= 90:
            increase_angle()
        
    initial_calc()

def decrease_size():
    reflectors[0].size -= 1
    reflectors[1].size -= 1
    if AUTO_ADJUST:
        # calculate with SAS
        # c, angle_A_degrees, angle_B_degrees = SAS_triangle_info(solar_panel_length,
        #                                                     reflectors[0].size, reflectors[0].angle)
        A, B, C = SSS_triangle_angles(solar_panel_length, reflectors[0].size, math.sqrt((solar_panel_points[1][0] - reflectors[0].end[0])**2 +
                                                                                    (solar_panel_points[1][1] - reflectors[0].end[1])**2))
        # print("A: " + str(A) + " B: " + str(B) + " C: " + str(C))
        reflectors[0].angle = B
        # c, angle_A_degrees, angle_B_degrees = SAS_triangle_info(solar_panel_length,
        #                                                     reflectors[1].size, reflectors[1].angle)
        A, B, C = SSS_triangle_angles(solar_panel_length, reflectors[1].size, math.sqrt((solar_panel_points[0][0] - reflectors[1].end[0])**2 +
                                                                                    (solar_panel_points[0][1] - reflectors[1].end[1])**2))
        reflectors[1].angle = B
        # go through all of the photons and recalculate their paths
        if reflectors[0].angle <= 45:
            # quick hack, also auto adjust angle and size together
            decrease_angle()
        if reflectors[0].angle >= 90:
            increase_angle()
        
    initial_calc()

font = pygame.font.SysFont("Arial", 30)
clock = pygame.time.Clock()
input_string = ""
inputting = False
turn = 0

reflector_1.angle -= 1
reflector_2.angle += 1
increase_angle()
final_calc()

run = True
while run:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        # mouse button down
        if event.type == pygame.MOUSEBUTTONDOWN:
            run = False
    # print("hi")

    # draw the intro
    total_spacing = 0
    spacing = 50
    inner_spacing = 30
    screen.fill((200, 200, 255))
    screen.blit(font.render("Welcome to the Solar Panel Simulator!", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Click to continue", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Click during the simulation to bring up the info box", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("In the info box, it specifies the angle, then the relative,", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("multiplicative increase in solar power hitting the panel,", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("the last number is the vertical height of the reflectors", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Press left and right to change the angle of the reflectors by typing it", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Press enter to process the inputted string", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Press up and down to change the size of the reflectors", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("(Keep in mind that this part is a WIP and does not currently)", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("(work properly with auto)", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Press space to toggle auto adjust", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("If you specify the command line argument 'auto', it will", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("automatically adjust the angle and size to always hit the", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("solar panel optimally. You can also type auto in the info box", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("Under the panel, we show the distribution of solar power", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("along the power, by calculating 1 ray per pixel at the top", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("of the screen, with a 10% chance of a photon being absorbed", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("by the reflectors for a deflection", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += spacing
    screen.blit(font.render("This can be used to calculate the feasibility or ROI of solar power", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("in more Northern areas, or just reduce cost by reducing the number", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("of panels, while retaining power. But thought should still be given", True, (0, 0, 0)), (0, total_spacing))
    total_spacing += inner_spacing
    screen.blit(font.render("to the cost of the panels, constructions, software for the motors, etc", True, (0, 0, 0)), (0, total_spacing))

    pygame.display.update()


def main():
    run = True
    need_recalc = False
    while run:
        draw()
        global keydown
        global mouse_click
        global turn
        global AUTO_ADJUST
        global time
        global input_string
        # print(len(thread_list))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                clock.tick(60)
                # decrease angle of reflectors if left
                if event.key == pygame.K_LEFT:
                    keydown = True
                    func = decrease_angle
                    turn += 1
                    func()
                    need_recalc = True
                # increase angle of reflectors
                elif event.key == pygame.K_RIGHT:
                    keydown = True
                    func = increase_angle
                    turn += 1
                    func()
                    need_recalc = True
                elif event.key == pygame.K_UP:
                    keydown = True
                    func = increase_size
                    turn += 1
                    func()
                    need_recalc = True
                elif event.key == pygame.K_DOWN:
                    keydown = True
                    func = decrease_size
                    turn += 1
                    func()
                    need_recalc = True
                # else if enter, process the inputted string
                else:
                    if not AUTO_ADJUST:
                        if event.key == pygame.K_RETURN:
                            # expect: degree
                            token = input_string.strip()
                            try:
                                reflectors[0].angle = int(token)
                                reflectors[1].angle = 180-int(token)
                            except:
                                # try to see if it's 'auto'
                                if token == "auto":
                                    AUTO_ADJUST = True
                                    print("Auto adjust enabled")
                                else:
                                    print("Invalid input")
                            input_string = ""
                            inputting = False
                        # else if backspace, remove the last character from the inputted string
                        elif event.key == pygame.K_BACKSPACE:
                            input_string = input_string[:-1]
                        # else if typing, add the character to the inputted string
                        elif event.key in range(256):
                            input_string += chr(event.key)

            if event.type == pygame.KEYUP:
                clock.tick(120)
                if need_recalc and keydown:
                    need_recalc = False
                    keydown = False
                    func = None
                    print("Running final calc")
                    # write 'please wait' at the bottom of the screen in the middle
                    pygame.draw.rect(screen, (180, 180, 180), (display[0]/2-100, display[1]-50, 200, 120))
                    screen.blit(font.render("Please wait...", True, (0, 0, 0)), (display[0]/2-100, display[1]-50))
                    pygame.display.update()
                    # time.sleep(10)
                    start_time = time.time()
                    final_calc()
                    print("Final calc took " + str(time.time()-start_time) + " seconds")
            # check for mouse clicks
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_click = not mouse_click
                if mouse_click:
                    inputting = True
                # print(pygame.mouse.get_pos())

        if keydown:
            if turn == 0:
                func()
                need_recalc = True
            turn += 1
            turn %= 50
        
        if mouse_click:
            # white box in the top right, displaying the angle of the reflectors
            pygame.draw.rect(screen, (255, 255, 255), (display[0]-200, 0, 200, 150))
            # print the angle of the reflectors on the screen
            screen.blit(font.render(str(reflectors[0].angle) + '°', True, (0, 0, 0)), (display[0]-200, 0))
            # screen.blit(font.render(str(reflectors[1].angle), True, (0, 0, 0)), (display[0]-100, 25))   
            value = sum(solar_panel_photon_count)
            value /= solar_panel_length
            # round to 2 decimal places
            value = round(value, 2)
            # print the average number of photons per pixel on the screen
            screen.blit(font.render(str(value) + "x Power", True, (0, 0, 0)), (display[0]-200, 25))
            # calculate the height of the reflectors
            height = reflectors[0].size * math.sin(math.radians(reflectors[0].angle))
            # normalize the height to the size of the solar panel, since while we measure in pixels,
            # it's ambiguous as to what unit the panel actually is. This gives us a multiplicative
            # factor that we can measure against the size of the panel we're using
            height /= solar_panel_length
            # round to 2 decimal places
            height = round(height, 1)
            # print the height of the reflectors on the screen
            screen.blit(font.render(str(height) +" vert len", True, (0, 0, 0)), (display[0]-200, 50))
            # print the length of the reflectors on the screen
            total_length = round(reflectors[0].size / solar_panel_length, 1)
            screen.blit(font.render(str(round(total_length,2)) + " total len", True, (0, 0, 0)), (display[0]-200, 75))
            # display input string
            if inputting:
                screen.blit(font.render(input_string, True, (0, 0, 0)), (display[0]-200, 100))

        pygame.display.update()
        


    pygame.quit()

if __name__ == '__main__':
    main()
