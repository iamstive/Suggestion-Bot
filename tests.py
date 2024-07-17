args = ['-1', 'aaa', '', '3', '10', '-9', '5', '6', '10', '15', '7']

print(sorted(int(i) for i in set(args) if i.isdigit()))
