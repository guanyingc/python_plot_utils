""" A python script to crop image patches, and draw boxes for the patches in the original image
Input: a single image or a directory that contains images, locations (top, left, bottom, right) of boxes
"""

import argparse
import os
import glob
import cv2
import numpy as np


def parse_arguments():
    parser = argparse.ArgumentParser()

    """ Specify the input """
    parser.add_argument('--in_dir', default='', help='process all images in the directory')
    parser.add_argument('--in_img', default='', help='a single input image')
    parser.add_argument('--key', default='*', help='select images with the key in the file name')
    parser.add_argument('--img_type', type=str, nargs='+', default=['.jpg', '.png', '.tif'],
            help='specify color (e.g., k|r|b|g|y) for each box, e.g., --colors r b') # list

    """ Specify the box location (top, left, bottom, right) """
    parser.add_argument('-t', '--t', default=-1, type=int, help='top of the box')
    parser.add_argument('-l', '--l', default=-1, type=int, help='left of the box')
    parser.add_argument('-b', '--b', default=-1, type=int, help='bottom of the box')
    parser.add_argument('-r', '--r', default=-1, type=int, help='right of the box')

    parser.add_argument('--height', default=-1, type=int,
            help='height of the box, if specified, ignore --b, compute bottom with t+height')
    parser.add_argument('--width', default=-1, type=int,
            help='width of the box, if spcified, ignore --r, compute right with l+width')

    # specify boxes with list of list
    parser.add_argument('--boxes', type=int, nargs='+', action='append', default=[],
            help='list of list, pass multiple boxes. e.g., --boxes t1 l1 b1 r1 --boxes t2 l2 b2 r2')

    """ Specify box colors """
    parser.add_argument('--colors', type=str, nargs='+', default=[],
            help='specify color (e.g., r|b|g|k) for each box, e.g., --colors r b. \
            if no color is passed, the boxes will not be highlighted by colors')
    parser.add_argument('--thick', default=2, type=int, help='thickness of bbox in px')

    """ Specify arrow locations and colors """
    parser.add_argument('--arrows', type=int, nargs='+', action='append', default=[],
            help= 'list of list, start and end points of the arrow, e.g., --arrows x1 y1 x2 y2')
    parser.add_argument('--arrow_thick', default=2, type=int) # thickness in px
    parser.add_argument('--arrow_color', type=str, nargs='+', default=[], help='g,r,b,k')

    """ Simple image processing, disable by default e.g., color enhancement, 
        useful for increasing the contrast of the image, and overlap cropped images
    """
    parser.add_argument('--keep_alpha', default=False, action='store_true', 
            help='keep alpha channel for 4-channel png') 
    parser.add_argument('--do_gamma', default=False, action='store_true',
            help='apply gamma curve on the saved image')
    parser.add_argument('--gamma', default=2.2, type=float)
    parser.add_argument('--do_iscale', default=False, action='store_true', 
            help='scale the image by a factor of --iscale') 
    parser.add_argument('--iscale', default=2.57, type=float)
    parser.add_argument('--overlap', default=False, action='store_true') # overlap cropped images

    """ Save directory and name """
    parser.add_argument('--save_ext', default='.png')
    parser.add_argument('--save_dir', default='ROI')
    parser.add_argument('--rename', default=0, type=int, 
            help='ignore the original image name, 1 for True, 0 for False')
    args = parser.parse_args()
    return args


class ImageCropper(object):
    """ A class takes image path/directory as input, 
        crop boxes and highlight boxes and arrows in the images
    """

    def __init__(self, cfgs):
        self.cfgs = cfgs
        """ print configurations """
        for k, v in cfgs.items():
            print('\t%s: %s' % (k, v))
        
        self.check_cfgs(cfgs)

        """ Get image names """
        self.img_names = self.load_image_list()

    def check_cfgs(self, cfgs):
        assert (args.in_dir != '' or args.in_img != ''), "Aleast one of the --in_dir or --in_img should be set"

        """ Check boxes """
        if len(cfgs['boxes']) == 0:
            """ Use t, l, b, r to define a box"""
            if cfgs['height'] > 0:
                cfgs['b'] = cfgs['t'] + cfgs['height']
            if cfgs['width'] > 0:
                cfgs['r'] = cfgs['l'] + cfgs['width']

            if cfgs['t'] >=0 and cfgs['l'] >= 0 and cfgs['b'] >= 0  and cfgs['r'] >= 0:
                cfgs['boxes'] = [[cfgs['t'], cfgs['l'], cfgs['b'], cfgs['r']]]

        assert len(cfgs['colors']) == 0 or (len(cfgs['colors']) == len(cfgs['boxes'])), \
                'The number of colors should either be 0 or equals to the boxes'

        print('Found %d boxes' % len(cfgs['boxes']))

        """ Check arrows """
        assert len(cfgs['arrows']) == len(cfgs['arrow_color']), \
                'The number of arrow colors should equals to the boxes'

    def load_image_list(self):
        """ Load a single image or a batch of images in a directory """
        cfgs = self.cfgs

        if cfgs['in_dir'] != '':
            img_names = glob.glob(os.path.join(cfgs['in_dir'], cfgs['key']))
            print('Input dir: %s' % cfgs['in_dir'])
        else:
            img_names = [cfgs['in_img']]
            print('Input image: %s' % cfgs['in_img'])

        img_names = self.filter_files(img_names)
        print('Found %d images' % len(img_names))
        return img_names

    def filter_files(self, file_names):
        """ filter out directory and files that are not ended with jpg/png/tif """
        img_names = []
        for f in file_names:
            if os.path.isdir(f) or f[-4:] not in self.cfgs['img_type']:
                continue
            img_names.append(f)
        return img_names

    def crop_batch_imgs(self):
        cfgs = self.cfgs

        if cfgs['overlap']:
            """for overlapping the cropped patches, 
               each box has a list to cache the patches""" 
            cropped_caches = [[] * len(cfgs['boxes'])]

        for i_img, img_name in enumerate(self.img_names):
            
            """ Load image """
            img = self.read_img(img_name)
            img = self.process_img(img, cfgs) # fix channel number, enhance image if required
            h, w, c = img.shape


            """ Draw arrows """
            if not cfgs['arrows'] is None:
                img = self.draw_arrows(img, cfgs)
            
            """ Crop boxes """
            boxes = cfgs['boxes']
            for i_b, (t, l, b, r) in enumerate(boxes):
                self.check_boxsize(t, l, b, r, h, w)

                c_h, c_w = b - t, r - l
                print('[Image %d/%d] [Boxes %d/%d] %s: %d X %d, crop: %d X %d' % (
                    i_img+1, len(self.img_names), i_b+1, len(boxes), img_name, h, w, c_h, c_w))
            
                """ Highlight box if colors is set"""
                if len(cfgs['colors']) > 0:
                    color = cfgs['colors'][i_b]
                    color_3channel = self.get_color_code(color)
                    img = cv2.rectangle(img, (l, t), (r-1, b-1), color=color_3channel, thickness=cfgs['thick'])
                
                """ Crop and save patches"""
                cropped_img = img[t:b, l:r]

                save_dir, save_name = self.get_save_dir_save_name(i_img, i_b, img_name, add_box_id=len(boxes)>1)
                self.save_img(os.path.join(save_dir, save_name), cropped_img)
                
                """ Cache the patches for overlapping """
                if cfgs['overlap']:
                    cropped_caches[i_b].append(cropped_img)

            """ Save the arrows/boxes highlighted input images """ 
            if len(cfgs['arrows']) > 0 or (len(cfgs['boxes']) > 0 and len(cfgs['colors']) > 0):
                drawed_img_name = os.path.basename(img_name)[:-4] + '_draw' + cfgs['save_ext']
                self.save_img(os.path.join(save_dir, drawed_img_name), img)
        
        """ Save overlapped patches images if required """
        if cfgs['overlap']:
            for i in range(len(cropped_caches)):
                overlapped_img = self.blend_images(cropped_caches[i])
                save_name = '%02d_overlapped_img' % (i) + cfgs['save_ext']
                self.save_img(os.path.join(save_dir, save_name), overlapped_img)

    def draw_arrows(self, img, cfgs):
        arrow_coords = cfgs['arrows']

        for i, arrow in enumerate(arrow_coords):
            start_point = tuple(arrow[0:2])
            end_point = tuple(arrow[2:4])

            self.check_arrowsize(start_point, end_point, img.shape[0], img.shape[1])

            color = self.get_color_code(cfgs['arrow_color'][i])
            img = cv2.arrowedLine(img, start_point, end_point, color, 
                    thickness=cfgs['arrow_thick'], line_type=8, tipLength=0.3)
        return img

    def get_color_code(self, color):
        """ Input color in k, r, g, b. Can be updated to support more colors"""
        color_map = {'None': (0, 0, 0), 
                     'k': (0,0,0), 'r': (0,0,1), 
                     'g': (0,1,0), 'b': (1,0,0)} # BGR
        return color_map[color]

    def check_boxsize(self, t, l, b, r, h, w):
        if t < 0 or l < 0 or b >= h or r >= w:
            raise Exception('Crop corners out of the image size')

    def check_arrowsize(self, start, end, h, w):
        assert (0 <= start[0] < w) and (0 <= start[1] < h), 'Start point of the arrow is invalid'
        assert (0 <= end[0] < w) and (0 <= end[1] < h), 'End point of the arrow is invalid'

    def read_img(self, img_path):
        img = cv2.imread(img_path, -1)
        if img.dtype == np.uint8:
            img = img.astype(np.float32) / 255.0
        elif img.dtype == np.uint16:
            img = img.astype(np.float32) / 65535.0
        else:
            raise Exception('Unknown file type: %s' % img.dtype)
        return img

    def save_img(self, save_name, image):
        save_ext = save_name[-3:]
        # print('\tSaving %s' % os.path.join(save_name))

        if save_ext in ['jpg', 'png']:
            cv2.imwrite(save_name, (image * 255).astype(np.uint8))
        elif save_ext in ['tif']:
            cv2.imwrite(save_name, (image * 65535).astype(np.uint16))
        else:
            raise Exception('Unknown save_name: %s', save_ext)

    def process_img(self, img, cfgs):

        """ Check the channel number of the images """
        if img.ndim == 2:
            h, w = img.shape
            img = img.reshape(h, w, 1)
        elif img.ndim == 3:
            h, w, c = img.shape
            if not cfgs['keep_alpha'] and c == 4:
                print('Removing alpha channel')
                img = img[:, :, :3]

        """ Enhance the images """
        if cfgs['do_iscale']:
            img = (img * cfgs['iscale']).clip(0, 1)
        if cfgs['do_gamma']:
            img = np.power(img.clip(0, 1), 1/cfgs['gamma'])
        return img

    def blend_images(self, imgs):
        mean_img = np.stack(imgs, 3).mean(3)
        return mean_img

    def get_save_dir_save_name(self, idx, i_box, img_name, add_box_id=False):
        save_dir = os.path.join(os.path.dirname(img_name), self.cfgs['save_dir'])
        self.make_dir(save_dir)

        if self.cfgs['rename']: # ignore the original image name
            if add_box_id:
                save_name = '%02d_%02d' % (idx, i_box)
            else:
                save_name = '%02d' % (idx)
        else:
            if add_box_id:
                save_name = os.path.basename(img_name)[:-4] + '_%02d' % i_box
            else:
                save_name = os.path.basename(img_name)[:-4]

        save_name = save_name + '_' + self.get_save_suffix()
        return save_dir, save_name

    def make_dir(self, dirname):
        if not os.path.exists(dirname):
            os.makedirs(dirname)

    def get_save_suffix(self):
        """ Set suffix for the saved image name """
        cfgs = self.cfgs

        save_suffix = cfgs['save_dir']
        if cfgs['do_gamma']:
            save_suffix += '_gamma'

        if cfgs['do_iscale']:
            save_suffix += '_iscale'

        save_suffix += cfgs['save_ext']
        return save_suffix


def main(args):
    cfgs = vars(args)
    image_cropper = ImageCropper(cfgs)
    image_cropper.crop_batch_imgs()


if __name__ == '__main__':
    args = parse_arguments()
    main(args)
