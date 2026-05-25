NeocitiesMG

> 使用API接口来管理文件，官网地址：<https://neocities.org/>
>

1. 克隆到本地后同步环境

   ```bash
   uv sync
   ```

2. 创建.env文件，示例：

   ```text
   NEOCITIES_BASE_URL=https://neocities.org/api
   NEOCITIES_USER=user@xxx.com
   NEOCITIES_PASS=123456
   NEOCITIES_REPO=D:\\HTML\\neocities
   ```

3. 运行脚本

   ```bash
   uv run main.py
   ```

