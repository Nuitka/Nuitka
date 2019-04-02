#program to parse any greeting of the form <salutation>,<address>!

from pyparsing import Word, alphas

# nuitka-skip-unless-imports: Word, alphas

greet = Word(alphas) + "," + Word(alphas) + "!"
greeting = greet.parseString("Hello , World !")
print(greeting)

def good_parse():
	'''Test function to check if result of pyparse is a list'''
	assert type(greeting) == list
if __name__ == '__main__':
	good_parse()
