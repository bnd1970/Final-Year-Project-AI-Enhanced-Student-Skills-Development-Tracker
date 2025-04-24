            # 生成折线图
            plt.rcParams['font.sans-serif'] = ['NotoSansSC']
            plt.rcParams['axes.unicode_minus'] = False
            
            plt.figure(figsize=(10, 6))
            plt.plot(dates, avg_scores, marker='o', linestyle='-', color='#1890ff')
            
            # 图表装饰
            plt.title("协作能力历史趋势", fontsize=14)
            plt.xlabel("日期", fontsize=12)
            plt.ylabel("平均得分", fontsize=12)
            plt.ylim(0, 5)
            plt.grid(True, linestyle='--', alpha=0.6)
            
            # 添加数据标签
            for x, y in zip(dates, avg_scores):
                plt.text(x, y+0.1, f'{y:.1f}', ha='center', color='#2f4f4f')