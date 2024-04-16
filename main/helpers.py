def reduce(function, array):
    value = function(array[0], array[1])

    for i in range(2, len(array)):
        value = function(value, array[i])

    return value
