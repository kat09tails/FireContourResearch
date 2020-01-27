import numpy as np
import os
import sys
from pathlib import Path
from osgeo import gdal
import rasterio as rst
import matplotlib.pyplot as plt
import cv2 as cv
from scipy.ndimage import gaussian_filter
import matplotlib.animation as animation
from MP4Maker import MP4Maker
from PIL import Image
from PIL import ImageEnhance
from collections import Counter
import peakutils

class KMeansConverter:

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

   # Retrieves band four and applies 5 cluster k-means
   def apply_KMeans(self, image_path, save_directory):
      print("Applying KMeans...")
      if not os.path.exists(save_directory):
         os.makedirs(save_directory)
      name = self.get_file_name(image_path)
      if not os.path.exists(save_directory + "/" + name):
         raster = rst.open(image_path)
         band_4 = raster.read(4)
         meta = raster.profile

         band = ((band_4.astype(np.float64)/np.max(band_4)) * 255).astype(np.uint8)

         blurred_image = gaussian_filter(band, sigma=5)
         
         float_image = np.float32(blurred_image)
         num_data = float_image.shape[0]*float_image.shape[1]
         float_image = float_image.reshape(num_data, 1)

         criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 5, 0.0001)
         ret,label,center = cv.kmeans(float_image, 5, None, criteria, 5, cv.KMEANS_RANDOM_CENTERS)
         center = np.uint8(center)
         res = center[label.flatten()]
         k_applied_image = res.reshape((band_4.shape))
         un = np.unique(k_applied_image)

         k_applied_image[k_applied_image == np.max(k_applied_image)] = 255

         k_applied_image[k_applied_image < np.max(k_applied_image)] = 0

         meta['count'] = 1
         meta['dtype'] = 'uint8'


         new_raster = rst.open(save_directory + '/' + name, 'w', **meta)
         new_raster.write(k_applied_image, 1)
         new_raster.close()

   ##---------------For Viewing Purposes Only from here on----------------------------
   def open_and_view(self, image_path, image_path_2):
      fig = plt.figure()
      raster = rst.open(image_path)
      print(raster.profile)
      image = raster.read(5)
      image = np.float32(image) * 255 / np.max(image)
      image = image.astype(np.uint8)
      print(np.unique(image))
      raster2 = rst.open(image_path_2)
      kmeans = raster2.read(1)
      print(np.unique(kmeans))

      fig.add_subplot(1, 3, 1)
      plt.imshow(kmeans)
      fig.add_subplot(1, 3, 2)
      plt.imshow(image)
      fig.add_subplot(1, 3, 3)
      plt.hist(image, 32, [0, 256])

      plt.show()
      raster.close()
      raster2.close()

   def create_kmeans_vid(self, path, save_path):
      dir = Path(path)
      image_names = []
      for file in dir.glob('*.tif*'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image_names.append(file_name)  
      np.asarray(image_names)
      images = []
      fig = plt.figure()
      for image_name in image_names:
         raster = rst.open(image_name)
         image = raster.read(1)
         plt.title("KMeans Band 4")
         images.append([plt.imshow(image, cmap="gray")])#, cmap='nipy_spectral')])
         raster.close()
      print("Creating Animation")
      ani = animation.ArtistAnimation(fig, images, interval=100, blit=True,
                                    repeat_delay=1000)
      print("Saving Animation")
      ani.save(save_path + ".mp4")

def main():
   plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' # I need this for some reason?? Take out if it causes issues.
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run after CompressImage.py. If it is executed after a different script it will not work.")
   km = KMeansConverter()
   if len(sys.argv) < 2:
      print("Please enter the directory of the images you would like to compress and the new directory for the compressed images.")
   elif sys.argv[1].lower() == "kmeans" and len(sys.argv) == 4:
      for image_path in km.image_locations(path=sys.argv[2]):
         km.apply_KMeans(image_path, sys.argv[3])
   elif sys.argv[1].lower() == "kmeans" and len(sys.argv) != 4:
      print("To apply kmeans to images please enter: kmeans image_directory_to_apply save_directory")
   elif sys.argv[1].lower() == "view" and len(sys.argv) == 4:
      km.open_and_view(image_path = sys.argv[2], image_path_2 = sys.argv[3])
   elif sys.argv[1].lower() == "view" and len(sys.argv) != 4:
      print("To view an image please enter: view image_directory")
   elif sys.argv[1].lower() == "vid" and len(sys.argv) == 4:
      km.create_kmeans_vid(sys.argv[2], sys.argv[3])
   elif sys.argv[1].lower() == "vid" and len(sys.argv) != 4:
      print("To create a kmeans video please enter: vid images_directory save_directory")
   else:
      print("To apply kmeans to images please enter: kmeans image_directory_to_apply save_directory")
      print("To view an image please enter: view image_directory kmeans_directory")
      print("To create a video please enter: vid images_directory save_directory")

if __name__ == "__main__":
   main()