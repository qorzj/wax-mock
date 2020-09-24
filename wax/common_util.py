class SortedDict:
    def of(self, dict_data):
        ret = {}
        for key, val in sorted(dict_data.items()):
            ret[key] = val
        return ret

    def __matmul__(self, other):
        return self.of(other)

    def __rmatmul__(self, other):
        return self.of(other)


sorted_dict = SortedDict()
