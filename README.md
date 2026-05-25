NeocitiesMG

> 使用API接口来管理文件
>
> 官网地址：<https://neocities.org/>

1. 克隆到本地后创建.env文件，内容示例：

   ```text
   NEOCITIES_BASE_URL=https://neocities.org/api
   NEOCITIES_USER=user@xxx.com
   NEOCITIES_PASS=123456
   NEOCITIES_REPO=D:\\HTML\\neocities
   ```

2. 推荐uv来管理

   ```bash
   uv sync
   ```

3. 运行脚本

   ```bash
   uv run main.py
   ```

