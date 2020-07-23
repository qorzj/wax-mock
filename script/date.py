lambda days=0: [lib.datetime.date.fromtimestamp(lib.time.time() - 86400 * (i - days)).isoformat()
    for i in range(101, 0, -1)
]