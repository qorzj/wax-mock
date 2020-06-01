lambda ret, request: (lambda page, limit: {
    "pageNum": page,
    "pageSize": limit,
    "size": len(ret[(page - 1) * limit: page * limit]),
    "startRow": (page - 1) * limit + 1,
    "endRow": min(page * limit, len(ret)),
    "total": len(ret),
    "pages": max((len(ret) - 1) // limit, 0) + 1,
    "list": ret[(page - 1) * limit : page * limit]
})(int(request.get_input('page') or '1'), int(request.get_input('limit') or '10'))