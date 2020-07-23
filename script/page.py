lambda ret, request: (lambda lst, page, limit: {
    "pageNum": page,
    "pageSize": limit,
    "size": len(lst[(page - 1) * limit: page * limit]),
    "startRow": (page - 1) * limit + 1,
    "endRow": min(page * limit, len(lst)),
    "total": len(lst),
    "pages": max((len(lst) - 1) // limit, 0) + 1,
    "list": lst[(page - 1) * limit : page * limit]
})(list(ret), int(request.get_input('page') or '1'), int(request.get_input('limit') or '10'))