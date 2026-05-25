
import scrapy
from gzc.items import GzcItem
from gzc.items import AjaxItem
from gzc.items import ParamItem
import re
import json
import logging

# ------------------ 日志配置 ------------------
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

class BjbPriceSpider(scrapy.Spider):
    name = "bjb_price"
    allowed_domains = ["detail.zol.com.cn"]
    start_urls = ["https://detail.zol.com.cn/notebook_index/subcate16_0_list_1_0_99_1_0_1.html"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items_count = 0          # 全局商品计数

    def parse(self, response):
        """
        获取主页面单商品url和进行翻页操作
        """
        # 提取当前页码（例如 _1.html）
        page_num = 1
        m = re.search(r'_(\d+)\.html$', response.url)
        if m:
            page_num = int(m.group(1))
        logger.info("当前模块为：parse | 正在处理第 %d 页", page_num)

        logger.debug("当前UA：%s", response.request.headers.get("User-Agent"))
        logger.info("response.status: %d", response.status)

        try:
            match = re.findall('<title>(.*?)</title>', response.text)
            if match and match[0] == "您正在进行防刷验证...":
                # 处理被反爬的情况
                logger.warning("疑似被反爬虫拦截，尝试更换UA或使用代理")
                logger.debug("响应内容（前200字符）：%s", response.text[:200])
            if not match:
                logger.warning("检查match，未找到title，响应前200字符：%s", response.text[:200])
        except Exception as e:
            logger.error("parse模块title提取异常: %s", e, exc_info=True)

        else:
            # 正常处理页面
            try:
                if response.status == 200:
                    list_box = response.css('div.content div.list-box div.list-item')
                    if list_box:
                        logger.info("本页抓取 %d 个商品", len(list_box))
                        for li in list_box:
                            self.items_count += 1
                            item = GzcItem()
                            item["link"] = response.urljoin(li.css('div.pro-intro h3 a::attr(href)').get())
                            item["name"] = li.css('div.pro-intro h3 a::text').get()
                            logger.info("进度：已准备抓取第 %d 个商品 -> %s", self.items_count, item["name"])
                            yield response.follow(item['link'], self.parse_shangpin_1_url)
                            yield item
                    else:
                        logger.error("请检查选择器，未找到 list-box")
                else:
                    logger.error("start_urls 状态码异常: %d", response.status)
            except Exception as e:
                logger.error("选择器有问题（模块：parse）: %s", e, exc_info=True)

            try:
                # 处理翻页逻辑
                next_text = response.css('div.page-box div.pagebar a.next::text').get()
                if next_text == "下一页":
                    next_href = response.css('div.page-box div.pagebar a.next::attr(href)').get()
                    logger.info("存在下一页，page=%d -> %s", page_num + 1, next_href)
                    yield response.follow(next_href, self.parse)
            except Exception as e:
                logger.error("parse模块翻页有问题: %s", e, exc_info=True)

    def parse_shangpin_1_url(self, response):
        logger.info("当前模块为：parse_shangpin_1_url")
        proId = mainId = seriesId = None

        try:
            script_text = response.xpath('//script[contains(., "_PRO_")]/text()').get()
            if script_text:
                proId_m = re.search(r'proId:\s*["\']?(\d+)["\']?', script_text)
                if proId_m:
                    proId = proId_m.group(1)
                mainId_m = re.search(r'mainId:\s*["\']?(\d+)["\']?', script_text)
                if mainId_m:
                    mainId = mainId_m.group(1)
                seriesId_m = re.search(r'seriesId:\s*["\']?(\d+)["\']?', script_text)
                if seriesId_m:
                    seriesId = seriesId_m.group(1)

                if proId:
                    Ajax_url = f"https://detail.zol.com.cn/xhr5_Product_GetProSkuInfo_proId={proId}.html"
                    logger.debug("Ajax_url: %s", Ajax_url)
                    yield response.follow(Ajax_url, self.parse_Ajax_url)
            else:
                ul_list = response.css('ul.nav__list.clearfix li')
                for ul in ul_list:
                    if ul.css('a::text').get() == "参数":
                        param_url = ul.css('a::attr(href)').get()
                        logger.info("未提取到script_text，直接跳转参数页: %s", param_url)
        except Exception as e:
            logger.error("parse_shangpin_1_url模块异常: %s", e, exc_info=True)

        # 如果缺少 proId/mainId/seriesId，尝试直接走参数页
        if not (proId or mainId or seriesId):
            name = response.css('div.breadcrumb span::text').get()
            price = response.css('div.price.price-normal span b.price-type::text').get()
            ul_list = response.css('ul.nav__list.clearfix li')
            for ul in ul_list:
                if ul.css('a::text').get() == "参数":
                    param_url = ul.css('a::attr(href)').get()
                    logger.info("（proId or mainId or seriesId）缺失，转向参数页: %s", param_url)
                    yield response.follow(param_url, self.parse_param_url)

    def parse_Ajax_url(self, response):
        logger.info("当前模块为：parse_Ajax_url")
        try:
            if response.status == 200:
                if response.text:
                    data = json.loads(response.text)
                    for item_data in data.get('list', []):
                        skuId = item_data.get('skuId')
                        price = item_data.get('price')
                        proUrl = item_data.get('proUrl')

                        yanse = None
                        banben = None
                        for param in item_data.get('params', []):
                            if param.get('specName') == '颜色':
                                yanse = param.get('itemName')
                            elif param.get('specName') == '版本':
                                banben = param.get('itemName')

                        item = AjaxItem()
                        item['skuId'] = skuId
                        item['price'] = price
                        item['proUrl'] = proUrl
                        item['yanse'] = yanse
                        item['banben'] = banben
                        link_url = f"https://detail.zol.com.cn{proUrl}?skuId={skuId}"
                        yield response.follow(link_url, self.parse_shangpin_2_url, cb_kwargs={'priceitem': item})
                        yield item
                else:
                    logger.warning('json_text 为 None')
        except Exception as e:
            logger.error("请求错误，status=%d, url=%s", response.status, response.url)
            logger.error("parse_Ajax_url 异常: %s", e, exc_info=True)

    def parse_shangpin_2_url(self, response, priceitem=None):
        logger.info("当前模块：parse_shangpin_2_url")
        try:
            if response.status == 200:
                try:
                    section_list = response.css('div.section div.section-content')
                    if section_list.css('a::text').get() == "查看完整参数":
                        param_url = section_list.css('a::attr(href)').get()
                        yield response.follow(param_url, self.parse_param_url,
                                              cb_kwargs={'priceitem': priceitem})
                except Exception as e:
                    logger.error("parse_shangpin_2_url 选择器异常: %s", e, exc_info=True)
        except Exception as e:
            logger.error("parse_shangpin_2_url 请求异常，status=%d, url=%s", response.status, response.url)
            logger.error("异常详情: %s", e, exc_info=True)

    def parse_param_url(self, response, priceitem=None):
        logger.info("当前模块：parse_param_url")
        try:
            if response.status == 200:
                try:
                    item = ParamItem()

                    # 1. 产品名称
                    title = response.css('div.product-model.page-title.clearfix h1::text').get()
                    if title:
                        item['product_name'] = title.replace("参数", "").strip()

                    # 2. 遍历参数行
                    rows = response.css('div.detailed-parameters table tr')
                    if not rows:
                        rows = response.css('div.detailed-parameters tr')

                    field_map = {
                        "产品型号": "product_model",
                        "上市时间": "launch_date",
                        "产品类型": "product_type",
                        "产品定位": "product_positioning",
                        "操作系统": "operating_system",
                        "CPU系列": "cpu_series",
                        "CPU型号": "cpu_model",
                        "最高睿频": "max_frequency",
                        "核心/线程数": "cores_threads",
                        "三级缓存": "l3_cache",
                        "核心代号": "core_codename",
                        "制程工艺": "process_technology",
                        "内存容量": "ram_capacity",
                        "内存类型": "ram_type",
                        "硬盘容量": "hdd_capacity",
                        "硬盘描述": "hdd_description",
                        "触控屏": "touch_screen",
                        "屏幕类型": "screen_type",
                        "屏幕尺寸": "screen_size",
                        "显示比例": "aspect_ratio",
                        "屏幕分辨率": "screen_resolution",
                        "屏幕刷新率": "refresh_rate",
                        "sRGB色域": "srgb_gamut",
                        "显卡类型": "gpu_type",
                        "显卡芯片": "gpu_chip",
                        "显存容量": "video_memory",
                        "显存类型": "memory_type",
                        "独显直连": "direct_gpu_connection",
                        "摄像头": "camera",
                        "音频系统": "audio_system",
                        "扬声器": "speaker",
                        "麦克风": "microphone",
                        "无线网卡": "wlan",
                        "有线网卡": "ethernet",
                        "蓝牙": "bluetooth",
                        "指取设备": "pointing_device",
                        "键盘描述": "keyboard_desc",
                        "指纹识别": "fingerprint_scanner",
                        "人脸识别": "face_recognition",
                        "电池类型": "battery_type",
                        "续航时间": "battery_life",
                        "电源适配器": "power_adapter",
                        "外壳材质": "chassis_material",
                        "外壳描述": "chassis_color",
                        "保修政策": "warranty_policy",
                        "质保时间": "warranty_period",
                    }

                    for row in rows:
                        th = row.css('th')
                        td = row.css('td')
                        if not th or not td:
                            continue

                        param_name = th.css('::text').get()
                        if not param_name or param_name.strip() == '':
                            param_name = th.css('span::text').get()
                        if not param_name:
                            continue
                        param_name = param_name.strip()

                        value = None
                        texts = td.css('::text').getall()
                        if texts:
                            value = ' '.join([t.strip() for t in texts if t.strip()])
                        if not value:
                            a_texts = td.css('a::text').getall()
                            if a_texts:
                                value = ' '.join([t.strip() for t in a_texts if t.strip()])
                        if not value:
                            value = td.xpath('normalize-space()').get()
                        if value:
                            value = ' '.join(value.split())

                        if param_name in field_map:
                            item[field_map[param_name]] = value

                    # 3. 电商报价处理
                    jd_price = response.css('tr:contains("电商报价") td .itemsub-b2c.red .red::text').get()
                    if jd_price:
                        item['jd_price'] = jd_price.strip()
                        full_price = response.css('tr:contains("电商报价") td ::text').get()
                        if full_price:
                            item['ecommerce_price'] = full_price.strip()
                    else:
                        jd_price_link = response.css('tr:contains("电商报价") td a.itemsub-b2c::text').get()
                        if jd_price_link:
                            item['ecommerce_price'] = jd_price_link.strip()

                    if not item.get('ecommerce_price') and priceitem and priceitem.get('price'):
                        item['ecommerce_price'] = priceitem['price']
                    elif not item.get('ecommerce_price'):
                        logger.debug("无电商报价，且priceitem未提供价格")

                    yield item
                except Exception as e:
                    logger.error("提取数据出现问题: %s", e, exc_info=True)
        except Exception as e:
            logger.error("请求出现问题，status=%d, url=%s", response.status, response.url)
            logger.error("异常: %s", e, exc_info=True)