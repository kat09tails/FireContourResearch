import numpy as np
import os
import sys
from pathlib import Path
import rasterio as rst
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio import shutil as rio_shutil
from rasterio.vrt import WarpedVRT

import rasterio.features
import rasterio.warp
import rasterio.transform
import affine
import matplotlib.pyplot as plt
import cv2 as cv

class CompressImage:
   IND = 0
   ###################################################
   ##       Function: image_locations               ##
   ## Retrieves file paths from the designated      ##
   ## directory, and returns a numpy array of file  ##
   ## names.                                        ##
   ###################################################
   def image_locations(self, path="Original_Images"):
      dir = Path(path)
      print("Current working directory: ", os.getcwd())
      print("Directory exists: ", dir.exists())
      image_names = []
      for file in dir.glob('*.tif'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image_names.append(file_name) 
      image_names = np.asarray(image_names)
      image_names.sort()       
      return image_names

   ###################################################
   ##       Function: get_file_name                 ##
   ## Parses the file name from a path string.      ##
   ###################################################
   def get_file_name(self, image_path):
      index_slash = image_path.rfind('/')
      return image_path[index_slash+1:len(image_path)]

   
   ###################################################
   ##       Function: get_width_height              ##
   ## Gathers the max width and height of an image, ##
   ## and also gathers the minimum left and bottom  ##
   ## coordinate, and maximum right and top         ##
   ## coordinate. This function essentially gathers ##
   ## information for a bounding box for images.    ##
   ###################################################
   def get_width_height(self, path="Original_Images"):
      print('Calculating Max Width and Height Needed')
      minBottom = 9999999
      minLeft = 9999999
      maxTop = 0
      maxRight = 0
      max_width = 0
      max_height = 0
      image_paths = self.image_locations(path)
      for index, image_path in enumerate(image_paths):
         try:
            raster = rst.open(image_path)
            band = raster.read(1)
            x, y = band.shape
            x -= 1
            y -= 1
            left, top = raster.xy(0, 0, offset='ul')
            right, bottom = raster.xy(x, y, offset='lr')

            if index == 0:
               minBottom = bottom
               minLeft = left
               maxTop = top
               maxRight = right

            else:
               if bottom < minBottom:
                  minBottom = bottom
               if left < minLeft:
                  minLeft = left
               if right > maxRight:
                  maxRight = right
               if top > maxTop:
                  maxTop = top
            raster.close()
         except:
            print("Cannot open file: ", image_path)
      minX, minY = raster.index(minLeft, maxTop)
      maxX, maxY = raster.index(maxRight, minBottom)
      width = maxX - minX
      height = maxY - minY
      raster.close()

      self.minLeft = minLeft
      self.maxTop = maxTop
      self.maxRight = maxRight
      self.minBottom = minBottom
      self.max_width = width
      self.max_height = height

      return minLeft, maxTop, maxRight, minBottom, width, height


   ###################################################
   ##       Function: region_of_interest            ##
   ## Removes all of the unneccessary black pixels  ##
   ## around an image, then modifies the meta data  ##
   ## to use the new top left corner.               ##
   ###################################################
   minBottom = 9999999
   minLeft = 9999999
   maxTop = 0
   maxRight = 0
   max_width = 0
   max_height = 0
   index = 0
   def region_of_interest(self, image_path, band_num = 4):
      dst_crs = rst.crs.CRS.from_epsg(4326)
      if not os.path.exists("IntRegImgs"):
         os.makedirs("IntRegImgs")
      name = self.get_file_name(image_path)
      if not os.path.exists("IntRegImgs/" + name):
         try:
            with rst.open(image_path) as src:
               # Write bands
               band = src.read(band_num)
               meta = src.profile
               meta['count'] = 1
               meta['dtype'] ='uint8'
               max_val = np.max(band)
               band = band / max_val
               band = band * 255
               band = band.astype(np.uint8)
               if not os.path.exists("Band4"):
                  os.makedirs("Band4")
               raster = []
               if not os.path.exists("Band4/" + name):
                  raster = rst.open("Band4" + '/' + name, 'w', **meta)
                  raster.write(band, 1)
                  no_black_pix = np.where(band != 0)
                  top = np.amin(no_black_pix[0])
                  left = np.amin(no_black_pix[1])
                  bottom = np.amax(no_black_pix[0])
                  right = np.amax(no_black_pix[1])

                  dst_width = right - left
                  dst_height = bottom - top

                  leftCoord, topCoord = src.xy(top, left)
                  rightCoord, bottomCoord = src.xy(bottom, right)

                  if self.index == 0:
                     self.minBottom = bottomCoord
                     self.minLeft = leftCoord
                     self.maxTop = topCoord
                     self.maxRight = rightCoord
                     self.max_width = dst_width
                     self.max_height = dst_height
                     self.index += 1

                  else:
                     if bottomCoord < self.minBottom:
                        self.minBottom = bottomCoord
                     if leftCoord < self.minLeft:
                        self.minLeft = leftCoord
                     if rightCoord > self.maxRight:
                        self.maxRight = rightCoord
                     if topCoord > self.maxTop:
                        self.maxTop = topCoord
                     if dst_width > self.max_width:
                        self.max_width = dst_width
                     if dst_height > self.max_height:
                        self.max_height = dst_height


                  xres = meta['transform'][0]
                  yres = -meta['transform'][4]
                  dst_transform = affine.Affine(xres, 0.0, leftCoord, 0.0, -yres, topCoord)
                  vrt_options = {
                     'resampling': rst.enums.Resampling.cubic,
                     'crs':dst_crs,
                     'transform':dst_transform,
                     'height':dst_height,
                     'width':dst_width
                  }
                  with WarpedVRT(raster, **vrt_options) as vrt:
                     rio_shutil.copy(vrt, "IntRegImgs/"+name, driver='GTiff')
                     raster.close()
               else:
                  raster = rst.open("Band4/" + name)
                  test_band= raster.read(1)
                  no_black_pix = np.where(band != 0)
                  top = np.amin(no_black_pix[0])
                  left = np.amin(no_black_pix[1])
                  bottom = np.amax(no_black_pix[0])
                  right = np.amax(no_black_pix[1])

                  dst_width = right - left
                  dst_height = bottom - top

                  leftCoord, topCoord = src.xy(top, left, offset='ul')
                  rightCoord, bottomCoord = src.xy(bottom, right, offset='lr')

                  if self.index == 0:
                     self.minBottom = bottomCoord
                     self.minLeft = leftCoord
                     self.maxTop = topCoord
                     self.maxRight = rightCoord
                     self.max_width = dst_width
                     self.max_height = dst_height
                     self.index += 1

                  else:
                     if bottomCoord < self.minBottom:
                        self.minBottom = bottomCoord
                     if leftCoord < self.minLeft:
                        self.minLeft = leftCoord
                     if rightCoord > self.maxRight:
                        self.maxRight = rightCoord
                     if topCoord > self.maxTop:
                        self.maxTop = topCoord
                     if dst_width > self.max_width:
                        self.max_width = dst_width
                     if dst_height > self.max_height:
                        self.max_height = dst_height

                  xres = meta['transform'][0]
                  yres = -meta['transform'][4]
                  dst_transform = affine.Affine(xres, 0.0, leftCoord, 0.0, -yres, topCoord)
                  vrt_options = {
                     'resampling': rst.enums.Resampling.cubic,
                     'crs':dst_crs,
                     'transform':dst_transform,
                     'height':dst_height,
                     'width':dst_width
                  }
                  with WarpedVRT(raster, **vrt_options) as vrt:
                     rio_shutil.copy(vrt, "IntRegImgs/"+name, driver='GTiff')
               raster.close()
         except:
            print("Could not open the file: ", name)
      else:
         raster = rst.open("IntRegImgs/" + name)
         test_band= raster.read(1)
         leftCoord, topCoord = raster.xy(0, 0)
         rightCoord, bottomCoord = raster.xy(test_band.shape[0]-1, test_band.shape[1]-1)

         if self.index == 0:
            self.minBottom = bottomCoord
            self.minLeft = leftCoord
            self.maxTop = topCoord
            self.maxRight = rightCoord
            self.max_width = dst_width
            self.max_height = dst_height
            self.index += 1

         else:
            if bottomCoord < self.minBottom:
               self.minBottom = bottomCoord
            if leftCoord < self.minLeft:
               self.minLeft = leftCoord
            if rightCoord > self.maxRight:
               self.maxRight = rightCoord
            if topCoord > self.maxTop:
               self.maxTop = topCoord
            if dst_width > self.max_width:
               self.max_width = dst_width
            if dst_height > self.max_height:
               self.max_height = dst_height

   ###################################################
   ##       Function: compress_image                ##
   ## Intended to resize an image after             ##
   ## get_width_height is run. If you wish to make  ##
   ## the images smaller, you can modify the        ##
   ## dst_width and dst_height to change the image  ##
   ## size.                                         ##
   ###################################################
   
   def compress_image(self, image_path, save_directory, save=True):
      if not os.path.exists(save_directory):
         os.makedirs(save_directory)
      print("Compressing image ", self.IND)
      self.IND += 1
      meta = ""
      name = self.get_file_name(image_path)
      band = []
      if not os.path.exists(save_directory+"/"+name):
         dst_crs = rst.crs.CRS.from_epsg(4326) # Coordinate system Hu Tzu Shan 1950
         dst_width = self.max_width
         dst_height = self.max_height

         xres = (self.maxRight - self.minLeft) / dst_width
         yres = (self.maxTop - self.minBottom) / dst_height
         dst_transform = affine.Affine(xres, 0.0, self.minLeft, 0.0, -yres, self.maxTop)
         vrt_options = {
            'resampling': rst.enums.Resampling.cubic,
            'crs':dst_crs,
            'transform':dst_transform,
            'height':dst_height,
            'width':dst_width
         }
         if(save):
            raster = rst.open(image_path)
            with WarpedVRT(raster, **vrt_options) as vrt:
               rio_shutil.copy(vrt, save_directory+"/"+name, driver='GTiff')
               raster.close()
      
      return name, band, meta



def main():
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run first. If it is executed after a different script it will not work.")
   ci = CompressImage()
   if(len(sys.argv) < 2):
      print("_________________________________\n")
      print("\tImage Reduction\n")
      print("_________________________________\n\n")
      print("1. Help\n")
      print("press any key (other than 1) to quit.\n\n")
      user_input = input(">>> ") 
      print("")    
      if(user_input == '1'):
         print("To compress images you can use the following command line arguments: ")
         print("compress [directory to compress] [save directory] [band number]\n")
         print("Example:\t python CompressImage.py compress OriginalImages CompressedImages 4\n")

   else:
      if sys.argv[1].lower() == "compress" and len(sys.argv) == 5:
         left = 0
         top = 0
         right = 0
         bottom = 0
         width = 0
         height = 0
         
         print("Compressing Images...")
         imageLocations = ci.image_locations(path=sys.argv[2])
         last_filename = ci.get_file_name(imageLocations[0])
         
         if os.path.exists("imgDim.txt") and os.path.exists("IntRegImgs"):
            dimFile = open("imgDim.txt", "r+")
            ci.minLeft = float(dimFile.readline()[6:-1])
            ci.maxTop = float(dimFile.readline()[5:-1])
            ci.maxRight = float(dimFile.readline()[7:-1])
            ci.minBottom = float(dimFile.readline()[8:-1])
            ci.max_width = int(dimFile.readline()[7:-1])
            ci.max_height = int(dimFile.readline()[8:])
            dimFile.close()
            for image_path in ci.image_locations(path="IntRegImgs"):
               ci.compress_image(image_path, sys.argv[3])

         elif os.path.exists("IntRegImgs") and not os.path.exists("Band4" + last_filename):
            for image_path in imageLocations:
               ci.region_of_interest(image_path, int(sys.argv[4]))
            dimFile = open("imgDim.txt", "a+")
            dimFile.write("left: %f\n" % ci.minLeft)
            dimFile.write("top: %f\n" % ci.maxTop)
            dimFile.write("right: %f\n" % ci.maxRight)
            dimFile.write("bottom: %f\n" % ci.minBottom)
            dimFile.write("width: %d\n" % ci.max_width)
            dimFile.write("height: %d" % ci.max_height)
            dimFile.close()     
            for image_path in ci.image_locations(path="IntRegImgs"):
               ci.compress_image(image_path, sys.argv[3])
         elif os.path.exists("IntRegImgs"):
            ci.get_width_height("IntRegImgs")
            dimFile = open("imgDim.txt", "a+")
            dimFile.write("left: %f\n" % ci.minLeft)
            dimFile.write("top: %f\n" % ci.maxTop)
            dimFile.write("right: %f\n" % ci.maxRight)
            dimFile.write("bottom: %f\n" % ci.minBottom)
            dimFile.write("width: %d\n" % ci.max_width)
            dimFile.write("height: %d" % ci.max_height)
            dimFile.close()   
            for image_path in ci.image_locations(path="IntRegImgs"):
               ci.compress_image(image_path, sys.argv[3])
         else:
            for image_path in ci.image_locations(path=sys.argv[2]):
               ci.region_of_interest(image_path, int(sys.argv[4]))
            dimFile = open("imgDim.txt", "a+")
            dimFile.write("left: %f\n" % ci.minLeft)
            dimFile.write("top: %f\n" % ci.maxTop)
            dimFile.write("right: %f\n" % ci.maxRight)
            dimFile.write("bottom: %f\n" % ci.minBottom)
            dimFile.write("width: %d\n" % ci.max_width)
            dimFile.write("height: %d" % ci.max_height)
            dimFile.close()     
            for image_path in ci.image_locations(path="IntRegImgs"):
               ci.compress_image(image_path, sys.argv[3])

      elif sys.argv[1].lower() == "compress" and len(sys.argv) != 4:
         print("To compress images please enter: compress [directory to compress] [save directory] [band number]\n")
      elif(len(sys.argv) > 2):
         print("To compress images please enter: compress [directory to compress] [save directory] [band number]\n")

if __name__ == "__main__":
   main()
