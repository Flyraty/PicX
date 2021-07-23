"""
图床迁移执行脚本，大致步骤如下
1. 读取配置文件指定的 markdown 文件父目录，递归搜索所有 markdown 文件。
    a. 默认不递归搜索，递归搜索请慎重，避免替换到非目标 markdown。
2. 遍历读取 markdown 文件，正则匹配图片链接 \!\[\]\(https://.*?\)。
    a. 如果没有匹配到，跳过该 markdown 文件
    b. 如果图片已经是阿里云 oss 链接，跳过该图片的迁移
3. 对匹配到的图片链接，下载到本地。
4. 调用阿里云 oss api 上传本地图片，并生成阿里云链接，正则替换原链接内容。删除本地图片，
5. 接收测试 flag，如果是测试处理，只会搜索到一篇带有图片链接的 markdown，并复制文件进行上述 2~4 步。
6. 需要注意的地方，请保证图片名称具有唯一性，否则可能会产生未知错误。
"""

import os
import re
import oss2
import requests
import hashlib
from lxml import etree

# 配置解析
config = {
    "is_test": False,  # 是否测试，默认打开
    "is_recursion": True,  # 是否递归搜索 markdown 文件，默认 False
    "is_md5": False,  # 是否使用链接 MD5 替换原始图片名称，默认 False。如果图片名称不具有唯一性，建议开启
    "is_bak": False,  # 是否开启备份。直接利用 sed 的备份特性，默认备份在执行目录，备份文件名为 xx_bak.md
    "source_area": "sinaimg.cn",  # 原始图床域名
    "oss_area": "oss-cn-beijing",  # 阿里云 oss 区域域名
    "oss_access_id": "",  # 阿里云 oss accessId
    "oss_access_key": "",  # 阿里云 oss accessKey
    "oss_bucket": "",  # 阿里云 oss bucket
    "oss_img_dir": "img",  # 阿里云 oss img 目录，默认是 img
    "source_dir": ""  # markdown 文件目录
}

is_test = config["is_test"]
is_recursion = config["is_recursion"]
is_md5 = config["is_md5"]
is_bak = config["is_bak"]
source_area = config["source_area"]
oss_area = config["oss_area"]
oss_access_id = config["oss_access_id"]
oss_access_key = config["oss_access_key"]
oss_bucket = config["oss_bucket"]
oss_img_dir = config["oss_img_dir"]
source_dir = config["source_dir"]


class MkFileHandler:
    def __init__(self):
        pass

    def get_mk_file_list(self):
        """
        :return: 包含图片链接的 markdown 文件列表
        """
        mk_files = []
        if is_test:
            all_dir_files = os.listdir(source_dir)
            for file in all_dir_files:
                mk_file = os.path.join(source_dir, file)
                if self.is_valid_mk(mk_file):
                    mk_files.append(mk_file)
                    break
        elif is_recursion:
            for main_dir, dirs, file_name_list in os.walk(source_dir):
                for file in file_name_list:
                    mk_file = os.path.join(main_dir, file)
                    if self.is_valid_mk(mk_file):
                        mk_files.append(mk_file)
        else:
            all_dir_files = os.listdir(source_dir)
            for file in all_dir_files:
                mk_file = os.path.join(source_dir, file)
                if self.is_valid_mk(mk_file):
                    mk_files.append(mk_file)
        return mk_files

    @staticmethod
    def is_valid_mk(mk_file):
        """
        :param mk_file: source_dir 下的文件或者目录
        :return: markdown 文件中是否存在图片
        """
        if mk_file.endswith("md"):
            if os.path.isfile(mk_file):
                with open(mk_file, "r+") as mk:
                    lines = "\n".join(mk.readlines())
            else:
                lines = ""
            # 检测 markdown 文件中
            if re.search("\!\[\]\(https://.*?\)|<img.*?>", lines):
                return True
        else:
            return False

    def get_img_list(self, mk_file):
        """
        :param mk_file: markdown 文件
        :return: markdown 文件中的图片信息二元组列表（img_mk, img_url, img_name）
        """
        res = []
        with open(mk_file, "r+") as mk:
            lines = "\n".join(mk.readlines())
        imgs = re.findall("\!\[\]\(https://.*?\)|<img.*?>", lines)
        for img_mk in imgs:
            if source_area in img_mk:
                img_url = re.sub(r'\!\[\]\(|', '', img_mk)[:-1]
                if '<img' in img_mk:
                    htree = etree.HTML(img_mk)
                    img_url = str(htree.xpath("//img/@src")[0])
                img_name = self.gen_img_name(img_url)
                res.append((img_mk, img_url, img_name))
        return res

    @staticmethod
    def gen_img_name(img_url):
        file_type = img_url.split(".")[-1]
        if not is_md5:
            return img_url.split("/")[-1]
        else:
            md5 = hashlib.md5()
            md5.update(img_url.encode("utf-8"))
            return f"{md5.hexdigest()}.{file_type}"

    @staticmethod
    def overwrite_mk_file(mk_file, source_url, des_url):
        """
        :param mk_file: markdown 文件
        :param source_url: 原始链接
        :param des_url: 替换链接
        :return:
        """
        if not is_bak:
            sed_cmd = f'sed -i "" "s#{source_url}#{des_url}#g" "{mk_file}"'
        else:
            sed_cmd = f'sed -i "_bak" "s#{source_url}#{des_url}#g" "{mk_file}"'
        os.popen(sed_cmd, 'w')


class OSSClient:
    def __init__(self):
        self.bucket = self.__connect()

    @staticmethod
    def __connect():
        """
        连接阿里云 oss bucket
        :return:
        """
        auth = oss2.Auth(access_key_id=oss_access_id, access_key_secret=oss_access_key)
        oss_host = f"http://{oss_area}.aliyuncs.com"
        bucket = oss2.Bucket(auth, oss_host, oss_bucket)
        return bucket

    def upload(self, img_url):
        """
        通过网络流上传图片
        :param img_url: 图片链接
        :return:
        """
        img = requests.get(img_url)
        img_name = img_url.split("/")[-1]
        img_path = os.path.join(oss_img_dir, img_name)
        self.bucket.put_object(img_path, img.content)

    def exists(self, img_name):
        """
        如果该图片已经在 oss 中，那么跳过上传，直接替换。
        :param img_name:
        :return:
        """
        img_path = os.path.join(oss_img_dir, img_name)
        return True if self.bucket.object_exists(img_path) else False

    @staticmethod
    def get_object_url(img_name):
        """
        获取文件外链
        :param img_name:
        :return:
        """
        return "https://{}.{}.aliyuncs.com/img/{}".format(oss_bucket, oss_area, img_name)


class MoveHandler:
    def __init__(self, mkh, oss):
        self.mkh = mkh
        self.oss = oss

    def execute(self):
        for mk_file in self.mkh.get_mk_file_list():
            print(f"正在迁移 {mk_file}")
            imgs = self.mkh.get_img_list(mk_file=mk_file)
            for img_mk, img_url, img_name in imgs:
                # 当 oss 中已经存在该图片时，跳过上传，直接替换
                if not self.oss.exists(img_name):
                    self.oss.upload(img_url)
                des_url = self.oss.get_object_url(img_name)
                self.mkh.overwrite_mk_file(mk_file, img_url, des_url)
        print(f"迁移完成")


if __name__ == '__main__':
    mkh = MkFileHandler()
    oss = OSSClient()
    mhl = MoveHandler(mkh, oss)
    mhl.execute()
