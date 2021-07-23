### PicX
图床迁移脚本工具（目前仅支持阿里云 oss）

#### 背景
一开始博客使用的是 ipic 提供的免费微博图床，虽然很方便，但是图片易受到微博的影响，一旦微博删除图片，博客的图片外链失效，又没有备份，对于想要长期维护的站点来说不是很友好，遂想迁移到阿里云 oss。
刚开始迁移使用的是 ipic mover，其提供一键迁移，自动扫描 markdown 文件，提取所有的 markdown 格式图片外链，交给 ipic 自动上传。但是存在如下问题：
- 不支持扫描 img 标签，对于博客相册和 html 文档不友好。
- 版本比较老，存在 bug，图片迁移不成功

上百篇的文档手动迁移会耗费大量时间，于是借助 ipic mover 的思路，自己实现了一个图片迁移脚本，自动将旧图床图片迁移到新图床，并且自动替换掉 markdown 文档中的旧链接。

#### 使用
- 按需修改 picx.py 中的 config 变量。
配置项
config	|Description	|Example|
|-------|-----------------------------------|---------|
| is_test| 是否测试，测试打开此项，只会处理一个 markdown 文件，方便查看效果与是否符合预期 | True\False |
| is_recursion| 是否递归搜索文件，如果目录层级不一样，可以打开此选项，用于搜索到所有需要迁移的 markdown | True\False |
| is_md5| 是否采用 MD5 生成新的图片名称，如果旧图床图片名称不具有唯一性，那么建议打开此选项，避免不同图片来回覆盖| True\False |
| is_bak| 是否备份原文件，打开此选项。只会在备份文件中替换链接，默认 xx.md.bak | True\False |
| source_area| 旧图床域名标识，不一定完整，但是要有标示性 | sinaimg.cn |
| oss_area| 新图床域名| oss-cn_beijing|
| oss_access_id| oss accessid | |
| oss_access_key| oss accesskey |
| oss_bucket| oss bucket| |
| oss_img_dir| oss 图片存储路径，默根目录下 img 目录| img |
| source_dir| markdown 文件所在的父目录| |

- 执行 picx.py

```python
python3 picx.py
```
- 测试
设置 config_map 中 is_test，is_bak 为 true，然后随便玩就行了
```python
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
```


#### feature
- 分离配置文件。
- 支持更多图床。
- web ui可视化界面，与 github pages 集成。

