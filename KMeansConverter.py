import numpy as np
import os
import sys
from math import sqrt
from pathlib import Path
# from osgeo import gdal
import rasterio as rst
import matplotlib.pyplot as plt
import cv2 as cv
from scipy.ndimage import gaussian_filter
from sklearn.metrics import silhouette_score as silhouette
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from yellowbrick.cluster import KElbowVisualizer
from yellowbrick.cluster import SilhouetteVisualizer
# from collections import Counter
# import peakutils

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

   def determine_clusters_elbow(self, image_path):
      raster = rst.open(image_path)
      band = raster.read(1)
      blurred_image = gaussian_filter(band, sigma=5)
      new_band = ((blurred_image.astype(np.float64)/np.max(blurred_image)) * 255).astype(np.uint8)
      # float_image = np.float32(blurred_image)
      num_data = new_band.shape[0]*new_band.shape[1]
      new_band = new_band.reshape(num_data, 1)
      model = KMeans()
      visualizer = KElbowVisualizer(model, k=(1,20))
      print(new_band.shape)
      visualizer.fit(new_band[:100000])
      visualizer.show()

   def determine_clusters_silhouette(self, image_path):
      raster = rst.open(image_path)
      band = raster.read(1)
      blurred_image = gaussian_filter(band, sigma=5)
      new_band = ((blurred_image.astype(np.float64)/np.max(blurred_image)) * 255).astype(np.uint8)
      # float_image = np.float32(blurred_image)
      num_data = new_band.shape[0]*new_band.shape[1]
      new_band = new_band.reshape(num_data, 1)
      model = KMeans(4)
      visualizer = SilhouetteVisualizer(model)
      print(new_band.shape)
      visualizer.fit(new_band[:100000])
      visualizer.show()


   # Retrieves band four and applies 5 cluster k-means
   previous_image = []
   iteration = 0
   def apply_KMeans(self, image_path, save_directory, apply_max_accumulate = False, save = True):
      raster = rst.open(image_path)
      band = raster.read(1)
      meta = raster.profile
      plt.imshow(band)
      plt.show()

      image_array = []
      if(apply_max_accumulate):
         if(self.iteration == 0):
            self.previous_image = np.copy(band)
            self.iteration += 1
         current_image = np.copy(band)
         image_array.append(self.previous_image)
         image_array.append(current_image)
         image_array = np.asarray(image_array)
         max_accum = np.maximum.accumulate(image_array, axis=0)
         self.previous_image = np.copy(max_accum[1])
         band = np.copy(max_accum[1])

         plt.imshow(band)
         plt.show()       


      # band = ((band.astype(np.float64)/np.max(band)) * 255).astype(np.uint8)

      blurred_image = gaussian_filter(band, sigma=5)
      
      float_image = np.float32(blurred_image)
      num_data = float_image.shape[0]*float_image.shape[1]
      float_image = float_image.reshape(num_data, 1)
      # print(float_image)

      ## For Test Purposes only####################################
      # X, y = make_blobs(n_samples=500,
      #             n_features=2,
      #             centers=4,
      #             cluster_std=1,
      #             center_box=(-10.0, 10.0),
      #             shuffle=True,
      #             random_state=1)
      # print(X)
      # clusterer = KMeans(n_clusters=2, random_state=10)
      # cluster_labels = clusterer.fit_predict(X)
      # print(clusterer)
      # print(cluster_labels.shape)
      # score = silhouette(float_image, cluster_labels)
      # print("Silhouette Score: " + score)
      #############################################################   
      num_clusters = sqrt(num_data/2)
      print(num_clusters)
      criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 5, 0.0001)
      ret,label,center = cv.kmeans(float_image, 5, None, criteria, 5, cv.KMEANS_RANDOM_CENTERS)
      # print(label.shape)
      # label = np.ravel(label)
      # print(label)
      # print(label.shape)
      # score = silhouette(float_image, label)
      # print("Silhouette Score: " + score)
      # print(label.shape)
      center = np.uint8(center)
      res = center[label.flatten()]
      k_applied_image = res.reshape((band.shape))
      un = np.unique(k_applied_image)

      k_applied_image[k_applied_image == np.max(k_applied_image)] = 255

      k_applied_image[k_applied_image < np.max(k_applied_image)] = 0

      meta['dtype'] = 'uint8'
      if(save):
         if not os.path.exists(save_directory):
            os.makedirs(save_directory)
         name = self.get_file_name(image_path)
         if not os.path.exists(save_directory + "/" + name):
            new_raster = rst.open(save_directory + '/' + name, 'w', **meta)
            new_raster.write(k_applied_image, 1)
            new_raster.close()
      return k_applied_image



def main():
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run after CompressImage.py. If it is executed after a different script it will not work.")
   km = KMeansConverter()
   if len(sys.argv) < 2:
      print("_________________________________\n")
      print("\tK Means Converter\n")
      print("_________________________________\n\n")
      print("1. Apply K Means\n")
      print("2. View Elbow Score Plot\n")
      print("3. View Silouhette Score Plot\n")
      print("4. Help\n")
      print("press any key (other than 1 or 2) to quit.\n\n")
      user_input = input(">>> ")
      if(user_input == '1'):
         path = input("Directory to apply k means to: ")
         save = input("Would you like to save (y/n)? ")
         max_accumulate = input("Would you like to apply the max pixel value accumulation (y/n)? ")
         save_directory = ""
         if (save == 'y'):
            save = True
            save_directory = input("Directory to save to: ")
         else:
            save = False
            save_directory = "Not Applicable"
         if (max_accumulate == 'y'):
            max_accumulate = True
         else:
            max_accumulate = False
         print("Applying KMeans...")
         for image_path in km.image_locations(path):
            km.apply_KMeans(image_path, save_directory, max_accumulate, save)
      elif(user_input == '2'):
         path = input("Path of image you would like to apply this to: ")
         path = 'Band_4_Compressed/AZPHD-000615_20160628T184704Z_00000.tif'
         km.determine_clusters_elbow(path)
      elif(user_input == '3'):
         path = input("Path of image you would like to apply this to: ")
         path = 'Band_4_Compressed/AZPHD-000615_20160628T184704Z_00000.tif'
         km.determine_clusters_silhouette(path)
      elif(user_input == '4'):
         print("To compress images you can use command line arguments, or if you do not insert anything\n")
         print("then you can run this program and enter input.\n")
         print("K Means Converter expects a directory of 1 band geotiffs.")
   elif sys.argv[1].lower() == "kmeans" and len(sys.argv) == 6:
      max_accum = False
      save = False
      if sys.argv[4] == 'y':
         max_accum = True
      if sys.argv[5] == 'y':
         save = True
      for image_path in km.image_locations(path=sys.argv[2]):
         km.apply_KMeans(image_path, sys.argv[3], sys.argv[4], sys.argv[5])
   elif sys.argv[1].lower() == "kmeans" and len(sys.argv) != 4:
      print("To apply kmeans to images please enter: kmeans image_directory_to_apply save_directory")
   else:
      print("To apply kmeans to images please enter: kmeans image_directory_to_apply save_directory use_max_accumulate(t/n) save(y/n)")


if __name__ == "__main__":
   main()