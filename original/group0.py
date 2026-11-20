# Algorithms 2022/2023 group project - working copy from May 2023.
#
# This is the code as the group wrote it. The task descriptions that came
# with the course template (function docstrings and "TODO" markers) were
# removed, because that text belongs to the course staff; the README links
# to the original assignment. Nothing else was changed.
#
# The cleaned-up version is crypto_algorithms.py in the repository root.
from typing import Tuple, List, Dict

def read_file(file_path: str) -> any:

    lst = []
    with open(file_path, "r") as crypto_list:
      for i in crypto_list:
        line = i.strip().split(',') 
        for j in range(1,4):
          date = line[j]
          line[j] = float(date)
        lst.append(line)
      return lst


def crypto_stats(data, crypto_name: str, interval: Tuple[int, int]) -> Tuple[float, float, float]:
    start = interval[0]
    end = interval[-1] 
    prices =[]
    for i in data:
        if i[0] == crypto_name:
            if i[1] >= start and i[1] <= end:
                prices.append(i[2])
    minimum = min(prices)
    maximum = max(prices)
    average = sum(prices)/len(prices)
    result = (minimum, average, maximum)
    return result




def sort_data(data) -> List[Tuple[str, float]]:

    def merge_sort(arr, key):
      if len(arr) > 1:
        mid = len(arr) // 2
        left = arr[:mid]
        right = arr[mid:]

        merge_sort(left, key)
        merge_sort(right, key)

        i = j = k = 0
        while i < len(left) and j < len(right):
            if left[i][key] < right[j][key]:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            k += 1

        while i < len(left):
            arr[k] = left[i]
            i += 1
            k += 1

        while j < len(right):
            arr[k] = right[j]
            j += 1
            k += 1
    # Here we sort the list by the cryptocurrency name (first # then CAPS then normal)
    merge_sort(data, 0)

    # Here we sort each cryptocurrency by the day of monitoring
    sorted_data = []
    current_crypto = ''
    current_crypto_data = []
    for data in data:
        if current_crypto != data[0]:
            if current_crypto_data:
                # Sorting the data for the current cryptocurrency
                merge_sort(current_crypto_data, 1)
                sorted_data.extend([(item[0], item[2]) for item in current_crypto_data])
                current_crypto_data = []

            current_crypto = data[0]

        current_crypto_data.append(data)

    # Sort the last data for the last cryptocurrency
    merge_sort(current_crypto_data, 1)
    sorted_data.extend([(item[0], item[2]) for item in current_crypto_data])
    return sorted_data




def get_max_value(data, crypto: str, month: int) -> Tuple[int, float]:

    # Calculate the day range for the specified month
    month_start_day = (month - 1) * 30 + 1
    month_end_day = month * 30

    # Initialize maximum price and the corresponding day
    max_price = -1
    max_price_day = -1

    # Iterate through the list of lists
    for item in data:
        crypto_name, day_elapsed, opening_price, closing_price = item

        if crypto_name == crypto:
            # Check if the day_elapsed is within the specified month
            if month_start_day <= day_elapsed <= month_end_day:
                if opening_price > max_price:
                    max_price = opening_price
                    max_price_day = day_elapsed

    return (int(max_price_day), float(max_price))


   
   



def search(data, value: float, crypto: str) -> Tuple[int, float]:

    closest_day = -1
    closest_price = float('inf')
    min_difference = float('inf')

    for item in data:
        crypto_name, day_elapsed, opening_price, closing_price = item

        if crypto_name == crypto:
            # Calculate the difference between the target price and the opening price
            difference = abs(value - opening_price)

            # Update the closest price, closest day, and min_difference if the difference is smaller
            if difference < min_difference:
                min_difference = difference
                closest_price = opening_price
                closest_day = day_elapsed

    return (int(closest_day),float(closest_price))





def min_correlation_pathways(data,
                             crypto: str,
                             interval: Tuple[int,int]) -> Dict[str, List[str]]:
    
   
    # Preprocess the data into a nested dictionary
    data_preprocessed = {}
    for item in data:
        crypto_name, day_elapsed, opening_price, _ = item
        if interval[0] <= day_elapsed <= interval[1]:
            if crypto_name not in data_preprocessed:
                data_preprocessed[crypto_name] = {}
            data_preprocessed[crypto_name][day_elapsed] = opening_price

    # correlations
    cryptos = list(data_preprocessed.keys())
    correlations = {}
    for i in range(len(cryptos)):
        for j in range(i+1, len(cryptos)):
            crypto1, crypto2 = cryptos[i], cryptos[j]
            common_days = set(data_preprocessed[crypto1].keys()).intersection(data_preprocessed[crypto2].keys())
            prices1 = [data_preprocessed[crypto1][day] for day in common_days]
            prices2 = [data_preprocessed[crypto2][day] for day in common_days]
            correlation = pearson_corr(prices1, prices2)
            correlations[(crypto1, crypto2)] = correlation
            correlations[(crypto2, crypto1)] = correlation

    # Initialize the Minimum spanning tree and set of nodes in the MST
    mst = {crypto: {}}
    nodes_in_mst = {crypto}

    while len(nodes_in_mst) < len(cryptos):
        # Find the edge with the smallest weight that connects a node in the MST with a node not in the MST
        min_weight = float('inf')
        min_edge = None
        for node in nodes_in_mst:
            for other_node in cryptos:
                if other_node not in nodes_in_mst and correlations.get((node, other_node), float('inf')) < min_weight:
                    min_weight = correlations[(node, other_node)]
                    min_edge = (node, other_node)

        # Add the edge to the MST
        node, other_node = min_edge
        mst[node][other_node] = min_weight
        mst[other_node] = {}  # Initialize an empty dictionary for the other node
        nodes_in_mst.add(other_node)

    return mst

def pearson_corr(x: List[float], y: List[float]) -> float:
    n = len(x)
    sum_x = float(sum(x))
    sum_y = float(sum(y))
    sum_x_sq = sum(map(lambda x: pow(x, 2), x))
    sum_y_sq = sum(map(lambda x: pow(x, 2), y))
    psum = sum(map(lambda x, y: x * y, x, y))
    num = psum - (sum_x * sum_y/n)
    

    den_sq = (sum_x_sq - pow(sum_x, 2) / n) * (sum_y_sq - pow(sum_y, 2) / n)
    if den_sq < 0:
        return 0
    den = pow(den_sq, 0.5)
    
    if den == 0: 
        return 0
    return num / den


def correlated_cryptos_at_lvl_k(data,
                                crypto: str,
                                level: int,
                                interval: Tuple[int,int]) -> List[str]:

    # We generate correlation tree
    tree = min_correlation_pathways(data, crypto, interval)

    # Initialize BFS
    queue = [(crypto, 0)]  # (node, level)
    visited = {crypto}
    correlated_at_k = []

    # BFS
    while queue:
        node, lvl = queue.pop(0)

        if lvl == level:
            correlated_at_k.append(node)

        if lvl > level:
            break

        # Add neighbors to the queue
        for neighbor in tree[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, lvl + 1))

    # tree is equal to = min_correlation_pathways
    return (tree, correlated_at_k)