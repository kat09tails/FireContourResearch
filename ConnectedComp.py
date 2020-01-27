import numpy as np
import os
import sys
from pathlib import Path
from osgeo import gdal
import rasterio as rst
import matplotlib.pyplot as plt
import cv2 as cv
from scipy.ndimage import gaussian_filter
from skimage import measure
from scipy.stats import itemfreq
import matplotlib.animation as animation
from MP4Maker import MP4Maker
import cc3d

class ConnectedComp:
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

   def apply_connected_comp(self, apply_directory, save_directory, num_components=100, num_images = 200):
      index_slash = save_directory.rfind('/')
      directory = save_directory[0:index_slash]
      print("Applying Connected Components...")
      if not os.path.exists(directory):
         os.makedirs(directory)    
      file_names = []
      images = []
      meta = []
      meta.append(['driver', 'dtype', 'nodata', 'width', 'height', 'count', 'crs', 'pixel width', 'row rotation', 'upperleftx_coord', 'column rotation', 'pixel height','upperlefty_coord', 'blockxsize', 'blockysize', 'tiled', 'compress', 'interleave'])
      image_num = 0
      for image_path in self.image_locations(apply_directory):
         if image_num < num_images:
            name = self.get_file_name(image_path)
            raster = rst.open(image_path)
            profile = raster.profile
            image = raster.read(1)
            image[image == 255] = 1
            file_names.append(name)
            images.append(image)
            pixel_transform = profile['transform']
            meta.append(['GTiff', 'uint8', 0.0, 2462, 3500, 1, 'epsg:4326', pixel_transform[0], pixel_transform[1], pixel_transform[2], pixel_transform[3], pixel_transform[4], pixel_transform[5], 256, 256, True, 'deflate', 'band'])
            image_num += 1
      file_names = np.asarray(file_names)
      images = np.asarray(images)
      print(meta[0])
      meta = np.asarray(meta)
      connectivity = 6 
      print("Connecting Components...")
      labeled_data = cc3d.connected_components(images, connectivity=connectivity)
      print(np.unique(labeled_data))
      labeled_data[labeled_data > int(num_components)] = 0

      print("Saving Images...")
      np.save(save_directory + ".npy", labeled_data)
      print("Saving Names...")
      np.save(save_directory + "_names.npy", file_names)
      print("Saving Meta...")
      np.save(save_directory + "_meta.npy", meta)

   ##---------------For Viewing Purposes Only from here on----------------------------
   def create_connected_components_vid(self, path, save_path):
      print(save_path)
      print(path)
      ccarray = np.load(path)
      images = []
      fig = plt.figure()
      for image in ccarray:
         plt.title("Connected Component")
         for i in range(1, 50):
            image[image == i] = 260 - (i * 5)
         images.append([plt.imshow(image, cmap="Greys")])#, cmap='nipy_spectral')])
      images = np.asarray(images)
      print("Creating Animation")
      ani = animation.ArtistAnimation(fig, images, interval=50, blit=True,
                                    repeat_delay=1000)
      print("Saving Animation")
      save_name = save_path + ".mp4"
      ani.save(save_name)

def main():
   plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' # I need this for some reason?? Take out if it causes issues.
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run after KMeansConverter.py. If it is executed after a different script it will not work.")
   cc = ConnectedComp()
   if len(sys.argv) < 2:
      print("Please enter the directory of the images you would like to compress and the new directory for the compressed images.")
   elif sys.argv[1].lower() == "cc" and len(sys.argv) == 5:
      cc.apply_connected_comp(sys.argv[2], sys.argv[3], sys.argv[4])
   elif sys.argv[1].lower() == "cc" and len(sys.argv) != 5:
      print("To apply connected components to images please enter: cc image_directory_to_apply save_directory number_components")
   elif sys.argv[1].lower() == "vid" and len(sys.argv) == 4:
      cc.create_connected_components_vid(sys.argv[2], sys.argv[3])
   elif sys.argv[1].lower() == "vid" and len(sys.argv) != 4:
      print("To create a connected components video please enter: vid images_directory save_directory")
   else:
      print("To apply connected components to images please enter: cc image_directory_to_apply save_directory")
      print("To create a connected components video please enter: vid images_directory save_directory")

if __name__ == "__main__":
   main()