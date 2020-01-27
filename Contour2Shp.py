import numpy as np
import os
import sys
from pathlib import Path
import matplotlib.pyplot as plt
import cv2 as cv
import matplotlib.animation as animation
from MP4Maker import MP4Maker
from shapely.geometry import mapping, Point, MultiPoint, MultiPolygon, Polygon #LineString, MultiLineString
import fiona
import geopandas as gpd
from fiona.crs import from_epsg
import shapefile as shp

class Contour2Shp:
   ###################################################
   ##       Function: image_locations               ##
   ## Retrieves file names from the designated      ##
   ## directory, and returns a numpy array of file  ##
   ## names.                                        ##
   ###################################################
   def image_locations(self, path="Original_Images"):
      dir = Path(path)
      image_names = []
      for file in dir.glob('*.shp'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image_names.append(file_name)        
      return np.asarray(image_names)

   def retrieve_images(self, apply_directory):
      dir = Path(apply_directory)
      meta = []
      images = []
      names = []
      for file in dir.glob('*.npy'):
         file_name = os.path.basename(file)
         index = file_name.find('.')
         check1 = file_name[index - 4:index] 
         check2 = file_name[index - 5:index]
         if check1 == "meta":
            meta = np.load(apply_directory + '/' + file_name, allow_pickle=True)
         elif check2 == "names":
            names = np.load(apply_directory + '/' + file_name)
         else:
            images = np.load(apply_directory + '/' + file_name)
            print("Got here " +file_name)
      return names, images, meta


   # creates contours from the connected components and saves them as shape files with meta data
   def convert_npy_2_shp(self, apply_directory, save_directory):
      if not os.path.exists(save_directory):
         os.makedirs(save_directory) 
      names, images, meta = self.retrieve_images(apply_directory)
      print("Applying Contours...")
      # Just for vid purpose only-----------
      contour_images = []
      #-------------------------------------
      print(len(names))
      for index, name in enumerate(names):
         ind = name.rfind('.')
         name = name[:ind]
         #print(name)
         dictionary = {}
         for indc, data in enumerate(meta[index + 1]):
            dictionary[meta[0][indc]] = data
         image = []
         image = np.copy(images[index])
         image[image > 1] = 1
         image = image.astype(np.uint8)

         contours, hierarchy = cv.findContours(image, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
         # Just for vid purpose only-----------
         contour_image = np.zeros_like(image)
         cv.drawContours(contour_image, contours, -1, color=(255,255,255), thickness=10)
         contour_images.append(contour_image)
         #-------------------------------------
         points = []
         polygons = []
         for contour in contours:
            if len(contour) > 400:
               contour = np.asarray(contour)
               num_points = 0
               points_given = 0
               for xy in contour:
                  num_points += 1
                  if num_points == 15:  # The Number of points that are eliminated
                     pt = Point(xy[0][0], xy[0][1])
                     points.append(pt)
                     points_given += 1
                     num_points = 0
               if(points_given < 3):
                  pass
               else:
                  polygon = Polygon([p.x, p.y] for p in points)
                  #polygon = polygon.simplify(0.001, False)
                  polygons.append(polygon)
               points = []
         polygon_list = MultiPolygon(polygons) 
         info = {
            'geometry': 'MultiPolygon',
            'properties' : {'driver':'str', 'dtype':'str', 'nodata':'float', 'width':'int', 'height':'int', 'count':'int', 'crs':'str', 'pixel width':'float', 'row rotation':'float', 'upperleftx_coord':'int', 'column rotation':'float', 'pixel height':'float', 'upperlefty_coord':'int', 'blockxsize':'int', 'blockysize':'int', 'tiled':'bool', 'compress':'str', 'interleave':'str'},
         }

         print("Saving Shape File...")
         save_path = save_directory + "/" + name + ".shp"
         shape = fiona.open(save_path, 'w', crs = from_epsg(4326), driver = 'ESRI Shapefile', schema=info)
         shape.write({
            'geometry': mapping(polygon_list),
            'properties' : dictionary,
         })
         shape.close()
      contour_images = np.asarray(contour_images)
      np.save("Applied_Images/Shape Files/contour.npy", contour_images)
   ##---------------View Only from here on----------------------------
   ###################################################
   ##       Function: view_shape_files              ##
   ## Takes in multiple shape files to view.        ##
   ###################################################
   def view_shape_files(self, file):
      shape = gpd.read_file(file + ".shp")
      width = 0
      height = 0
      for dictionary in fiona.open(file + ".shp"):
         height = dictionary['properties']['height']
         width = dictionary['properties']['width']
      shape.plot()
      plt.axis([0, width, height, 0])
      plt.show()

   def create_contour_vid(self, path, save_path):
      print(save_path)
      print(path)
      ccarray = np.load(path)
      images = []
      fig = plt.figure()
      for image in ccarray:
         plt.title("Contours")
         images.append([plt.imshow(image, cmap="Greys")])#, cmap='nipy_spectral')])
      images = np.asarray(images)
      print("Creating Animation")
      ani = animation.ArtistAnimation(fig, images, interval=50, blit=True,
                                    repeat_delay=1000)
      print("Saving Animation")

      save_name = save_path + ".mp4"

      ani.save(save_name)

   def create_vid(self, apply_path, save_path):
      if not os.path.exists("temp_directory"):
         os.makedirs("temp_directory")
      dir = Path(apply_path)
      images = []
      width = 0
      height = 0
      
      interval = 0

      for file in dir.glob('*.shp'):
         index = os.path.basename(file).rfind('.')
         if not os.path.exists("temp_directory/" + os.path.basename(file)[:index] + ".png"):
            file_name = os.path.dirname(file) + "/" + os.path.basename(file)
            shape = gpd.read_file(file_name)
            # shape = shp.Reader(file_name)
            # if interval == 0:
            #    for dictionary in fiona.open(file_name):
            #       height = dictionary['properties']['height']
            #       width = dictionary['properties']['width']
            #    interval += 1
            # #polygons = []
            # for sh in shape.shapeRecords():
            #    x = [i[0] for i in sh.shape.points[:]]
            #    y = [i[1] for i in sh.shape.points[:]]
            #    #polygon, = plt.plot(x, y, 'o', markersize=30)
            #    #polygons.append(polygon)
            #    plt.title("Contours")
            #    plt.axis([0, width, height, 0])
            #    plt.plot(x, y, 'o', markersize=1)
                
            
            # shape.plot()
            # plt.show()


            plt.savefig("temp_directory/" + os.path.basename(file)[:index] + ".png", bbox_inches='tight')
         plt.close('all')
      fig = plt.figure()
      dir = Path("temp_directory")
      images = []
      for file in dir.glob('*.png'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         image = cv.imread(file_name)
         images.append([plt.imshow(image)])#, cmap='nipy_spectral')])
           
      print("Creating Animation")

      ani = animation.ArtistAnimation(fig, images, interval=100, blit=True,
                                    repeat_delay=1000)
      print("Saving Animation")
      ani.save(save_path + ".mp4")
      for file in dir.glob('*.png'):
         file_name = os.path.dirname(file) + "/" + os.path.basename(file)
         os.remove(file_name)
      os.rmdir("temp_directory")

         

def main():
   plt.rcParams['animation.ffmpeg_path'] = '/usr/bin/ffmpeg' # I need this for some reason?? Take out if it causes issues.
   cs = Contour2Shp()
   print("Notice: You can run all processes at once using Main.py. If you run scripts individually please note that this script is intended to run after ConnectedComp.py. If it is executed after a different script it will not work.")
   if len(sys.argv) < 2:
      print("Please enter the directory of the images you would like to compress and the new directory for the compressed images.")
   elif sys.argv[1].lower() == "shp" and len(sys.argv) == 4:
      cs.convert_npy_2_shp(sys.argv[2], sys.argv[3])
   elif sys.argv[1].lower() == "shp" and len(sys.argv) != 4:
      print("To convert images into contour shape files please enter: shp image_directory_to_apply save_directory")
   elif sys.argv[1].lower() == "view" and len(sys.argv) == 3:
      cs.view_shape_files(sys.argv[2])
   elif sys.argv[1].lower() == "view" and len(sys.argv) != 3:
      print("To view an image please enter: view image_directory")
   elif sys.argv[1].lower() == "vid" and len(sys.argv) == 4:
      cs.create_vid(sys.argv[2], sys.argv[3])
   elif sys.argv[1].lower() == "vid" and len(sys.argv) != 4:
      print("Warning: Currently does not work. To create a video please enter: vid apply_directory save_directory")
   elif sys.argv[1].lower() == "vidcont" and len(sys.argv) == 4:
      cs.create_contour_vid(sys.argv[2], sys.argv[3])
   elif sys.argv[1].lower() == "vidcont" and len(sys.argv) != 4:
      print("To create a video please enter: vid apply_directory save_directory")
   else:
      print("To convert images into contour shape files please enter: shp image_directory_to_apply save_directory")
      print("To view an image please enter: view image_directory")
      print("To create a video please enter: vid apply_directory save_directory")

if __name__ == "__main__":
   main()