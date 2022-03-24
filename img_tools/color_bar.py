""" A small script for generating colorbar in both horizontal and vertical shapes"""
import argparse
import os
import numpy as np
from imageio import imsave
from matplotlib import cm


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--horizontal', default=False, action='store_true')
    parser.add_argument('--h', default=255, type=int, help='height of the color bar')
    parser.add_argument('--w', default=20,  type=int, help='width of the color bar')
    parser.add_argument('--colormap', default='jet', help='jet|viridis') #
    parser.add_argument('--save_dir', default='results/', help='save_dir')
    parser.add_argument('--format', default='png', help='jpg|png|pdf')
    args = parser.parse_args()
    return args

def main(args):
    bar = np.linspace(0, 1, args.h).reshape(-1, 1)  # A single vertical line [H, 1]
    bar = bar.repeat(args.w, 1)  # A 2D bar of shape [H, W]

    """ 
    More types of colormap can be found in 
    https://matplotlib.org/3.5.1/tutorials/colors/colormaps.html
    """ 
    if args.colormap == 'jet':
        colorbar = cm.jet(bar)[:, :, :3]
    elif args.colormap == 'viridis':
        colorbar = cm.viridis(bar)[:, :, :3]
    else:
        raise Exception('Undefined colormap %s' % args.colormap)
    
    if not os.path.exists(args.save_dir):
        os.makedirs(args.save_dir)
    save_name = os.path.join(args.save_dir, 'color_bar_%s' % args.colormap)

    if args.horizontal:
        """ By default the created colormap is vertical, transpose it to horizontal"""
        colorbar = colorbar.transpose([1, 0, 2])
        save_name += '_horz'
    
    imsave(save_name + '.' + args.format, (colorbar * 255).astype(np.uint8))


if __name__ == '__main__':
    args = parse_arguments()
    main(args)
