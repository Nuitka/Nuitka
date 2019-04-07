import pandas as pd
# nuitka-skip-unless-imports: pandas
s = pd.Series([1,2,3,4,5],index = ['a','b','c','d','e'])
assert s[1]
'''
s = pd.Series([1,2,3,4,5],index = ['a','b','c','d','e'])
print s[1]
o/p:-
2
''' 