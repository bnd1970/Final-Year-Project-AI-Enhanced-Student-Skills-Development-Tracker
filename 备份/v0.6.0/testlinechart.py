import matplotlib.pyplot as plt
import numpy as np

# Sample data (You can modify this with your own data)
dates = ['04-01', '04-02', '04-03', '04-04', '04-05', '04-06', '04-07']
discussion_participation = [4, 3.5, 4.5, 5, 4, 4.5, 4]
contribution_proposal = [3.5, 3, 4, 4.5, 4, 4.5, 5]
problem_solving = [4, 4.5, 4, 3.5, 4, 4, 4.5]
coordination_ability = [3, 3.5, 4, 4, 4.5, 4, 4.5]
response_timeliness = [4, 4.5, 4, 3.5, 4, 4.5, 5]

# Create a plot
plt.figure(figsize=(10, 5))

# Plot each criterion
plt.plot(dates, discussion_participation, marker='o', label='Discussion participation frequency', color='b')
plt.plot(dates, contribution_proposal, marker='o', label='Unsolicited contribution proposal', color='orange')
plt.plot(dates, problem_solving, marker='o', label='Problem solving ability', color='green')
plt.plot(dates, coordination_ability, marker='o', label='Team coordination ability', color='red')
plt.plot(dates, response_timeliness, marker='o', label='Response timeliness', color='purple')

# Customize the plot
plt.title("Collaboration Ability Scores Over Time")
plt.xlabel("Date")
plt.ylabel("Score")
plt.legend(loc='upper left')
plt.grid(True)

# Set y-axis limits and ticks
plt.ylim(0, 5)  # Limit the y-axis to range from 0 to 5
plt.yticks(np.arange(0, 6, 1))  # Set y-axis ticks at 0, 1, 2, 3, 4, 5


# Display the plot
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
