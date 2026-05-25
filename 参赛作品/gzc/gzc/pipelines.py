# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import pymysql
from gzc.items import GzcItem, AjaxItem, ParamItem
class GzcPipeline:
    def open_spider(self,spider):
        db_config = spider.settings.get('DB_CONFIG', {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'db': 'data',
            'charset': 'utf8mb4',
        })
        self.conn = pymysql.connect(**db_config)
        self.cursor = self.conn.cursor()
        # 创建表（如果不存在）
        self._create_tables()

    def _create_tables(self):
        # GzcItem 表：列表页商品
        sql_gzc = '''
        CREATE TABLE IF NOT EXISTS gzc_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            link VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
        # AjaxItem 表：SKU 信息
        sql_ajax = '''
        CREATE TABLE IF NOT EXISTS ajax_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            skuId VARCHAR(50) NOT NULL,
            price VARCHAR(50),
            proUrl VARCHAR(500),
            yanse VARCHAR(100),
            banben VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_skuId (skuId)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
        # ParamItem 表：详细参数
        # 这里动态创建表，字段较多，使用 ParamItem 的所有字段
        # 注意：字段名使用英文（与 item 中字段一致），类型统一为 TEXT
        param_fields = [
            ('product_name', 'VARCHAR(255)'),
            ('product_model', 'VARCHAR(255)'),
            ('ecommerce_price', 'VARCHAR(100)'),
            ('jd_price', 'VARCHAR(100)'),
            ('launch_date', 'VARCHAR(50)'),
            ('product_type', 'VARCHAR(100)'),
            ('product_positioning', 'VARCHAR(255)'),
            ('operating_system', 'VARCHAR(255)'),
            ('cpu_series', 'VARCHAR(100)'),
            ('cpu_model', 'VARCHAR(100)'),
            ('max_frequency', 'VARCHAR(50)'),
            ('cores_threads', 'VARCHAR(50)'),
            ('l3_cache', 'VARCHAR(50)'),
            ('core_codename', 'VARCHAR(100)'),
            ('process_technology', 'VARCHAR(100)'),
            ('ram_capacity', 'VARCHAR(50)'),
            ('ram_type', 'VARCHAR(50)'),
            ('hdd_capacity', 'VARCHAR(50)'),
            ('hdd_description', 'VARCHAR(255)'),
            ('touch_screen', 'VARCHAR(50)'),
            ('screen_type', 'VARCHAR(50)'),
            ('screen_size', 'VARCHAR(50)'),
            ('aspect_ratio', 'VARCHAR(50)'),
            ('screen_resolution', 'VARCHAR(50)'),
            ('refresh_rate', 'VARCHAR(50)'),
            ('srgb_gamut', 'VARCHAR(50)'),
            ('gpu_type', 'VARCHAR(100)'),
            ('gpu_chip', 'VARCHAR(100)'),
            ('video_memory', 'VARCHAR(50)'),
            ('memory_type', 'VARCHAR(50)'),
            ('direct_gpu_connection', 'VARCHAR(50)'),
            ('camera', 'VARCHAR(100)'),
            ('audio_system', 'VARCHAR(100)'),
            ('speaker', 'VARCHAR(100)'),
            ('microphone', 'VARCHAR(100)'),
            ('wlan', 'VARCHAR(255)'),
            ('ethernet', 'VARCHAR(100)'),
            ('bluetooth', 'VARCHAR(100)'),
            ('pointing_device', 'VARCHAR(100)'),
            ('keyboard_desc', 'VARCHAR(255)'),
            ('fingerprint_scanner', 'VARCHAR(50)'),
            ('face_recognition', 'VARCHAR(50)'),
            ('battery_type', 'VARCHAR(100)'),
            ('battery_life', 'VARCHAR(100)'),
            ('power_adapter', 'VARCHAR(255)'),
            ('chassis_material', 'VARCHAR(100)'),
            ('chassis_color', 'VARCHAR(100)'),
            ('warranty_policy', 'VARCHAR(255)'),
            ('warranty_period', 'VARCHAR(50)'),
        ]
        columns = ', '.join([f'`{col}` {type_}' for col, type_ in param_fields])
        sql_param = f'''
        CREATE TABLE IF NOT EXISTS param_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            {columns},
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uk_product_model (product_model)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        '''
        self.cursor.execute(sql_gzc)
        self.cursor.execute(sql_ajax)
        self.cursor.execute(sql_param)
        self.conn.commit()

    def process_item(self, item):
        if isinstance(item, GzcItem):
            sql = "INSERT INTO gzc_items (name, link) VALUES (%s, %s)"
            self.cursor.execute(sql, (item.get('name'), item.get('link')))
        elif isinstance(item, AjaxItem):
            sql = """
                INSERT INTO ajax_items (skuId, price, proUrl, yanse, banben)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                price = VALUES(price),
                proUrl = VALUES(proUrl),
                yanse = VALUES(yanse),
                banben = VALUES(banben)
            """
            self.cursor.execute(sql, (
                item.get('skuId'), item.get('price'),
                item.get('proUrl'), item.get('yanse'), item.get('banben')
            ))
        elif isinstance(item, ParamItem):
            # 动态构建 INSERT 语句
            # 获取 item 中所有非 None 的字段
            fields = []
            values = []
            for key, val in item.items():
                if val is not None:
                    fields.append(key)
                    values.append(val)
            if fields:
                placeholders = ', '.join(['%s'] * len(fields))
                columns = ', '.join([f'`{f}`' for f in fields])
                sql = f"INSERT INTO param_items ({columns}) VALUES ({placeholders})"
                # 使用 ON DUPLICATE KEY UPDATE 防止 product_model 重复（如果设置了唯一键）
                # 简单起见，先尝试插入，若重复则更新
                try:
                    self.cursor.execute(sql, values)
                except pymysql.IntegrityError:
                    # 如果 product_model 重复，执行更新操作
                    update_parts = [f'`{f}` = %s' for f in fields if f != 'product_model']
                    update_values = [item.get(f) for f in fields if f != 'product_model']
                    if update_parts:
                        update_sql = f"""
                            UPDATE param_items
                            SET {', '.join(update_parts)}
                            WHERE `product_model` = %s
                        """
                        self.cursor.execute(update_sql, update_values + [item.get('product_model')])
        else:
            spider.logger.warning(f"Unknown item type: {type(item)}")
        self.conn.commit()
        return item

    def close_spider(self,spider):
        self.cursor.close()
        self.conn.close()