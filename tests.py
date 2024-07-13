message = [1, 2, 3, 4, 0, 6]

print(message[4] if message[4] > 3 else message[0])
del_params = ['-', '0', '10', 'g', '9', 'c']
for i in range(len(del_params) - 1, -1, -1):
    if del_params[i].isdigit():
        continue
    del_params.pop(i)
print(del_params)
print('3 3 3 33  3'.split())
del_params = list(map(int, del_params))
print(del_params)