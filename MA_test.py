import time

# Program to calculate moving average
arr = [1, 2, 3, 4, 5, 6, 7, 9, 10]
window_size = 5
 
i = 0
# Initialize an empty list to store moving averages
moving_averages = []
 

while i < len(arr) - window_size + 1: # Loop through the array to consider every window 
    window = arr[i : i + window_size] # Store elements from i to i+window_size in list to get the current window
    window_average = round(sum(window) / window_size, 2) # Calculate the average of current window
    print(window_average)
    i += 1 # Shift window to right by one position

print(wind_gusts(5.6))
