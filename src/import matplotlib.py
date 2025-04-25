import matplotlib.pyplot as plt


def generate_history_chart(data, output_path):
    """
    生成协作能力历史趋势折线图（示例数据）。

    :param data:       列表，包含各时点的平均得分
    :param output_path: 图表保存路径，例如 'history_trend.png'
    """
    # 横坐标：1, 2, ..., len(data)
    x = list(range(1, len(data) + 1))

    plt.figure(figsize=(10, 6))
    plt.plot(x, data, marker='o', linestyle='-')

    # 设置标题与标签
    plt.title("Historical trend of collaborative ability", fontsize=14)
    plt.xlabel("data", fontsize=12)
    plt.ylabel("average score", fontsize=12)

    # 限制 y 轴范围
    plt.ylim(0, 5)

    # 设置 x 轴刻度
    plt.xticks(x)

    # 添加网格
    plt.grid(True, linestyle='--', alpha=0.6)

    # 在每个点上方标注数值
    for xi, yi in zip(x, data):
        plt.text(xi, yi + 0.1, f'{yi:.1f}', ha='center', va='bottom', fontsize=10)

    # 布局 & 保存
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


if __name__ == "__main__":
    # 示例数据
    data = [4.4, 3.2, 4.4, 3.8, 4.0, 3.9, 3.8, 4.2, 3.5, 3.9]
    save_path = "history_trend.png"
    generate_history_chart(data, save_path)
    print(f"折线图已保存到 {save_path}")
