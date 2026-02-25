import matplotlib.pyplot as plt
import numpy as np

def six_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(10, 15))

    fwidth = 0.5
    fheight = 1/3
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03

    offset3 = 0.06
    shift34 = 0.03

    ax1 = fig.add_axes((xpad+left_margin, 2*fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, 2*fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))

    ax3 = fig.add_axes((xpad+left_margin, fheight + ypad + offset3 + shift34, fwidth - 2*xpad, fheight - 2*ypad - offset3))
    ax4 = fig.add_axes((fwidth + xpad+left_margin/2, fheight + ypad + shift34, fwidth - 2*xpad, fheight - 2*ypad))

    ax5 = fig.add_axes((xpad+left_margin, ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax6 = fig.add_axes((fwidth + xpad+left_margin/2, ypad, fwidth - 2*xpad, fheight - 2*ypad))

    axs = np.array([[ax1, ax2], [ax3, ax4], [ax5, ax6]])
    return fig, axs

def four_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(10, 10))

    fwidth = 0.5
    fheight = 0.5
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03

    offset3 = 0.06
    shift34 = 0.03


    ax1 = fig.add_axes((xpad+left_margin, fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, fheight + ypad, fwidth - 2*xpad, fheight - 2*ypad))

    ax3 = fig.add_axes((1.5*xpad+left_margin, ypad + shift34, fwidth - 2.5*xpad, fheight - 2*ypad))
    ax4 = fig.add_axes((fwidth + xpad+left_margin/2, ypad + shift34, fwidth - 2*xpad, fheight - 2*ypad - offset3/2))

    axs = np.array([[ax1, ax2], [ax3, ax4]])
    return fig, axs

def single_axes_setup():
    fig = plt.figure(figsize=(6.5, 6.5))
    ax = fig.add_axes((0.15, 0.1, 0.8, 0.8))
    return fig, ax

def three_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(15, 5))

    fwidth = 1/3
    fheight = 1
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03

    offset3 = 0.06
    shift34 = 0.03


    ax1 = fig.add_axes((xpad+left_margin, ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, ypad, fwidth - 2*xpad, fheight - 2*ypad))
    ax3 = fig.add_axes((fwidth*2 + xpad+left_margin/2, ypad, fwidth - 2*xpad, fheight - 2*ypad))

    axs = np.array([ax1, ax2, ax3])
    return fig, axs

def two_axes_setup():
    # Figure setup
    fig = plt.figure(figsize=(12, 6))

    fwidth = 1/2
    fheight = 1
    fpad = 0.1
    xpad = fpad * fwidth
    ypad = fpad * fheight
    left_margin = 0.03
    bottom_margin = -0.0295


    ax1 = fig.add_axes((xpad+left_margin, ypad+bottom_margin, fwidth - 2*xpad, fheight - 2*ypad))
    ax2 = fig.add_axes((fwidth + xpad+left_margin/2, ypad+bottom_margin, fwidth - 2*xpad, fheight - 2*ypad))

    axs = np.array([ax1, ax2])
    return fig, axs

def get_axes(n):
    if n == 6:
        fig, axs = six_axes_setup()
    elif n == 4:
        fig, axs = four_axes_setup()
    elif n == 3:
        fig, axs = three_axes_setup()
    elif n == 2:
        fig, axs =  two_axes_setup()
    else:
        fig, ax = single_axes_setup()
        axs = [ax]
    axs = np.array(axs)
    return fig, axs
