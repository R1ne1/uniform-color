from osgeo import gdal
import numpy as np


def convert_uint16_to_uint8(input_file, output_file):
    # 打开输入影像
    dataset = gdal.Open(input_file)
    if dataset is None:
        print(f"无法打开影像 {input_file}")
        return

    # 获取影像信息
    cols = dataset.RasterXSize
    rows = dataset.RasterYSize
    bands = dataset.RasterCount
    geotransform = dataset.GetGeoTransform()
    projection = dataset.GetProjection()

    # 创建输出影像
    driver = gdal.GetDriverByName('GTiff')
    out_ds = driver.Create(output_file, cols, rows, bands, gdal.GDT_Byte)
    out_ds.SetGeoTransform(geotransform)
    out_ds.SetProjection(projection)

    # 逐波段处理并转换为uint8
    for b in range(1, bands + 1):
        band = dataset.GetRasterBand(b)
        data_uint16 = band.ReadAsArray()

        # 将 uint16 影像归一化为 0-255，避免数据截断
        data_uint8 = ((data_uint16 - data_uint16.min()) / (data_uint16.max() - data_uint16.min()) * 255).astype(
            np.uint8)

        # 写入输出影像
        out_band = out_ds.GetRasterBand(b)
        out_band.WriteArray(data_uint8)

        # 刷新缓存以确保数据写入
        out_band.FlushCache()

    # 关闭影像文件
    out_ds = None
    dataset = None
    print(f"转换完成，输出文件保存为 {output_file}")


# 使用示例
input_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879-MSS2.tiff"
output_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879\GF2_PMS2_E123.4_N41.8_20160529_L1A0001609879-MSS2_uint8.tiff"
# input_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663-MSS2.tiff"
# output_file = r"D:\Desktop\GF2示例数据\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663\GF2_PMS2_E123.9_N42.3_20170919_L1A0002610663-MSS2_uint8.tiff"

convert_uint16_to_uint8(input_file, output_file)
