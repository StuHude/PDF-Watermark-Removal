# 这是一个示例 Python 脚本。

# 按 Shift+F10 执行或将其替换为您的代码。
# 按 双击 Shift 在所有地方搜索类、文件、工具窗口、操作和设置。
import numpy as np

import cv2

font = cv2.FONT_HERSHEY_SIMPLEX

img = cv2.imread("./shuiyin.png")
lower_hsv = np.array([160, 160, 160])
upper_hsv = np.array([255, 255, 255])

mask = cv2.inRange(img,lower_hsv,upper_hsv)
mask = cv2.GaussianBlur(mask,(1,1),0)
for i in range(0,img.shape[0]):
  for j in range(0,img.shape[1]):
      if mask[i,j] == 255:
          img[i,j] = [255,255,255]
cv2.imwrite('res.jpg', img)
print('Done!')


