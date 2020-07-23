lambda days=0: [lib.datetime.datetime.fromtimestamp(lib.time.time() - 86400 * (i - days)  + lib.random.randint(-10000, 10000)).isoformat() + 'Z'
    for i in range(101, 0, -1)
]