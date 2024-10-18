from osgeo import gdal, gdalconst
import numpy as np

# 输入和参考影像路径
org_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879-MSS2_uint8.tiff"
ref_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663-MSS2_uint8.tiff"

# 打开影像
raster = gdal.Open(org_file)
ref_raster = gdal.Open(ref_file)
rows, cols = raster.RasterYSize, raster.RasterXSize
bands = raster.RasterCount
print(f"输入影像尺寸: {cols}x{rows}, 波段数: {bands}")

# 设置分块大小
bk_size = 512
num_w = int(np.ceil(cols / bk_size))
num_h = int(np.ceil(rows / bk_size))
print(f"分块数：宽度 {num_w}, 高度 {num_h}")

# Wallis 匀光参数初始化
eps = 1e-8
res_out = np.zeros((4, num_h, num_w, bands), dtype=float)  # 存储均值和标准差

# 计算每个块的灰度均值和标准差
for b in range(bands):
    img_band = raster.GetRasterBand(b + 1)
    ref_band = ref_raster.GetRasterBand(b + 1)

    for i in range(num_h):
        for j in range(num_w):
            x_off = min(j * bk_size, cols - bk_size)
            y_off = min(i * bk_size, rows - bk_size)

            img = img_band.ReadAsArray(x_off, y_off, bk_size, bk_size)
            ref = ref_band.ReadAsArray(x_off, y_off, bk_size, bk_size)

            res_out[0, i, j, b] = np.mean(img)  # mg
            res_out[1, i, j, b] = np.std(img)   # sg
            res_out[2, i, j, b] = np.mean(ref)  # mf
            res_out[3, i, j, b] = np.std(ref)   # sf

# 输出 Wallis 匀色结果
driver = gdal.GetDriverByName("GTiff")
out_ds = driver.Create("Wallis匀色结果new.tif", cols, rows, bands, gdal.GDT_Byte)

for b in range(bands):
    in_band = raster.GetRasterBand(b + 1)
    out_band = out_ds.GetRasterBand(b + 1)

    for i in range(num_h):
        for j in range(num_w):
            x_off = min(j * bk_size, cols - bk_size)
            y_off = min(i * bk_size, rows - bk_size)

            gx = in_band.ReadAsArray(x_off, y_off, bk_size, bk_size)
            mg = res_out[0, i, j, b]
            sg = res_out[1, i, j, b]
            mf = res_out[2, i, j, b]
            sf = res_out[3, i, j, b]

            # 计算 Wallis 匀色结果
            wallis = np.abs((gx - mg) * (sf / (sg + eps)) + mf)
            wallis = np.clip(wallis, 0, 255).astype(np.uint8)

            # 写入结果
            out_band.WriteArray(wallis, x_off, y_off)

        print(f"波段 {b + 1}，块 ({i + 1}, {j + 1}) 完成")

out_ds.FlushCache()
del out_ds
print("Wallis 匀光处理完成")
