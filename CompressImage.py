import numpy as np
import os
import sys
from pathlib import Path
from osgeo import gdal
import rasterio as rst
import rasterio.features
import rasterio.warp
import rasterio.transform
import matplotlib.pyplot as plt
import cv2 as cv
import matplotlib.animation as animation
from MP4Maker import MP4Maker

class CompressImage:

   ###################################################
   ##       Function: image_locations               ##
   ## Retrieves file names from the designated      ##
   ## directory, and returns a numpy array of file  ##
   ## names.                                        ##
   ###################################################
   def image_locations(self, path="Original_Images"):
      dir = Path(path)
      image_names = []
      for file in dir.glob('*.tif*'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image_names.append(file_name)        
      return np.asarray(image_names)

      
   def get_file_name(self, image_path):
      index_slash = image_path.rfind('/')
      return image_path[index_slash+1:len(image_path)]

   # Pre-processing to get the width and height of the bounding box of the first image.
   def get_width_height(self, path="Original_Images"):
      max_width = 0
      max_height = 0
      num_image = 0
      iteration = 0
      latitude = 0
      longitude = 0
      for image_path in self.image_locations(path):
         if iteration == 1:
            break
 
         raster = rst.open(image_path)
         band_5 = raster.read(5)
         max_value = np.max(band_5)
         band_5 = band_5.astype(np.float64)/max_value #normalize
         band_5 = 255 * band_5
         band_5 = band_5.astype(np.uint8)
         ret,thresh = cv.threshold(band_5,127,255,cv.THRESH_BINARY_INV)
         kernel = np.ones((1,1), np.uint8) 
         dilation = cv.dilate(thresh, kernel, iterations=1) 
         contours, hierarchy = cv.findContours(dilation, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
         ws = []
         hs = []
         xs = []
         ys = []
         for contour in contours[1:]:
            x, y, w, h = cv.boundingRect(contour)

            ws.append(w)
            hs.append(h)
            xs.append(x)
            ys.append(y)
         ws = np.asarray(ws)
         hs = np.asarray(hs)
         xs = np.asarray(xs)
         ys = np.asarray(ys)

         x = np.min(xs) - 300
         y = np.min(ys) - 800
         w = np.max(xs) - np.min(xs) + ws[np.argmax(xs)] + 1000 # hundreds give a little more room in case of cutoffs
         h = np.max(ys) - np.min(ys) + hs[np.argmax(xs)] + 700
         if w > max_width:
            max_width = w
         if h > max_height:
            max_height = h
         raster.close()
         num_image += 1
         iteration += 1
         longitude, latitude = raster.xy(x, y)

      return longitude, latitude, max_width, max_height

   # Reduce image size by the bounding box around interesting regions
   def compress_image(self, image_path, save_directory, longitude, latitude, max_width, max_height):
      print("Compressing Images...")
      if not os.path.exists(save_directory):
         os.makedirs(save_directory)
      name = self.get_file_name(image_path)
      if not os.path.exists(save_directory + "/" + name):

         raster = rst.open(image_path)

         band_5 = raster.read(5)
         meta = raster.profile
         

         max_value = np.max(band_5)
         band_5 = band_5.astype(np.float64)/max_value #normalize
         band_5 = 255 * band_5
         band_5 = band_5.astype(np.uint8)
         ret,thresh = cv.threshold(band_5,127,255,cv.THRESH_BINARY_INV)
         kernel = np.ones((1,1), np.uint8) 
         dilation = cv.dilate(thresh, kernel, iterations=1) 
         contours, hierarchy = cv.findContours(dilation, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)


         y, x = raster.index(longitude, latitude)

         w = max_width
         h = max_height

         # Reduced Bands
         band_x, band_y = raster.xy(x, y)
         band_1 = raster.read(1)[y:y+h, x:x+w]
         band_2 = raster.read(2)[y:y+h, x:x+w]
         band_3 = raster.read(3)[y:y+h, x:x+w]
         band_4 = raster.read(4)[y:y+h, x:x+w]
         band_5 = raster.read(5)[y:y+h, x:x+w]
         
         meta['width'] = band_1.shape[1]
         meta['height'] = band_1.shape[0]
         meta['transform'] = meta['transform'] * meta['transform'].translation(band_x, band_y)

         raster.close()

         # Write bands
         new_raster = rst.open(save_directory + '/' + name, 'w', **meta)
         new_raster.write(band_1, 1)
         new_raster.write(band_2, 2)
         new_raster.write(band_3, 3)
         new_raster.write(band_4, 4)
         new_raster.write(band_5, 5)
         new_raster.close()


   def get_coordinates(self, image_path):
      raster = rst.open(image_path)
      print(raster.profile)
      mask = raster.dataset_mask()
      for geom, val in rasterio.features.shapes(mask, transform=raster.transform):
         geom = rasterio.warp.transform_geom(raster.crs, 'EPSG:4326', geom, precision=6)
         print(geom)

   def open_and_view_all(self, image_path):
      raster = rst.open(image_path)

      fig = plt.figure()
      blue = raster.read(1)
      green = raster.read(2)
      red = raster.read(3)
      rgb = np.dstack((red,green,blue))
      band_4 = raster.read(4)
      band_5 = raster.read(5)

      fig.add_subplot(1, 2, 1)
      plt.imshow(rgb)
      fig.add_subplot(1, 3, 2)
      plt.imshow(band_4)
      fig.add_subplot(1, 3, 3)
      plt.imshow(band_5)
      plt.show()

   def open_and_view_one(self, image_path, band_num = 4):
      raster = rst.open(image_path)
      band = raster.read(int(band_num))
      plt.imshow(band)
      plt.show()

   def create_vid(self, path="Compressed_Images", save_path = "Animations/Images", band_num = 4):
      dir = Path(path)
      image_names = []
      for file in dir.glob('*.tif*'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image_names.append(file_name)  
      np.asarray(image_names)
      images = []
      fig = plt.figure()
      maxw = 0
      maxh = 0
      for image_name in image_names:
         raster = rst.open(image_name)
         image = raster.read(band_num)
         meta = raster.profile
         width = meta["width"]
         height = meta["height"]
         if(width > maxw):
            maxw = width
         if(height > maxh):
            maxh = height
         raster.close()
      for image_name in image_names:
         raster = rst.open(image_name)
         image = raster.read(band_num)

         normalized_image = image/np.max(image)
         image = 255 * normalized_image
         image = image.astype(np.uint8)

         plt.title("Band " + str(band_num))
         images.append([plt.imshow(image, cmap="gray")])#, cmap='nipy_spectral')])
         raster.close()

      print("Creating Animation")
      ani = animation.ArtistAnimation(fig, images, interval=100, blit=True,
                                    repeat_delay=1000)
      print("Saving Animation")
      ani.save(save_path + ".mp4")
   
   def create_color_vid(self, path="Compressed_Images", save_path = "Animations/Images"):
      dir = Path(path)
      image_names = []
      for file in dir.glob('*.tif*'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image_names.append(file_name)  
      np.asarray(image_names)
      images = []
      fig = plt.figure()
      maxw = 0
      maxh = 0
      for image_name in image_names:
         raster = rst.open(image_name)
         image = raster.read(1)
         meta = raster.profile
         width = meta["width"]
         height = meta["height"]
         if(width > maxw):
            maxw = width
         if(height > maxh):
            maxh = height
         raster.close()
      for image_name in image_names:
         raster = rst.open(image_name)
         blue = raster.read(1)
         green = raster.read(2)
         red = raster.read(3)

         image = np.dstack((red,green,blue))


         plt.title("RGB Bands")
         images.append([plt.imshow(image, cmap="gray")])#, cmap='nipy_spectral')])
         raster.close()

      print("Creating Animation")
      ani = animation.ArtistAnimation(fig, images, interval=100, blit=True,
                                    repeat_delay=1000)
      print("Saving Animation")
      ani.save(save_path + ".mp4")




def main():
   plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' # I need this for some reason?? Take out if it causes issues.
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run first. If it is executed after a different script it will not work.")
   ci = CompressImage()
   if len(sys.argv) < 2:
      print("Please enter the directory of the images you would like to compress and the new directory for the compressed images.")
   elif sys.argv[1].lower() == "compress" and len(sys.argv) == 4:
      longitude, latitude, width, height = ci.get_width_height()
      for image_path in ci.image_locations(path=sys.argv[2]):
         ci.compress_image(image_path, sys.argv[3], longitude, latitude, width, height) #max_width=3585, max_height = 3884)
   elif sys.argv[1].lower() == "compress" and len(sys.argv) != 4:
      print("To compress images please enter: compress image_directory_to_compress save_directory")
   elif sys.argv[1].lower() == "viewall" and len(sys.argv) == 3:
      ci.open_and_view_all(image_path = sys.argv[2])
   elif sys.argv[1].lower() == "viewall" and len(sys.argv) != 3:
      print("To view all image bands please enter: viewall image_directory")
   elif sys.argv[1].lower() == "viewone" and len(sys.argv) == 4:
      ci.open_and_view_one(image_path = sys.argv[2], band_num= sys.argv[3])
   elif sys.argv[1].lower() == "viewone" and len(sys.argv) != 4:
      print("To view one image band please enter: viewone image_directory, band_number")
   elif sys.argv[1].lower() == "vid" and len(sys.argv) == 5:
      ci.create_vid(sys.argv[2], sys.argv[3], int(sys.argv[4]))
   elif sys.argv[1].lower() == "vid" and len(sys.argv) != 5:
      print("To create a video please enter: vid images_directory save_directory band_number")
   elif sys.argv[1].lower() == "cvid" and len(sys.argv) == 4:
      ci.create_color_vid(sys.argv[2], sys.argv[3])
   elif sys.argv[1].lower() == "cvid" and len(sys.argv) != 4:
      print("To create a color video please enter: cvid images_directory save_directory")
   else:
      print("To compress images please enter: compress image_directory_to_compress save_directory")
      print("To view all image bands please enter: viewall image_directory")
      print("To view one image band please enter: viewone image_directory, band_number")
      print("To create a video please enter: vid images_directory save_directory band_number")
      print("To create a color video please enter: cvid images_directory save_directory")

if __name__ == "__main__":
   main()
