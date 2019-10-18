#python3.7.0
#Project/dropk#/well/profileID/name_ef.jpg
#run this command above the echo project directory

import glob
import sys
import pickle as pkl
import matplotlib.pyplot as plt
import numpy as np
from skimage.transform import hough_circle, hough_circle_peaks
from skimage.feature import canny
from skimage.draw import circle_perimeter
from skimage.util import img_as_ubyte
from skimage.util import pad
from skimage import io
import os
from classes_only import Well_well_well as well
from classes_only import Plate

from datetime import datetime, date, time
import json

#Function Definitions
#Params
    #r1 lower radius bound
    #r2 upper radius bound
    #search step size between radii
    #edge: a binary image which is the output of canny edge detection
    #peak_num the # of circles searched for in hough space

#Output:
    #accums 
    #cx : circle center x
    #cy : circle center y
    #radii circle radii
def circular_hough_transform(r1,r2,step,edge, peak_num):  # do we need to do this? difference in a radium in circle matters to the conversion rate
    # be able to distinguish up to one pixel of the circle 

    hough_radii = np.arange(r1,r2,step)
    hough_res = hough_circle(edge,hough_radii)
    accums, cx, cy, radii = hough_circle_peaks(hough_res,hough_radii,total_num_peaks=peak_num)
    return accums, cx, cy, radii

def single_radii_circular_hough_transform(r1,edge):
    hough_res = hough_circle(edge,r1)
    accums, cx, cy, radii = hough_circle_peaks(hough_res,r1,total_num_peaks=1)
    return accums, cx, cy, radii

#Params
    #This functions draws a circle of radius r centered on x,y on an image. It draws the center of the circle
    #image: input greyscale numpy 2darray
    #cx: int center x
    #cy: int center y
    #color: single 8-bit channel int. i.e 0-255
def draw_circles_on_image(image,cx,cy,radii,colour,dotsize):
    for center_y, center_x, radius in zip(cy,cx,radii):
        circy, circx = circle_perimeter(center_y,center_x,radius)
        image[circy,circx] = colour
        image[cy[0]-dotsize:cy[0]+dotsize,cx[0]-dotsize:cx[0]+dotsize] = colour

def draw_circles_on_image_center(image,cx,cy,radii,colour,dotsize):
    for center_y, center_x, radius in zip(cy,cx,radii):
        circy, circx = circle_perimeter(center_y,center_x,radius)
        image[circy,circx] = colour
        image[cy[0]-dotsize:cy[0]+dotsize,cx[0]-dotsize:cx[0]+dotsize] = colour

def save_canny_save_fit(path,sig,low,high): #sig=3,low = 0, high = 30
    zstack = io.imread(path)  
    image = img_as_ubyte(zstack[:,:,0]) # finds the top x-y pixels in the z-stack
    edges = canny(image,sigma=sig,low_threshold=low,high_threshold=high)   # edge detection
    accum_d, cx_d, cy_d, radii_d = circular_hough_transform(135,145,2,edges,1) #edge detection on drop, params: r1,r2,stepsize,image,peaknum. Key params to change are r1&r2 for start & end radius
    ### room temp well
    accum_w, cx_w, cy_w, radii_w = circular_hough_transform(479,495,1,edges,1) #edge detection on well. Units for both are in pixels
    ### This works well for echo 4C plate type for rockmaker
    accum_w, cx_w, cy_w, radii_w = circular_hough_transform(459,475,1,edges,1) #edge detection on well. Units for both are in pixels

    return cx_d,cy_d,radii_d, cx_w, cy_w, radii_w

    
def main():

    t0=time.time()  ### save time to know how long this script takes (this one takes longer than step 2)

    if len(sys.argv) != 2:
        print('Usage: python pregui_analysis.py [plate_dir]')
        print('Aborting script')
        sys.exit()
    
    current_directory = os.getcwd()
    plate_dir = sys.argv[1]
    plate_temperature = sys.argv[2]
    

    image_list=glob.glob("{}/overlayed/*".format(plate_dir))
    image_list.sort(key=lambda x: (int(x.split('well_')[1].split('_overlay')[0].split("_subwell")[0])))
    
    dict_image_path_subwells = \
    {
        a.split('well_')[1].split('_overlay')[0].replace("subwell",""):a for a in image_list
    }

    print(current_directory + '/' + plate_dir.strip('/') + '_offsets.csv') ### eventually do this in the main gui
    
    wellnames = Plate.well_names
    plate_to_pickle = Plate(Plate.plate_dict) #empty dictionary

    a = {}
    
    try:
        with open(current_directory+"/"+plate_dir+"/plateid.txt", 'r') as plate_id_file:
            plate_id = int(plate_id_file.read().rstrip())
            a[plate_id] = {}
    except FileNotFoundError:
        print("File Error: plateid.txt not found. JSON will not have plate_id key")

    plateKeys = ["date_time"]
    wellKeys = ["image_path","well_id","subwell","well_radius","well_x","well_y","drop_radius","drop_x","drop_y"]

    ### Create json output dictionary
    a[plate_id] = {key:0 for key in plateKeys}
    a[plate_id]["date_time"] = "Generated on: "+datetime.now().isoformat(" ")


    ### Try to get the plate ID saved from before


    for im_idx, im_path in sorted(dict_image_path_subwells.items()):
        print("processing: ", im_idx, im_path)
        if im_path:
            cx_d,cy_d,radii_d, cx_w, cy_w, radii_w = save_canny_save_fit(im_path,3,0,50,plate_temperature) ### calling this function also saves

        # cx_d,cy_d,radii_d, cx_w, cy_w, radii_w = [0,0,0,0,0,0] time saving code (will output zeros)
        ### radii radius of the drop circle 
        ### everything _w is for the well
        ### everything _d is for the drop
        ### plan on keeping the drop information
        # offset_x = cx_d - cx_w
        # offset_y = cy_w - cy_d
        well,subwell = im_idx.split("_")

        str_well_id = wellnames[int(well)-1]

        # print(cx_w,cy_w,radii_w,cx_d,cy_d,radii_d,cx_w,cy_w,radii_d,name,im_path,0,0,0)

        str_currentWell = "{0}_{1}".format(str_well_id, subwell)
        print(str_currentWell)
        a[plate_id][str_currentWell] = {key:0 for key in wellKeys}
        a[plate_id][str_currentWell]["image_path"] = im_path
        a[plate_id][str_currentWell]["well_id"] = str_well_id
        a[plate_id][str_currentWell]["subwell"] = subwell ### Don't know how to get this information
        a[plate_id][str_currentWell]["well_radius"] = int(radii_w)
        a[plate_id][str_currentWell]["well_x"] = int(cx_w)
        a[plate_id][str_currentWell]["well_y"] = int(cy_w)
        a[plate_id][str_currentWell]["drop_radius"] = int(radii_d)
        a[plate_id][str_currentWell]["drop_x"] = int(cx_d)
        a[plate_id][str_currentWell]["drop_y"] = int(cy_d)

    with open(current_directory + '/' + plate_dir + '/' +plate_dir.strip('/') + '.json', 'w') as fp:
        json.dump(a, fp)
    print('wrote to json')

    print("time to run: %s"%(time.time()-t0))


if __name__ == "__main__":
    main()
    