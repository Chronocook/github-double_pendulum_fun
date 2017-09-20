
# -*- coding: utf-8 -*-
""""
This code animates a double pendulum!

Dependancies (anaconda has these):
numpy
scipy

Note: if you don't have ffmpeg installed you need to run this once with
the import imageio uncommented.

Original integration code at:
http://matplotlib.org/examples/animation/double_pendulum_animated.html
Double pendulum formula translated from the C code at
http://www.physics.usyd.edu.au/~wheat/dpend_html/solve_dpend.c

@author : Brad Beechler (brad.beechler@uptake.com)
Modified: 20170206 (Brad Beechler)
"""

from logger import log
from numpy import sin, cos
import numpy as np
import multiprocessing as mp

import scipy.integrate as integrate
### Only need to run once to download ffmpeg
#import imageio
#imageio.plugins.ffmpeg.download()
import moviepy.editor as mpy #pip install moviepy

MAX_TIME = 100
DT       = 0.05
G        = 9.8  # acceleration due to gravity, in m/s^2
length_1 = 1.0  # length of pendulum weight 1 in m
length_2 = 0.5  # length of pendulum weight 2 in m
mass_1   = 1.0  # mass of pendulum weight 1 in kg
mass_2   = 0.8  # mass of pendulum weight 2 in kg
mass_t   = mass_1 + mass_2  # total mass

COLOR = {}
COLOR['black']       = [0.0,0.0,0.0]
COLOR['light_black'] = [5.0,5.0,5.0]
COLOR['white']       = [250.0,250.0,250.0]
COLOR['light_white'] = [255.0,255.0,255.0]
COLOR['grey']        = [100.0,100.0,100.0]
COLOR['light_grey']  = [155.0,155.0,155.0]
COLOR['red']         = [220.0,35.0,35.0]
COLOR['light_red']   = [250.0,150.0,150.0]
COLOR['blue']        = [30.0,30.0,150.0]
COLOR['light_blue']  = [75.0,75.0,225.0]


def calc_derivitives(state, t):
    """
    Uses fourth order Runge-Kutta to integrate
    state: [theta1, omega1, theta2, omega2]
    """
    derivs    = np.zeros_like(state)
    derivs[0] = state[1]
    delta     = state[2] - state[0]
    denom1    = (mass_t * length_1 - mass_2 * length_1 * cos(delta) * cos(delta))
    derivs[1] = (mass_2 * length_1 * state[1]**2 * sin(delta) * cos(delta) +
                 mass_2 * G * sin(state[2]) * cos(delta) +
                 mass_2 * length_2 * state[3] * state[3] * sin(delta) -
                 mass_t * G * sin(state[0])) / denom1
    derivs[2] = state[3]
    denom2    = (length_2/length_1) * denom1
    derivs[3] = (-mass_2 * length_2 * state[3]**2 * sin(delta) * cos(delta) +
                 mass_t * G * sin(state[0]) * cos(delta) -
                 mass_t * length_1 * state[1] * state[1] * sin(delta) -
                 mass_t * G * sin(state[2])) / denom2
    return derivs


def draw_circle(image_array, x, y, radius, color='white', fade=True):
        xp = min(x+radius+1, len(image_array[0,:])-1)
        xm = max(x-radius, 0)
        yp = min(y+radius+1, len(image_array[:,0])-1)
        ym = max(y-radius, 0)
        if fade:
            kernel = np.zeros((2*radius+1, 2*radius+1, 3))
            ymask,xmask = np.ogrid[-radius:radius+1, -radius:radius+1]
            mask = xmask**2 + ymask**2 <= radius**2
            kernel[mask] = COLOR['light_'+color]
            mask = (xmask)**2 + (ymask)**2 <= (radius/1.3)**2
            kernel[mask] = COLOR[color]
        else:
            kernel = np.zeros((2*radius+1, 2*radius+1, 3))
            ymask,xmask = np.ogrid[-radius:radius+1, -radius:radius+1]
            mask = xmask**2 + ymask**2 <= radius**2
            kernel[mask] = COLOR[color]

        image_array[ym:yp,xm:xp,:] = kernel
        return image_array


def draw_line(image_array, x1, y1, x2, y2, color='white', thick=1.0, fade=True):
        ymask,xmask = np.ogrid[0:len(image_array[0,:]), 0:len(image_array[0,:])]
        m = (y2 - y1) / (x2 - x1)
        b = y1 - (m * x1)
        threshold = max(thick, abs(thick * m))
        #log.out.info("y = " + str(m) + " * x + " + str(b) + " THRESH= " + str(threshold))
        mask  = (abs(ymask - (m * xmask) - b) < threshold)
        xbound_mask = (xmask < max(x1,x2))
        ybound_mask = (ymask < max(y1,y2))
        mask = np.logical_and(mask, xbound_mask)
        mask = np.logical_and(mask, ybound_mask)
        xbound_mask = (xmask > min(x1,x2))
        ybound_mask = (ymask > min(y1,y2))
        mask = np.logical_and(mask, xbound_mask)
        mask = np.logical_and(mask, ybound_mask)
        image_array[mask] = COLOR[color]
        return image_array


def coords_to_space(x1,y1,x2,y2,xgrid,ygrid, motion_space=None,
                    size=10, color='red'):
    """
    Converts the pendulum's coordinates into an image.
    """
    # Make and array of size (xres,yres)
    if (len(x1) != len(y1)) or (len(x1) != len(x2)) or (len(x2) != len(y2)):
        log.out.error("ERROR! x and y need same time dimension!")
        return None
    # This is [x,y,t,RGB]
    if (motion_space is None):
        motion_space = np.zeros([len(ygrid),len(xgrid), len(x1), 3],  dtype=float)
    for i in range(len(x1)):
        indexX1 = (np.abs(xgrid-x1[i])).argmin()
        indexY1 = (np.abs(ygrid-y1[i])).argmin()
        motion_space[:,:,i,:] = draw_circle(motion_space[:,:,i,:], indexX1, indexY1,
                                            size, color=color)
        indexX2 = (np.abs(xgrid-x2[i])).argmin()
        indexY2 = (np.abs(ygrid-y2[i])).argmin()
        motion_space[:,:,i,:] = draw_circle(motion_space[:,:,i,:], indexX2, indexY2,
                                            size, color=color)
        motion_space[:,:,i,:] = draw_line(motion_space[:,:,i,:], len(xgrid)/2, len(ygrid)/2,
                                          indexX1, indexY1, thick=1.0)
        motion_space[:,:,i,:] = draw_line(motion_space[:,:,i,:], indexX1, indexY1,
                                          indexX2, indexY2, thick=1.0)
    return motion_space


def integrate_single_pendulum(i, derivs, state, t):
    data = integrate.odeint(derivs, state, t)
    return {'i':i, 'data':data}


def stash_result(result):
    global INTEGRALS
    INTEGRALS[result['i']] = result['data']


def make_frame(t):
    index = int(t/DT)
    #log.out.info(index)
    return IMAGE_ARRAY[:,:,index,:]


def make_a_movie():
    log.out.info("Starting Pendulum integration")
    # create a time array from 0..MAX_TIME sampled at 0.05 second steps
    t = np.arange(0.0, MAX_TIME, DT)
    ensemble_size = 24
#    ensemble_size = 2


    # th1 and th2 are the initial angles (degrees)
    # w10 and w20 are the initial angular velocities (degrees per second)
    initial_state = [{} for _ in range(ensemble_size)]
    for i in range(ensemble_size):
        initial_state[i]['theta_1'] = 165.0 - (i * 0.00001)
#        initial_state[i]['theta_1'] = 165.0 - (i * 1.0)
        initial_state[i]['omega_1'] = 0.0
        initial_state[i]['theta_2'] = -80.0
        initial_state[i]['omega_2'] = 0.0


    # Set the initial state
    state = [None for _ in range(ensemble_size)]
    for i in range(ensemble_size):
        state[i] = np.radians([initial_state[i]['theta_1'], initial_state[i]['omega_1'],
                               initial_state[i]['theta_2'], initial_state[i]['omega_2']])


    # integrate the ODE using scipy.integrate.
    pool = mp.Pool()
    global INTEGRALS
    INTEGRALS = [None for _ in range(ensemble_size)]
    for i in range(ensemble_size):
        pool.apply_async(integrate_single_pendulum,
                         args = (i, calc_derivitives, state[i], t),
                         callback = stash_result)
    pool.close()
    pool.join()


    # Decompose the integrals into x/y coords
    pendulum = [{} for _ in range(ensemble_size)]
    for i in range(ensemble_size):
        pendulum[i]['x1'] =  length_1 * sin(INTEGRALS[i][:,0])
        pendulum[i]['y1'] = -length_1 * cos(INTEGRALS[i][:,0])
        pendulum[i]['x2'] =  length_2 * sin(INTEGRALS[i][:,2]) + pendulum[i]['x1']
        pendulum[i]['y2'] = -length_2 * cos(INTEGRALS[i][:,2]) + pendulum[i]['y1']

    # Make the movie
    xrange = 2.0
    xres   = 600
    xstep  = 2.0 * xrange / (xres-1)
    xgrid  = np.arange(-1.0*xrange, xrange+xstep, xstep)
    yrange = 2.0
    yres   = 600
    ystep  = 2.0 * yrange / (yres-1)
    ygrid  = np.arange(1.0*yrange, -1.0*yrange-ystep, -1.0*ystep)

    global IMAGE_ARRAY
    IMAGE_ARRAY = None
    for i in range(ensemble_size):
        if i % 2 == 0:
            color = 'red'
        else:
            color = 'blue'
        IMAGE_ARRAY = coords_to_space(pendulum[i]['x1'], pendulum[i]['y1'],
                                      pendulum[i]['x2'], pendulum[i]['y2'],
                                      xgrid, ygrid, size=10, color=color,
                                      motion_space=IMAGE_ARRAY)

    thisFPS = 1.0 / DT

    animation  = mpy.VideoClip(make_frame, duration=MAX_TIME) # 2 seconds
    # You can write the result as a gif (veeery slow) or a video:
    #animation.write_gif(make_frame, fps=15)
    animation.write_videofile('pendulum.mp4', fps=thisFPS)

#<@>===========================================================
# Messing around with recursive runge-kutta solver
# This would allow for more performant coupling experiments
def rk4(f):
    return lambda t, y, dt: (
             lambda dy1: (
               lambda dy2: (
                 lambda dy3: (
                   lambda dy4: (dy1 + 2*dy2 + 2*dy3 + dy4)/6
                 )(dt * f(t + dt, y + dy3))
	          )(dt * f(t + dt/2, y + dy2/2))
	        )(dt * f(t + dt/2, y + dy1/2))
	      )(dt * f(t, y))


def rk4_test():
    from math import sqrt
    initial_state = 1.0
    dy = rk4(lambda t, y: t*sqrt(y))
    y  = initial_state
    t = 0.0
    while t <= MAX_TIME+DT:
        print("t=" + str(t) + " y="+ str(y))
        t, y = t + DT, y + dy(t, y, DT)
#<@>===========================================================


## DRIVER
if __name__ == "__main__":

#    rk4_test()

    make_a_movie()





