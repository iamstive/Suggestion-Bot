args = list(map(str, ".split()))
dargs = {}
for i in args:
    if i not in dargs:
        dargs[i] = args.count(i)

print(dargs)