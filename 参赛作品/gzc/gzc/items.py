# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class GzcItem(scrapy.Item):
    name = scrapy.Field()
    link = scrapy.Field()#shangpin_1_url
class AjaxItem(scrapy.Item):
    skuId=scrapy.Field()
    price=scrapy.Field()
    proUrl=scrapy.Field()
    yanse=scrapy.Field()
    banben=scrapy.Field()
class ParamItem(scrapy.Item):
    # 基本参数
    product_name = scrapy.Field()          # 产品名称
    product_model = scrapy.Field()         # 产品型号
    ecommerce_price = scrapy.Field()       # 电商报价
    jd_price = scrapy.Field()              # 京东价格
    launch_date = scrapy.Field()           # 上市时间
    product_type = scrapy.Field()          # 产品类型
    product_positioning = scrapy.Field()   # 产品定位
    operating_system = scrapy.Field()      # 操作系统

    # 处理器
    cpu_series = scrapy.Field()            # CPU系列
    cpu_model = scrapy.Field()             # CPU型号
    max_frequency = scrapy.Field()         # 最高睿频
    cores_threads = scrapy.Field()         # 核心/线程数
    l3_cache = scrapy.Field()              # 三级缓存
    core_codename = scrapy.Field()         # 核心代号
    process_technology = scrapy.Field()    # 制程工艺

    # 存储设备
    ram_capacity = scrapy.Field()          # 内存容量
    ram_type = scrapy.Field()              # 内存类型
    hdd_capacity = scrapy.Field()          # 硬盘容量
    hdd_description = scrapy.Field()       # 硬盘描述

    # 显示屏
    touch_screen = scrapy.Field()          # 触控屏
    screen_type = scrapy.Field()           # 屏幕类型
    screen_size = scrapy.Field()           # 屏幕尺寸
    aspect_ratio = scrapy.Field()          # 显示比例
    screen_resolution = scrapy.Field()     # 屏幕分辨率
    refresh_rate = scrapy.Field()          # 屏幕刷新率
    srgb_gamut = scrapy.Field()            # sRGB色域

    # 显卡
    gpu_type = scrapy.Field()              # 显卡类型
    gpu_chip = scrapy.Field()              # 显卡芯片
    video_memory = scrapy.Field()          # 显存容量
    memory_type = scrapy.Field()           # 显存类型
    direct_gpu_connection = scrapy.Field() # 独显直连

    # 多媒体设备
    camera = scrapy.Field()                # 摄像头
    audio_system = scrapy.Field()          # 音频系统
    speaker = scrapy.Field()               # 扬声器
    microphone = scrapy.Field()            # 麦克风

    # 网络通信
    wlan = scrapy.Field()                  # 无线网卡
    ethernet = scrapy.Field()              # 有线网卡
    bluetooth = scrapy.Field()             # 蓝牙

    # 输入设备
    pointing_device = scrapy.Field()       # 指取设备
    keyboard_desc = scrapy.Field()         # 键盘描述
    fingerprint_scanner = scrapy.Field()   # 指纹识别
    face_recognition = scrapy.Field()      # 人脸识别

    # 电源描述
    battery_type = scrapy.Field()          # 电池类型
    battery_life = scrapy.Field()          # 续航时间
    power_adapter = scrapy.Field()         # 电源适配器

    # 外观
    chassis_material = scrapy.Field()      # 外壳材质
    chassis_color = scrapy.Field()         # 外壳描述

    # 保修信息
    warranty_policy = scrapy.Field()       # 保修政策
    warranty_period = scrapy.Field()       # 质保时间
