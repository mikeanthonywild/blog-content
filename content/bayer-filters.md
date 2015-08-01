Title: Digital Image Processing: Bayer Filters
Date: 2015-07-26 21:41

A reasonable assumption of the image acquisition process in a modern digital camera would be that an array of photosensors have a 1:1 mapping to the output image, with each photosensor having red, green and blue components; in reality the process is a little more complex, with no simple mapping between input and output.

Most modern image sensors are based on the same design that [Eastman Kodak originally patented in 1975](http://www.google.com/patents/US3971065). As expected, the image sensor consists of a 2D array of photosensors. However, these photosensors are only able to detect the overall light intensity, they can't distinguish between different colours, this results in a monochrome image. Higher-end image sensors typically feature 12-bit or higher ADCs, resulting in a 2D matrix of light intensity values between 0 and 4,095.

To overcome the monochromatic nature of photosensors, a Colour Filter Array is placed in front of the sensor as illustrated in the diagram below.

![Colour Filter Array]({filename}/images/colour_filter_array.png)

*Image: Wikimedia Commons under GPL - https://en.wikipedia.org/wiki/File:Bayer_pattern_on_sensor.svg*

Each pixel of the filter aligns directly with the underlying photosensor, letting only a single band of light through. Bryce Bayer, the technique's original inventor, used two green pixels for every red and blue pixel, mimicking the distribution of receptors in the human eye. Knowing the exact Bayer pattern used, it's possible to generate a colour image from the light intensity data of each photosensor, resulting in the image below.

![Colour-coded Bayer Filter output]({filename}/images/bayer_output.png)

*Image: Wikimedia Commons under CC - https://upload.wikimedia.org/wikipedia/commons/d/de/Normal_and_Bayer_Filter_%28120px-Colorful_spring_garden%29.png*
