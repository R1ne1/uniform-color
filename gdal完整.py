import cv2
import numpy as np
from osgeo import gdal
import matplotlib.pyplot as plt

# 文件路径
org_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879-MSS2_uint8.tiff"
ref_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663-MSS2_uint8.tiff"

# 读取影像
def read_tiff(file_path):
    dataset = gdal.Open(file_path)
    img = dataset.ReadAsArray().transpose((1, 2, 0))  # 转置为 (height, width, bands)
    return img

img_org = read_tiff(org_file)
infer_img = read_tiff(ref_file)
height, width, bands = img_org.shape

# 计算变异系数 (CV)
cv_org = np.std(img_org) / np.mean(img_org)
cv_ref = np.std(infer_img) / np.mean(infer_img)
r = cv_org / cv_ref

# 确定块大小
num = int(np.ceil(8 * r))
w = int(np.ceil(width / num))
h = int(np.ceil(height / num))

# 预分配均值和标准差数组
mg = np.zeros((num, num, bands), dtype=np.float32)
mf = np.zeros_like(mg)
sg = np.zeros_like(mg)
sf = np.zeros_like(mg)

# 计算块状统计
for b in range(bands):
    for i in range(num):
        for j in range(num):
            origin_x = min(i * w, width - w)
            origin_y = min(j * h, height - h)
            end_x = origin_x + w
            end_y = origin_y + h

            img_block = img_org[origin_x:end_x, origin_y:end_y, b]
            ref_block = infer_img[origin_x:end_x, origin_y:end_y, b]

            mg[i, j, b] = np.mean(img_block)
            sg[i, j, b] = np.std(img_block)
            mf[i, j, b] = np.mean(ref_block)
            sf[i, j, b] = np.std(ref_block)

# Wallis 滤波器应用
eps = 1e-8
wallisImg = np.zeros_like(img_org)

for b in range(bands):
    mg_res = cv2.resize(mg[:, :, b], (width, height), interpolation=cv2.INTER_LINEAR)
    mf_res = cv2.resize(mf[:, :, b], (width, height), interpolation=cv2.INTER_LINEAR)
    sf_res = cv2.resize(sf[:, :, b], (width, height), interpolation=cv2.INTER_LINEAR)
    sg_res = cv2.resize(sg[:, :, b], (width, height), interpolation=cv2.INTER_LINEAR)

    band_i = (img_org[:, :, b] - mg_res) * (sf_res / (sg_res + eps)) + mf_res
    wallisImg[:, :, b] = np.clip(band_i, 0, 255).astype(np.uint8)

# 使用 GDAL 保存结果
def save_tiff_gdal(filename, img_data):
    height, width, bands = img_data.shape
    driver = gdal.GetDriverByName('GTiff')
    output_dataset = driver.Create(filename, width, height, bands, gdal.GDT_Byte)

    # 写入每个波段
    for b in range(bands):
        output_dataset.GetRasterBand(b + 1).WriteArray(img_data[:, :, b])

    # 关闭数据集
    output_dataset = None

# 保存 Wallis 归一化后的影像
save_tiff_gdal(r"waillisww2.tif", wallisImg)

# 显示影像
plt.figure(figsize=(15, 5))
plt.subplot(1, 3, 1)
plt.imshow(cv2.cvtColor(img_org, cv2.COLOR_BGR2RGB))
plt.title("Original Image")

plt.subplot(1, 3, 2)
plt.imshow(cv2.cvtColor(infer_img, cv2.COLOR_BGR2RGB))
plt.title("Reference Image")

plt.subplot(1, 3, 3)
plt.imshow(cv2.cvtColor(wallisImg, cv2.COLOR_BGR2RGB))
plt.title("Wallis Normalized Image")

plt.show()

