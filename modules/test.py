def stockPairs(stocksProfit, target):
    # Write your code here

    if len(stocksProfit) == 0:
        return 0

    pairs = []
    for profits in reversed(stocksProfit):

        for profits_2 in stocksProfit:

            if (profits + profits_2) == target:

                new_pair = [profits, profits_2]
                new_pair.sort()
                pairs.append(new_pair)

        stocksProfit.pop()

    print(pairs)

    unique_pairs = []
    for pair in pairs:
        if pair not in unique_pairs:
            unique_pairs.append(pair)

    return len(unique_pairs)


def performOperations(arr, operations):
    # Write your code here

    for operation in operations:

        arr_slice = arr[operation[0]:operation[1]+1]
        revers_arr = list(reversed(arr_slice))

        t = arr[operation[1]+1:]
        print(t)
        arr = arr[0:operation[0]] + revers_arr + arr[operation[1]+1:]

    return arr


t = [1, 2, 3]

op = [[0, 2], [1, 2], [0, 2]]

print(performOperations(t, op))
