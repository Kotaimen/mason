import math


def human_size(size):

    """ Return a human readable byte size """

    if size <= 0:
        return '0'

    # Human readable names
    # 2^0 2^10 2^20 2^30 2^40 2^50 2^60
    units = ['B', 'KB', 'MB', 'GB', 'TB', 'LB', 'EB']

    # Calculate which unit shall use
    index = int(math.floor(math.log(size) / math.log(2) / 10))

    # Just use last unit if given size is too large
    if index > len(units) - 1:
        index = len(units) - 1

    # Calculate size in that unit
    denominator = 2 ** (index * 10)
    result = 1.0 * size / denominator
    remainder = size % denominator

    # If division is done without remainder, don't need precision
    if remainder == 0:
        precision = 0
    else:
        # Otherwise calculation precision so that no more than 3 digits is needed
        precision = 2 - int(math.floor(math.log10(result)))
    if precision < 0:
        precision = 0
    # Format result
    return ('%%.%df ' % precision) % result + units[index]
    #return '{:.{}f}{}'.format(result, precision , units[index])

def test():
    print human_size(0)
    print human_size(1023)
    print human_size(1024)
    print human_size(1025)
    print human_size(1024 * 1024 - 100)
    print human_size(1024 * 1024)
    print human_size(1024 * 1024 + 10204)

if __name__ == '__main__':
    test()
