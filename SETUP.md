# 环境配置指南

## 方法一：使用 Anaconda 创建虚拟环境（推荐）

### 1. 使用 environment.yml 创建环境

```bash
# 进入项目目录
cd /Users/ddxd/Repository/sim_renesas/garage_charging_robot

# 使用 environment.yml 创建环境
conda env create -f environment.yml

# 激活环境
conda activate garage_robot
```

### 2. 手动创建环境

如果网络不稳定，可以手动创建：

```bash
# 创建 Python 3.9 环境
conda create -n garage_robot python=3.9 -y

# 激活环境
conda activate garage_robot

# 安装依赖
pip install numpy matplotlib
```

### 3. 验证安装

```bash
# 激活环境后运行
python run_demo.py
```

---

## 方法二：使用 venv 创建虚拟环境

如果不使用 Anaconda：

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活环境（macOS/Linux）
source venv/bin/activate

# 激活环境（Windows）
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

---

## 依赖列表

项目依赖非常简单，只需要：
- Python 3.8+
- numpy
- matplotlib

---

## 快速测试

环境配置完成后，运行以下命令测试：

```bash
# 激活环境
conda activate garage_robot

# 运行演示
python run_demo.py

# 运行参数对比实验
python run_experiment.py

# 运行状态机演示
python run_with_state_machine.py
```

---

## 常见问题

### Q: conda 创建环境时网络超时怎么办？

**方案 1**: 使用国内镜像源

```bash
# 添加清华镜像源
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
conda config --add channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/
conda config --set show_channel_urls yes

# 再次尝试创建环境
conda env create -f environment.yml
```

**方案 2**: 离线安装

```bash
# 先创建空环境
conda create -n garage_robot python=3.9 --offline

# 激活后用 pip 安装
conda activate garage_robot
pip install numpy matplotlib
```

### Q: 如何删除环境？

```bash
# 退出环境
conda deactivate

# 删除环境
conda env remove -n garage_robot
```

### Q: 如何导出当前环境？

```bash
# 激活环境
conda activate garage_robot

# 导出环境配置
conda env export > environment_full.yml

# 或只导出 pip 依赖
pip freeze > requirements_full.txt
```

---

## 环境管理命令

```bash
# 查看所有环境
conda env list

# 激活环境
conda activate garage_robot

# 退出环境
conda deactivate

# 查看环境中的包
conda list

# 更新包
conda update numpy matplotlib
```

---

## IDE 配置

### VS Code

1. 打开项目文件夹
2. 按 `Cmd+Shift+P` (macOS) 或 `Ctrl+Shift+P` (Windows)
3. 输入 "Python: Select Interpreter"
4. 选择 `garage_robot` 环境

### PyCharm

1. File → Settings → Project → Python Interpreter
2. 点击齿轮图标 → Add
3. 选择 Conda Environment
4. 选择 Existing environment
5. 选择 `garage_robot` 环境

---

## 推荐的开发流程

```bash
# 1. 创建并激活环境
conda activate garage_robot

# 2. 开发和测试
python run_demo.py

# 3. 修改代码后重新测试
python run_demo.py

# 4. 完成后退出环境
conda deactivate
```

---

## 项目依赖说明

### numpy
- **用途**: 数值计算、矩阵运算
- **版本**: 任意（建议 >= 1.20）
- **核心功能**: 运动学计算、路径规划

### matplotlib
- **用途**: 数据可视化、绘图
- **版本**: 任意（建议 >= 3.3）
- **核心功能**: 结果可视化、性能分析图表

---

## 环境变量（可选）

如果需要自定义配置：

```bash
# 设置结果保存目录
export GARAGE_ROBOT_RESULTS_DIR="./results"

# 设置日志级别
export GARAGE_ROBOT_LOG_LEVEL="INFO"
```

---

祝您使用愉快！🚀
