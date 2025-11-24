FROM python:3.10-slim

# 添加元数据标签
LABEL maintainer="coderxiu<coderxiu@qq.com>"
LABEL description="闲鱼AI客服机器人"
LABEL version="2.0"

# 设置时区和编码
ENV TZ=Asia/Shanghai \
    PYTHONIOENCODING=utf-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 创建时区目录和文件
RUN mkdir -p /usr/share/zoneinfo/Asia && \
    echo "CST-8" > /etc/timezone

# 设置工作目录
WORKDIR /app

# 复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

# 创建必要的目录
RUN mkdir -p data prompts

# 复制示例提示词文件并重命名为正式文件
COPY prompts/classify_prompt_example.txt prompts/classify_prompt.txt
COPY prompts/price_prompt_example.txt prompts/price_prompt.txt
COPY prompts/tech_prompt_example.txt prompts/tech_prompt.txt
COPY prompts/default_prompt_example.txt prompts/default_prompt.txt

# 复制所有必要的文件
COPY main.py XianyuAgent.py XianyuApis.py context_manager.py ./
COPY web_api.py web_admin_api.py start_web.py delivery_manager.py ./
COPY product_publisher.py product_prompt_manager.py publish_tool.py ./
COPY utils/ utils/
COPY static/ static/

# 容器启动时运行的命令
CMD ["python", "main.py"]
