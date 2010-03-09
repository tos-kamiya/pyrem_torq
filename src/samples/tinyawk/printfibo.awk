BEGIN {
    fiboTbl[0] = 0
    fiboTbl[1] = 1
    i = 2
    while (i < 10) {
        fiboTbl[i] = fiboTbl[i - 1] + fiboTbl[i - 2]
        i = i + 1
    }
    
    i = 0
    while (i < 10) {
        print fiboTbl[i]
        i = i + 1
    }
    
    if (fiboTbl[9] > 50)
        print "fibo(9) > 50"
    else
        print "fibo(9) <= 50"
}
