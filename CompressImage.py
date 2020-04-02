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

   ###################################################
   ##       Function: image_locations               ##
   ## Retrieves file names from the designated      ##
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

      
   def get_file_name(self, image_path):
      index_slash = image_path.rfind('/')
      return image_path[index_slash+1:len(image_path)]

   # # Pre-processing to get the width and height of the bounding box of the first image.
   # def get_width_height(self, path="Original_Images", band_num = 4):
   #    max_width = 0
   #    max_height = 0
   #    num_image = 0
   #    iteration = 0
   #    latitude = 0
   #    longitude = 0
   #    image_path = self.image_locations(path)[0]
   #    raster = rst.open(image_path)
   #    band = raster.read(band_num)
   #    if(band.shape[0] > 7000 or band.shape[1] > 7000):
   #       max_value = np.max(band)
   #       band = band.astype(np.float64)/max_value #normalize
   #       band = 255 * band
   #       band = band.astype(np.uint8)
   #       ret,thresh = cv.threshold(band,200,255,cv.THRESH_BINARY_INV)
   #       kernel = np.ones((1,1), np.uint8) 
   #       dilation = cv.dilate(thresh, kernel, iterations=1) 
   #       contours, hierarchy = cv.findContours(dilation, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
   #       ws = []
   #       hs = []
   #       xs = []
   #       ys = []
   #       for contour in contours[1:]:
   #          x, y, w, h = cv.boundingRect(contour)

   #          ws.append(w)
   #          hs.append(h)
   #          xs.append(x)
   #          ys.append(y)
   #       ws = np.asarray(ws)
   #       hs = np.asarray(hs)
   #       xs = np.asarray(xs)
   #       ys = np.asarray(ys)

   #       x = np.min(xs) - 300
   #       y = np.min(ys) - 1000
   #       w = np.max(xs) - np.min(xs) + ws[np.argmax(xs)] + 1000 # hundreds give a little more room in case of cutoffs
   #       h = np.max(ys) - np.min(ys) + hs[np.argmax(xs)] + 900
   #       if w > max_width:
   #          max_width = w
   #       if h > max_height:
   #          max_height = h
   #       raster.close()
   #       num_image += 1
   #       iteration += 1
   #       longitude, latitude = raster.xy(x, y)
   #    else:
   #       longitude, latitude = raster.xy(0, 0) # finds the longitude and latitude of the x,y pixel
   #       max_width = band.shape[0]
   #       max_height = band.shape[1]
   #       iteration += 1
   #       raster.close()
   #    return longitude, latitude, max_width, max_height
      # Pre-processing to get the width and height of the bounding box of the first image.
   def get_width_height(self, path="Original_Images", band_num = 4):
      print('Calculating Max Width and Height Needed')
      minBottom = 9999999
      minLeft = 9999999
      maxTop = 0
      maxBottom = 0
      max_width = 0
      max_height = 0
      image_paths = self.image_locations(path)
      image_paths.sort()
      for index, image_path in enumerate(image_paths):
         print(index)
         try:
            raster = rst.open(image_path)
            band = raster.read(band_num)
            meta = raster.profile
            # print(meta)
            print("Affine Transformation: ", meta['transform'])
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
            # minX, minY = raster.index(minLeft, maxTop)
            # maxX, maxY = raster.index(maxRight, minBottom)
            # print("min latitude: ", minLat)
            # print("min longitude: ", minLong)
            # print("max latitude: ", maxLat)
            # print("max longitude: ", maxLong)
            # print("max X: ", maxX)
            # print("max Y: ", maxY)
            # print("min X: ", minX)
            # print("min Y: ", minY)
            # width = maxX - minX
            # height = maxY - minY
            # print("width: ", width)
            # print("height: ", height)
            # print("Meta: ", meta)
            raster.close()
         except:
            print("Cannot open file: ", image_path)
      # first_path = image_paths[0]
      # raster = rst.open(first_path)
      # band = raster.read(band_num)
      minX, minY = raster.index(minLeft, maxTop)
      maxX, maxY = raster.index(maxRight, minBottom)
      width = maxX - minX
      height = maxY - minY
      raster.close()

      return minLeft, maxTop, maxRight, minBottom, width, height


   # # Reduce image size by the bounding box around interesting regions
   # def compress_image(self, image_path, save_directory, longitude, latitude, max_width, max_height, band_num=4, save=True):

   #    meta = ""
   #    name = ""
   #    band = []
   #    if(save):
   #       if not os.path.exists(save_directory):
   #          os.makedirs(save_directory)
   #       name = self.get_file_name(image_path)
   #       if not os.path.exists(save_directory + "/" + name):

   #          raster = rst.open(image_path)

   #          band = raster.read(band_num)
   #          max_value = np.max(band)
   #          band = band.astype(np.float64)/max_value #normalize
   #          band = 255 * band
   #          band = band.astype(np.uint8)
   #          print("band shape: ", band.shape)
   #          meta = raster.profile
   #          print("Meta: ", meta)

   #          x, y = raster.index(longitude, latitude)

   #          w = max_width
   #          h = max_height
   #          print("Width: ", w)
   #          print("Height: ", h)

   #          maxX = w - 1
   #          maxY = h - 1 
   #          raster_empty = np.zeros((h, w), dtype='uint8')
   #          print("X is: ", x)
   #          print("raster_empty shape: ", raster_empty.shape)
   #          print("band shape: ", band.shape)
   #          print(raster_empty[np.abs(x):(np.abs(x) + band.shape[1]), np.abs(y): (np.abs(y) + band.shape[0])].shape)
   #          raster_empty[np.abs(x):(np.abs(x) + band.shape[1]), np.abs(y): (np.abs(y) + band.shape[0])] += band
   #          plt.imshow(raster_empty)
   #          plt.show()


   #          # Fixed Bands
   #          band_x, band_y = raster.xy(x, y)
   #          # if x < 0:
   #          #    print("x<0")
   #          #    band = np.pad(band, (np.abs(x), 0), 'constant')
   #          #    test = np.pad(test, (5, 0), 'constant')
   #          #    print(test)
   #          # if maxX > band.shape[0]-1:
   #          #    print("maxX>band.shape[0]-1")
   #          #    band = np.pad(band, (0, maxX -(band.shape[0])), 'constant')
   #          #    test = np.pad(test, (5, 0), 'constant')
   #          #    print(test)
   #          # if y < 0:
   #          #    print("y<0")
   #          #    band = np.pad(band, ((np.abs(y), 0), (0,0)), 'constant')
   #          #    test = np.pad(test, ((5, 0), (0,0)), 'constant')
   #          #    print(test)
   #          # if maxY > band.shape[1]-1:
   #          #    print("maxY>band.shape[1]-1")
   #          #    band = np.pad(band, ((0, (maxY-band.shape[1])), (0,0)), 'constant')
   #          #    test = np.pad(test, ((0, 5), (0,0)), 'constant')
   #          #    print(test)
   #          # band = band[y:y+h, x:x+w]
   #          print("New Width: ", band.shape[1])
   #          print("New Height: ", band.shape[0])
            
   #          meta['dtype'] = 'uint8'
   #          meta['width'] = band.shape[1]
   #          meta['height'] = band.shape[0]
   #          meta['transform'] = meta['transform'] * meta['transform'].translation(band_x, band_y)
   #          meta['count'] = 1
   #          raster.close()
   #          # Write bands
   #          new_raster = rst.open(save_directory + '/' + name, 'w', **meta)
   #          new_raster.write(band, 1)
   #          new_raster.close()
   #    else:
   #       name = self.get_file_name(image_path)

   #       raster = rst.open(image_path)

   #       band = raster.read(band_num)
   #       band = np.asarray(band)
   #       meta = raster.profile 
   #       meta['width'] = band.shape[1]
   #       meta['height'] = band.shape[0]
   #       meta['count'] = 1
   #       raster.close()
   #    return name, band, meta

     # Reduce image size by the bounding box around interesting regions
   IND = 0
   def compress_image(self, image_path, save_directory, left, top, right, bottom, width, height, band_num=4, save=True):
      print("Compressing image ", self.IND)
      self.IND += 1
      meta = ""
      name = ""
      band = []
      dst_crs = rst.crs.CRS.from_epsg(4326) # Coordinate system Hu Tzu Shan 1950
      dst_width = width
      dst_height = height
      # left, bottom, right, top = -112.15743925707692, 34.2879692732589, -112.08819563514932, 34.314932373883536
      xres = (right - left) / dst_width
      yres = (top - bottom) / dst_height
      dst_transform = affine.Affine(xres, 0.0, left, 0.0, -yres, top)
      vrt_options = {
         'resampling': rst.enums.Resampling.cubic,
         'crs':dst_crs,
         'transform':dst_transform,
         'height':dst_height,
         'width':dst_width
      }
      if(save):
         if not os.path.exists(save_directory):
            os.makedirs(save_directory)
         name = self.get_file_name(image_path)
         if not os.path.exists(save_directory + "/" + name):
            try:
               with rst.open(image_path) as src:
                  # Write bands
                  band = src.read(band_num)
                  meta = src.profile
                  meta['count'] = 1
                  if not os.path.exists("Band4"):
                     os.makedirs("Band4")
                  raster = []
                  if not os.path.exists("Band4/" + name):
                     raster = rst.open("Band4" + '/' + name, 'w', **meta)
                     raster.write(band, 1)
                  else:
                     raster = rst.open("Band4/" + name)
                  with WarpedVRT(raster, **vrt_options) as vrt:
                        data = vrt.read(1)
                        # Process the dataset in chunks.  Likely not very efficient.
                        for _, window in vrt.block_windows():
                           data = vrt.read(window=window)
                        rio_shutil.copy(vrt, save_directory+"/"+name, driver='GTiff')
                        raster.close()
               # raster = rst.open(image_path)
               # print("Got Here First")
               # vrt = rst.vrt.WarpedVRT(raster, **vrt_options)
               # data = vrt.read(band_num)
               # print("Got Here")
               # for _, window in vrt.block_window(band_num, ):
               #    data = vrt.read(window=window)
               # plt.imshow(data)
               # plt.show()
               # raster.close()
            except:
               print("Could not open the file: ", name)
      
      return name, band, meta



def main():
   plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' # I need this for some reason?? Take out if it causes issues.
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run first. If it is executed after a different script it will not work.")
   ci = CompressImage()
   if(len(sys.argv) < 2):
      print("_________________________________\n")
      print("\tImage Reduction\n")
      print("_________________________________\n\n")
      print("1. Compress Images\n")
      print("2. Help\n")
      print("press any key (other than 1 or 2) to quit.\n\n")
      user_input = input(">>> ")
      if(user_input == '1'):
         path = input("Directory to apply compression to: ")
         save = input("Would you like to save (y/n)? ")
         if (save == 'y'):
            save = True
            save_directory = input("Directory to save to: ")
         else:
            save = False
            save_directory = "Not Applicable"
         band_num = input("Please enter the band that you would like to apply compression to (number): ")
         left, top, right, bottom, width, height = ci.get_width_height()
         width = width / 2
         height = height / 2
         # longitude =  -112.15743925707692
         # latitude = 34.31306953528484
         # width = 5424
         # height = 12713
         for image_path in ci.image_locations(path):
            ci.compress_image(image_path, save_directory, left, top, right, bottom, width, height)
      
      elif(user_input == '2'):
         print("To compress images you can use command line arguments, or if you do not insert anything\n")
         print("then you can run this program and enter input.")

   else:
      if sys.argv[1].lower() == "compress" and len(sys.argv) == 4:
         left = 0
         top = 0
         right = 0
         bottom = 0
         width = 0
         height = 0
         # raster = rst.open("Band4/AZPHD-000615_20160628T184704Z_00000.tif")
         # raster2 = rst.open("CompressedBands/AZPHD-000615_20160628T184704Z_00000.tif")
         # meta = raster.profile
         # band = raster.read(1)
         # meta2 = raster2.profile
         # band2 = raster2.read(1)
         # print(meta)
         # print(meta2)
         # plt.imshow(band)
         # plt.show()
         # plt.imshow(band2)
         # plt.show()
         # raster.close()
         if not os.path.exists("imgDim.txt"):
            print("no image dimension data")
            left, top, right, bottom, width, height = ci.get_width_height(sys.argv[2])
            dimFile = open("imgDim.txt", "a+")
            width = width / 2
            height = height / 2
            dimFile.write("left: %f\n" % left)
            dimFile.write("top: %f\n" % top)
            dimFile.write("right: %f\n" % right)
            dimFile.write("bottom: %f\n" % bottom)
            dimFile.write("width: %d\n" % width)
            dimFile.write("height: %d" % height)
            dimFile.close()
         else:
            print("file exists")
            dimFile = open("imgDim.txt", "r+")
            left = float(dimFile.readline()[6:-1])
            top = float(dimFile.readline()[5:-1])
            right = float(dimFile.readline()[7:-1])
            bottom = float(dimFile.readline()[8:-1])
            width = int(dimFile.readline()[7:-1])
            height = int(dimFile.readline()[8:])
            print(left)
            print(top)
            print(right)
            print(bottom)
            print(width)
            print(height)
            dimFile.close()

         print("Compressing Images...")
         for image_path in ci.image_locations(path=sys.argv[2]):
            ci.compress_image(image_path, sys.argv[3], left, top, right, bottom, width, height) #max_width=3585, max_height = 3884)
      elif sys.argv[1].lower() == "compress" and len(sys.argv) != 4:
         print("To compress images please enter: compress image_directory_to_compress save_directory")
      elif(len(sys.argv) > 2):
         print("To compress images please enter: compress image_directory_to_compress save_directory")

if __name__ == "__main__":
   main()
