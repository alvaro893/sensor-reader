"""Module handles various support operations on frames received from the camera such as
applying custom colormaps, applying masks, calculating reference points, equalizing histogram.
It also generates heatmaps, removes background, applies custom colormap. Additionally, it provides
functionality to drop outliers and estimate amount of people from the frame.
"""
from copy import deepcopy
from itertools import compress

import cv2
import numpy as np

from Camera import Camera
from analysis import Images

imagePath = Images.imagePath

# def get_reference_raw(camera_name, frame):
#     """ Extracts region from a frame depending on a camera name and calculates mean value of the region.
#     Used for calibrating the range of human temperatures.
#
#     Args:
#         camera_name (str): name of the camera.
#         frame (numpy.2darray): grayscale frame received from the camera.
#
#     Returns:
#         float: The return value. Mean value of specified region.
#     """
#     reference_raw = None
#     if camera_name == "RESTAURANT2":
#         reference_raw = np.mean(frame[10:20, 146:156])
#     elif camera_name == "RESTAURANT1":
#         reference_raw = np.mean(frame[32:42, 143:153])
#     return reference_raw

# def extract_grayscale(frame, human_mask):
#     """ Extracts all regions identified within the range of human temperatures.
#
#     Args:
#         frame (numpy.2darray): grayscale frame received from the camera.
#         human_mask (numpy.2darray): Bitmap representation of the frame where all people are black and everything else is white.
#
#     Returns:
#         numpy.2darray: The return value. Frame where humans are grayscale and everything else is white.
#     """
#     mask = (255-human_mask)     #Invert mask
#     mask = np.logical_not(mask) #Create boolean mask
#     frame[mask] = 255           #Color everything except human regions in white
#     return frame


def extract_grayscale(heatmap, human_mask):
    """ Extracts all regions identified within the range of human temperatures.

    Args:
        frame (numpy.2darray): grayscale frame received from the camera.
        human_mask (numpy.2darray): Bitmap representation of the frame where all people are black and everything else is white.

    Returns:
        numpy.2darray: The return value. Frame where humans are grayscale and everything else is white.
    """
    mask = (255-human_mask)     #Invert mask
    mask = np.logical_not(mask) #Create boolean mask
    heatmap[mask] = 255           #Color everything except human regions in white
    return heatmap

def drop_outliers(*args):
    '''
    *args:
         Variable length argument list. Used to pass frame list and n_people list

    Returns:
        list: The return value. Initial list with outliers being dropped. or in case of
        multiple arguments passed to the function additionally returns extra list with
        corresponding elements being dropped as well.
    '''

    m = 2
    """
    Defines how clean we need the signal sample to be (false positives),or how many
    signal measurements we can afford to throw away to keep the signal clean (false negatives).
    """ 

    multy_args = False

    people_list = args[0]

    if len(args) > 1:
        multy_args = True
        frame_list = args[1]
        if len(frame_list) == 0:
            return people_list, args[1]
    
    if len(people_list) == 0 or max(people_list) == 0:
        return people_list, frame_list if multy_args else people_list

    #Calculate deviation for every element
    d = np.abs(people_list - np.median(people_list))
    # Calculate median of deviation distribution
    mdev = np.median(d)
    if mdev == 0:
        return people_list, frame_list if multy_args else people_list
    else:
        # Calculate s
        s = d/mdev
        #Create boolean array of non outliers
        non_outliers = [True if x < m else False for x in s]
        #Drop outliers
        people_list = list(compress(people_list, non_outliers))
        return people_list, list(compress(frame_list, non_outliers)) if multy_args else people_list
            

def estimate_people_left(thresh):
    """ Splits frame into top, middle and bottom regions. Depending on how much space does one person
    occupy in each region, estimates amount of people in it.

    Args:
        thresh (numpy.2darray): black and white image where people are black and everything else
        is white.

    Returns:
        int: estimated amount of people in the frame.
    """

    #Define average amount of pixels one person occupies depending on his position in a frame
    TOP_HUMAN = 15
    MID_HUMAN = 20
    BOT_HUMAN = 25

    #Split frame into top, middle and bottom regions
    top = thresh[0:40, :]
    mid = thresh[40:90, :]
    bot = thresh[90:, :]

    #Estimate amount of people in each region
    top_people = np.floor(count_pixels(top) * 1.0 / TOP_HUMAN)
    mid_people = np.floor(count_pixels(mid) * 1.0 / MID_HUMAN)
    bot_people = np.floor(count_pixels(bot) * 1.0 / BOT_HUMAN)

    # print('Top people: ' + str(top_people), 'Middle people: ' + str(mid_people), 'Bottom people: '+ str(bot_people))
    # print('Top pixels: ' + str(count_pixels(top)), 'Middle pixels: ' + str(count_pixels(mid)),
    # 'Bottom pixels: ' + str(count_pixels(bot)))  

    #Calculate total amount of people
    res = int(top_people + bot_people + mid_people)

    return res

def count_pixels(region):
    """ Calculates amount of black pixels in the input region.

    Args:
        region (numpy.2darray): region to count pixels from.

    Returns:
        int: The return value. Amount of black pixels in the input region.
    """
    num_black = (region == 0).sum()
    return num_black 

def estimate_people_right_camera(thresh):
    """ Applies mask to extract top, middle and bottom regions from the frame. Depending on how much
    space does one person occupy in each region, estimates amount of people in it.

    Args:
        thresh (numpy.2darray): black and white image where people are black and everything else
        is white.

    Returns:
        int: The return value. Estimated amount of people in the frame.
    """

    #Make copies of original thresh image
    bot = deepcopy(thresh)
    mid = deepcopy(thresh)
    top = deepcopy(thresh)

    #Define average amount of pixels one person occupies depending on his position in a frame
    TOP_HUMAN = 17
    MID_HUMAN = 23
    BOT_HUMAN = 30

    #Load masks for top, mid and bottom regions
    mask_bot = Images.get(Images.mask_bot)
    mask_bot = np.logical_not(mask_bot)
    mask_mid = Images.get(Images.mask_mid)
    mask_mid = np.logical_not(mask_mid)
    mask_top = Images.get(Images.mask_top)
    mask_top = np.logical_not(mask_top)

    #Apply mask to every region
    top[mask_top] = 255
    mid[mask_mid] = 255
    bot[mask_bot] = 255

    #Estimate amount of people in each region
    top_people = np.floor(count_pixels(top) * 1.0 / TOP_HUMAN)
    mid_people = np.floor(count_pixels(mid) * 1.0 / MID_HUMAN)
    bot_people = np.floor(count_pixels(bot) * 1.0 / BOT_HUMAN)

    # print('Top people: ' + str(top_people), 'Middle people: ' + str(mid_people), 'Bottom people: '+ str(bot_people))
    # print('Top pixels:' + str(count_pixels(top)), 'Mid pixels:' + str(count_pixels(mid)), 'Bottom pixels:' + str(count_pixels(bot))) 

    #Calculate total amount of people in the frame
    res = int(top_people + bot_people + mid_people)

    return res

def applyMask(camera_name, img, **kwargs):
    """ Applies mask to the input image. Depending on keyword arguments leaves cashier area masked
    or unmasked.

    Args:
        camera_name (str): name of the camera.
        img (numpy.2darray): grayscale image to which custom colormap is applied.

    **kwargs:
        cashier (boolean): True if cashier area should be shown, False if it should be masked.

    Returns:
        img (numpy.2darray): The return value. Masked image.
    """

    #Load corresponding masks
    if camera_name == 'RESTAURANT1' and kwargs["cashier"]:
        mask = Images.get(Images.mask_cabins)
    elif camera_name == 'RESTAURANT1' and not kwargs["cashier"]:
        mask = Images.get(Images.mask_right)
    elif camera_name == 'RESTAURANT2' and kwargs["cashier"]==True:
        mask = Images.get(Images.mask_cashier)
    elif camera_name == 'RESTAURANT2' and not kwargs["cashier"]:
        mask = Images.get(Images.mask_main)
    else:
        # General case (no mask)
        mask = Images.get(Images.white)

    #Create boolean mask and apply to the image   
    mask = np.logical_not(mask)
    img[mask] = 255
    
    return img


def estimate_general_thermal_camera(thresh):
    """ Over simplication of the right and left camera algorithms

        Args:
            thresh (numpy.2darray): black and white image where people are black and everything else
            is white.

        Returns:
            int: The return value. Estimated amount of people in the frame.
        """

    HUMAN = 5000 # Define average amount of pixels one person occupies in a frame

    people = np.floor(count_pixels(thresh) * 1.0 / HUMAN)

    return int(people)


def process_image(img, camera_name):
    """ Depending on camera name sends frame to get an estimation of people in the input frame.

    Args:
        img (numpy.2darray): input image.
        camera_name (str): name of the camera.

    Returns:
        n_people (int): The return value. Amount of people estimated from the frame.
    """
    # thresh_full = applyMask(camera_name, img.copy(), cashier=True)
    thresh_count = applyMask(camera_name, img, cashier=False)
    if camera_name == "RESTAURANT2":
        n_people = estimate_people_left(thresh_count)
    elif camera_name == "RESTAURANT1":
        n_people = estimate_people_right_camera(thresh_count)
    else:
        n_people = estimate_general_thermal_camera(thresh_count)
    return n_people

def hist_equalization(image):
    """ Applies clahe histogram equalization to the input image.

    Args:
        image (numpy.2darray): input image. 

    Returns:
        clahe (numpy.2darray): The return value. Equalized image.
    """
    #Create a CLAHE object (arguments are optional).
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(4 , 4))
    clahe = clahe.apply(image)
    return clahe

def applyCustomColorMap(src_img, **kwargs):
    """ Applies chosen custom color map to the input image.

    Args:
        im_gray (numpy.2darray): grayscale image. 

    **kwargs:
        cmap (str): Name of the colormap to apply. Default value is Inferno.
        reverse (boolean): Flip colorscale when True, leave the same if False. Default value is False.

    Returns:
        img_color (numpy.2darray): The return value. Pseudo-clored image.
    """
    #Check if color map is explicitly specified, otherwise use inferno as default
    if 'cmap' not in kwargs.keys():
        kwargs["cmap"] = Images.inferno_cropped

    if 'reverse' not in kwargs.keys():
        kwargs["reverse"] = False

    #Load colormap image
    img = cv2.cvtColor(src_img, cv2.COLOR_GRAY2BGR);

    #Load image to create a color map from
    lut = Images.get(kwargs["cmap"])
    lut = np.asarray(lut, dtype=np.uint8)
    #Reverse if needed
    if kwargs["reverse"]:
        lut = np.flip(lut, 0)

    #Create LUT object and apply to input frame
    if "dst_img" in kwargs.keys():
        cv2.LUT(img, lut, dst=kwargs['dst_img'])
    else:
        img_color = cv2.LUT(img, lut)
        return img_color

def make_heatmap_grayscale(frame_list): 
    """ Makes average representation of a heatmap for the last period. Applies custom colormap,
    histogram equalization, removes background and saves file.

    Args:
        frame_list (list): list of FLAT(1d-array) frames collected during last period.

    Returns:
        heatmap_grayscale (numpy.2darray): The return value. Grayscale image of regions with
        human temperatures.
    """

    heatmap_grayscale = np.mean(frame_list, 0).astype(np.uint8).reshape(Camera.IMAGE_HEIGHT,Camera.IMAGE_WIDTH)
    heatmap_grayscale = hist_equalization(heatmap_grayscale)
    colored_heatmap = applyCustomColorMap(heatmap_grayscale, cmap=Images.inferno_cropped, reverse=True)
    #colored_heatmap = cv2.resize(colored_heatmap, None, fx=4, fy=4, interpolation=cv2.INTER_LINEAR)
    colored_heatmap = remove_bg(colored_heatmap, cmap="inferno_cropped", reverse=True)
    #cv2.imwrite(imagePath + "colored_heatmap.png", colored_heatmap)
    Images.put("colored_heatmap.png", colored_heatmap)
    return heatmap_grayscale

def remove_bg(colored_heatmap, **kwargs):
    """ Makes average representation of a heatmap for the last period. Applies custom colormap,
    removes background and saves file.

    Args:
        colored_heatmap (numpy.2darray): colored heatmap.

    **kwargs:
        cmap (str): name of a colormap.
        reverse (boolean): True if colorscale should be flipped, False otherwise. Default value is False. 

    Returns:
        heatmap_grayscale (numpy.2darray): The return value. Grayscale image of regions with
        human temperatures.
    """

    #Specifies what color to remove depending on colormap name
    cmap_to_bgr_false = {"inferno_cropped": [190,251,253],
                    "viridis": [84,13,69],
                    "plasma": [28,253,238],
                    "king_yna": [46,187,254]}

    cmap_to_bgr_true = {"inferno_cropped": [75,19,32],
                    "viridis": [36,230,253],
                    "plasma": [114,1,11],
                    "king_yna": [108,41,26]}

    cmap = kwargs["cmap"]

    #Extract background region
    if kwargs["reverse"]:
        mask = cv2.inRange(colored_heatmap, np.asarray(cmap_to_bgr_true[cmap]), np.asarray(cmap_to_bgr_true[cmap]))
    else:
        mask = cv2.inRange(colored_heatmap, np.asarray(cmap_to_bgr_false[cmap]), np.asarray(cmap_to_bgr_false[cmap]))
    
    #Create mask out of background region
    mask = cv2.bitwise_not(mask)
    #Create alpha channel
    alpha = mask.copy()
    #Apply mask
    mask = np.logical_not(mask)
    colored_heatmap[mask] = 255
    #Split channels
    b, g, r = cv2.split(colored_heatmap)
    #Merge channels back
    rgba = [b,g,r, alpha]
    res = cv2.merge(rgba,4)
    return res