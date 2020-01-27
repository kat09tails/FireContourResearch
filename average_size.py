from pathlib import Path
import os
'''----------------------------------------
|   Created by Kathryn Reese               |
|   Class: Average Size                    |
|   Determines the average sizes of        |
|   Geotiff's and shp files.               |
|------------------------------------------|
'''
class average_size:
   def get_average(self, directory, num_images):
      dir = Path(directory)
      average_sz = 0
      num_files = 0
      units = "kb"
      img_num  = 0
      for file in dir.glob('*.shp*'):
         if(img_num < num_images):
            average_sz += os.path.getsize(file)
            num_files += 1
            img_num += 1

      for file in dir.glob('*.tif*'):
         if(img_num < num_images):
            average_sz += os.path.getsize(file)
            num_files += 1
            units = "gb"
            img_num += 1

      average_sz = average_sz / num_files
      if(units == "kb"):
         print(str(average_sz) + " bytes")
         kilobytes = average_sz / (2 ** 10)
         return str(kilobytes) + " kb", average_sz
      if(units == "gb"):
         print(str(average_sz) + " bytes")
         gigabytes = average_sz / (2 ** 30)
         return str(gigabytes) + " gb", average_sz


def main():
   avsz = average_size()
   gigabytes, byt = avsz.get_average("Original_Images", 200)
   kilabytes, byt2 = avsz.get_average("Applied_Images/Shape Files", 200)
   print(gigabytes)
   print(kilabytes)
   print(str(byt2/byt) + " bytes")


if __name__ == "__main__":
   main()