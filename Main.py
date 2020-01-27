from CompressImage import CompressImage
from KMeansConverter import KMeansConverter
from ConnectedComp import ConnectedComp
from Contour2Shp import Contour2Shp
import matplotlib.pyplot as plt
import os
import sys
from pathlib import Path
import shutil
import timeit

'''----------------------------------------
|   Created by Kathryn Reese               |
|   Class: Main                            |
|   Designed to run all classes.           |
|------------------------------------------|
'''
class Program:
   def help(self):
      print("This program is designed to reduce files sizes, apply kmeans, apply 3d connected components, and the apply contours and place in shape files.")
      print("It reduces the file sizes by using OpenCV's find contours, and then placing a bounding box around the predominant contour area. It takes this bounding box and makes that area a new image.")
      print("The program then applies kmeans to these reduced images, then saves those images as geotiffs with only one band.")
      print("Connected Components is then applied to the kmeans images, and then connected components is saved as 3 npy files.")
      print("Contour2Shp then takes the connected component files and applies opencv's contouring method to these files, and then saves them as shape files.")
      print("\nYou can do each individual step, but ensure that you do them in the order described above.")
      print("\nTo use this program enter \"python Main.py save/nosave directory_to_apply save_directory\"")
      print("\tEnter save if you wish to save each type of geotiff/npy along the way.")
      print("\tEnter nosave if you wish to delete each type of geotiff/npy along the way.")

   def runPrograms(self, apply_directory, save_directory="Shape Files", num_components = 1, save=False):
      ci = CompressImage()
      km = KMeansConverter()
      cc = ConnectedComp()
      cs = Contour2Shp()

      if not os.path.exists(save_directory):
         os.makedirs(save_directory)

      print("Step: Compressing Image")
      tic = timeit.default_timer()
      longitude, latitude, width, height = ci.get_width_height(apply_directory)
      for image_path in ci.image_locations(apply_directory):
         ci.compress_image(image_path, save_directory + "/CompressedImages", longitude, latitude, width, height)
      toc = timeit.default_timer()
      print("Time to compress: {}" .format(str(toc-tic)))

      print("Step: Applying K-Means")
      tic = timeit.default_timer()
      for image_path in km.image_locations(save_directory + "/CompressedImages"):
         km.apply_KMeans(image_path, save_directory + "/KMeans")
      toc = timeit.default_timer()
      print("Time applying K-Means: {}" .format(str(toc-tic)))

      if not save:
         print("Deleting Compressed Images...")
         tic = timeit.default_timer()
         shutil.rmtree(save_directory + "/CompressedImages")
         toc = timeit.default_timer()
         print("Time deleting compressed images: {}" .format(str(toc-tic)))

      print("Step: Applying Connected Components")
      tic = timeit.default_timer()
      cc.apply_connected_comp(save_directory + "/KMeans", save_directory + "/Connected Components/cc6_" + num_components, num_components)
      toc = timeit.default_timer()

      if not save:
         print("Deleting K-Means...")
         tic = timeit.default_timer()
         shutil.rmtree(save_directory + "/KMeans")
         toc = timeit.default_timer()
         print("Time deleting K-Means Images: {}" .format(str(toc-tic)))

      print("Step: Applying Contouring and Saving to shp")
      tic = timeit.default_timer()
      cs.convert_npy_2_shp(save_directory + "/Connected Components", save_directory + "/Shape Files")
      toc = timeit.default_timer()
      print("Time applying contouring and saving to shp: {}" .format(str(toc-tic)))

      if not save:
         print("Deleting Connected Components...")
         tic = timeit.default_timer()
         shutil.rmtree(save_directory + "/Connected Components")  
         toc = timeit.default_timer()
         print("Time deleting connected components: {}" .format(str(toc-tic)))

      print("Process Complete")
      print("You can view a shape file by using the commands \"python Contour2Shp.py view image_path\"")   

def main():
   plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' # I need this for some reason?? Take out if it causes issues.
   prog = Program()
   if len(sys.argv) == 1:
      print("Enter \"python Main.py help\" to learn how to use this program.")
   elif sys.argv[1] == 'help':
      prog.help()
   elif len(sys.argv) == 5 and sys.argv[1].lower() == 'save':
      prog.runPrograms(sys.argv[2], sys.argv[3], sys.argv[4], True)
   elif len(sys.argv) == 5 and sys.argv[1].lower() == 'nosave':
      prog.runPrograms(sys.argv[2], sys.argv[3], sys.argv[4], False)
   else:
      print("Enter \"python Main.py help\" to learn how to use this program.")
      print("\nTo use this program enter \"python Main.py save/nosave directory_to_apply save_directory number_components\"")  


if __name__ == "__main__":
   main()
   