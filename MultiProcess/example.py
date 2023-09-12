import os 
import math
from multiprocessing import Pool

CORENUM = 8

def func():
    print('===> This is a multiprocessing example!')

if __name__ == '__main__':

    pool = Pool(CORENUM) # define thread number
    inputPath = ''
    infile_list = []
    
    for home, dirs, files in os.walk(inputPath):
        for file in files:
            if not file.endswith(".png"):
                continue
            in_file = os.path.join(home, file)
            infile_list.append(in_file)

    infile_list = infile_list[:1000] # 1000 samples
    inputNum = len(infile_list)
    block = int(math.ceil(inputNum / CORENUM))

    ret_list = []
    for bn in range(0, inputNum, block):
        endpos = min(inputNum, bn+block)
        print('file [{}-{}] is training'.format(bn+1, endpos))
        ret = pool.apply_async(func=func, args=(infile_list[bn:endpos],))
        ret_list.append(ret)

    pool.close()
    pool.join()