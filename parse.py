from Queue import Queue
from random import randint

flag_SLR = True
shift_reduce = False
reduce_reduce = False

def parse_grammar(file_name):
	
	global start
	global non_terminals
	global terminals

	with open(file_name,"r") as f:
		lines = f.readlines()
	
	productions = dict()
	first_time = True
	for i in lines:
		i = i.strip('\n')
		production = i.split(":=")
		lhs = production[0]
		rhs = production[1]
		if lhs not in non_terminals:
			non_terminals.append(lhs)
		for i in rhs.split('|'):
			for j in i:
				if j not in terminals and not j.isupper():
					terminals.append(j)

		if first_time:
			start = lhs
			first_time = False
		if '|' in rhs:
			productions[lhs] = rhs.split('|')
		else:
			productions[lhs] = list()
			productions[lhs].append(rhs)

	char = chr(randint(65,90))
	while char in non_terminals:
		char = chr(randint(65,90))
	augment = {char:[start+'~']}
	productions = dict(productions.items() + augment.items())
	start = char
	non_terminals.append(char)
	terminals.append('~')
	return productions

def compute_nullable(productions):

	old_nullable = dict()
	new_nullable = dict()
	
	for non_terminal in productions:
			old_nullable[non_terminal] = False
			new_nullable[non_terminal] = False
	
	first_time = True

	while old_nullable != new_nullable or first_time:
		old_nullable = new_nullable.copy()
		for non_terminal in productions:
			null = False
			for rhs in productions[non_terminal]:
				for i,j in enumerate(rhs):
					if not j.isupper() and j != '$':
						null = False
						break
					elif j == '$':
						null = True 
					elif j.isupper() and old_nullable[j]:
						null = True
					else:
						null = False
			new_nullable[non_terminal] = null
		first_time = False
	
	return new_nullable 

def compute_first(productions, nullable):
	oldfirst = dict()
	newfirst = dict()
	first = dict()
	for lhs in productions:
		oldfirst[lhs]= str()
		newfirst[lhs]= str()
	first_time = True
	while (oldfirst!=newfirst or first_time):
		oldfirst = newfirst.copy()
		first_time = False
		for lhs in productions:
			for rhs in productions[lhs]:
				for i in rhs:
					if not i.isupper() and i!='$':
						if i not in newfirst[lhs]:
							newfirst[lhs] = newfirst[lhs] + i
						break
					elif i.isupper() and i!='$':
						for c in newfirst[i]:
							if c not in newfirst[lhs]:
								newfirst[lhs] = newfirst[lhs] + c
						if nullable[i]:
							pass
						else:
							break
	for i,j in oldfirst.iteritems():
		first[i] = list(j)
	return first


def compute_follow(productions,first, nullable):
	old_follow = dict()
	cur_follow = dict()
	for non_terminal in productions:
		old_follow[non_terminal] = list()
		cur_follow[non_terminal] = list()

	first_time = True
	while old_follow != cur_follow or first_time:
		old_follow = dict(cur_follow)
		for non_terminal in productions:
			for rhs in productions[non_terminal]:
				temp = -1
				while abs(temp)<=len(rhs) and rhs[temp].isupper() and nullable[rhs[temp]]:
					cur_follow[rhs[temp]] = cur_follow[rhs[temp]] + old_follow[non_terminal]
					temp -= 1
				if abs(temp)<=len(rhs) and rhs[temp].isupper():
					cur_follow[rhs[temp]] = cur_follow[rhs[temp]] + old_follow[non_terminal]
				for j,k in enumerate(rhs):
					if k.isupper():
						if (j+1)<len(rhs) and not rhs[j+1].isupper() and rhs[j+1] not in cur_follow[k]:
							cur_follow[k].append(rhs[j+1])
						elif (j+1)<len(rhs) and rhs[j+1].isupper():
							temp = j+1
							while temp<len(rhs) and rhs[temp].isupper() and nullable[rhs[temp]]:
								cur_follow[k] += first[rhs[temp]]
								temp += 1
							if temp<len(rhs) and not rhs[temp].isupper() and rhs[temp] not in cur_follow[k]:
								cur_follow[k].append(rhs[temp])
							if temp<len(rhs) and rhs[temp].isupper():
								cur_follow[k] += first[rhs[temp]]

		for non_terminal in cur_follow:
			cur_follow[non_terminal] = list(set(cur_follow[non_terminal]))

		for non_terminal in old_follow:
			old_follow[non_terminal] = list(set(old_follow[non_terminal]))

		first_time = False

	return cur_follow

def generate_productions():
	global productions
	productions_tuple = list()
	for lhs in productions:
		for rhs in productions[lhs]:
			productions_tuple.append((lhs,rhs))

	return productions_tuple


class state:

	def __init__(self):
		self.productions = dict()
		self.transitions = dict()

	def assign_number(self,number):
		self.number = number

	def get_number(self):
		return self.number

	def add_production(self, production):
		global productions

		(lhs, rhs_list) = production.items()[0]
		flag = True
		if lhs in self.productions:
			for i in rhs_list:
				if i not in self.productions[lhs]:
					flag = False
			if not flag:
				self.productions[lhs] = self.productions[lhs] + rhs_list
				self.productions[lhs] = list(set(self.productions[lhs]))
		else:
			flag = False
			self.productions = dict( self.productions.items() + production.items() )

		if flag:
			return

		for rhs in rhs_list:
			if rhs.split('.')[1] != '':
				next_char = rhs.split('.')[1][0]
				if next_char.isupper():
					to_add = list()
					for i in productions[next_char]:
						to_add.append('.'+i)
					self.add_production({ next_char:to_add })

	def update_transition(self,transition,state):
		self.transitions[transition] = state

	def __eq__(self,state):
		equal = True
		if self.productions.items() != state.productions.items():
			equal = False
		return equal

	def print_state(self):
		print "State",self.number
		for lhs,rhs in self.productions.iteritems():
			print lhs+':='+'|'.join(rhs)
		if self.transitions:
			print "Transitions :"
			for i,j in self.transitions.iteritems():
				print i,j
		print

	def get_reduce(self):
		red = dict()

		for lhs,rhs in self.productions.iteritems():
			for rule in rhs:
				if(rule[-1]=='.'):
					for tupl in productions_tuple:
						if (lhs,rule[:-1]) == tupl:
							for follow_lhs in follow[lhs]:
								red[follow_lhs]='r'+str(productions_tuple.index(tupl))
					if(rule[-2]=="~"):
						red["~"]="A"

		return red

class dfa:
	
	def __init__(self):
		self.states = list()
		self.queue = Queue(20)

	def print_dfa(self):
		for i in self.states:
			i.print_state()

	def construct(self):
		#to construct the dfa

		global productions
		global start

		state_count = 0
		zero_state = state()
		production = dict()
		production[start] = list()

		#constructing zero state
		for rhs in productions[start]:
			production[start].append('.'+rhs)
		zero_state.add_production(production)
		zero_state.assign_number(state_count)
		state_count = state_count + 1

		self.queue.put(zero_state)
		while not self.queue.empty():
			cur_state = self.queue.get()
			self.states.append(cur_state)
			#get a state off the queue and comput transitions
			to_do = compute_transitions(cur_state)
			for i,j in to_do.iteritems():
				#check if a state is already there
				flag = False
				for k in self.states:
					if j == k:
						flag = True
						cur_state.update_transition(i,k.get_number())
				for k in range(self.queue.qsize()):
					temp = self.queue.get()
					if j == temp:
						flag = True
						cur_state.update_transition(i,temp.get_number())
					self.queue.put(temp)
				#if not assign number and add to queue
				if not flag:
					j.assign_number(state_count)
					cur_state.update_transition(i,state_count)
					state_count = state_count + 1
					self.queue.put(j)

def compute_transitions(cur_state):
	#takes a state and returns a dictionary
	#the key in the dictionary is the transition character
	#value is the state to which the transition is to be done

	transitions = dict()
	computed_transitions = list()
	for lhs in cur_state.productions:
		for rhs in cur_state.productions[lhs]:
			index = rhs.index('.')
			if rhs.split('.')[1] != '' and rhs.split('.')[1] != '$':
				next_char = rhs.split('.')[1][0]
				#find the character for transition and check all the productions
				#in the state to find a similar production
				#Eg: A-> .B|.d
				#    C-> .D|.d
				# both the procudtions have a transition with d which is takken care of

				if next_char not in computed_transitions:
					#add to the computed_transitions the characters through which 
					#transitions are taken care of

					computed_transitions.append(next_char)
					
					#moving the '.' in the producton
					temp = rhs.replace('.','')
					rhs = temp[:index+1]+'.'+temp[index+1:]

					#create a temporary state and add all the productions
					#after moving the '.'
					transition_state = state()
					transition_state.add_production({lhs:[rhs]})
					to_add =  similar_productions(next_char,cur_state)
					for i,j in to_add.iteritems(): 
						transition_state.add_production({i:j})
					transitions[next_char] = transition_state
	return transitions

def similar_productions(next_char, state):
	#iterates through the productions in the state to find those which 
	#have a transition with next_char

	productions = dict()
	for lhs in state.productions:
		for rhs in state.productions[lhs]:
			index = rhs.index('.')
			if rhs.split('.')[1] != '':
				n_c = rhs.split('.')[1][0]
				if n_c == next_char:
					#transition found store it after moving the dot
					temp = rhs.replace('.','')
					rhs = temp[:index+1]+'.'+temp[index+1:]
					if lhs in productions:
						productions[lhs] = list(set(productions[lhs]+[rhs]))
					else:
						productions[lhs] = [rhs]
	return productions

def print_prod():
	num = 0
	for tupl in productions_tuple:
		print num,
		(lhs,rhs) = tupl
		print lhs+':='+rhs
		num = num + 1


def generate_table(dfa):
	global start
	global flag_SLR
	global shift_reduce
	global reduce_reduce
	print "start",start 
	table = list()
	num = 0
	for state in dfa.states:
		table.append(dict())
		num = num +1
	for state in dfa.states:
		ls = list()
		lr = list()
		for lhs,rhs in state.transitions.iteritems():
			if lhs.isupper():
				table[state.number][lhs]='g'+str(rhs)
			else:
				table[state.number][lhs]='s'+str(rhs)
				ls.append(lhs)
		perform_reduce = state.get_reduce()
		for lhs,rhs in perform_reduce.iteritems():		
			if lhs not in ls and lhs not in lr:
				table[state.number][lhs]=rhs
				lr.append(lhs)
			elif lhs in ls:
				shift_reduce = True
				flag_SLR  = False
			else:
				reduce_reduce = True
				flag_SLR = False

	return table

def print_table(table):
	global terminals
	global non_terminals
	print "Parsing table"
	print "\t",
	for non_terminal in non_terminals:
		print non_terminal,"\t",
	for terminal in terminals:
		print terminal,"\t",
	print
	for index,state in enumerate(table):
		print index,"\t",
		for i in non_terminals:
			if i in state:
				print state[i],"\t",
			else:
				print "\t",
		for i in terminals:
			if i in state:
				print state[i],"\t",
			else:
				print "\t",
		print


def parse(table,input_string):
	error = False
	accept = False
	stack = list()
	stack.append("~")
	stack.append("0")
	input_string = input_string + "~"
	input_string = list(input_string)
	print "Stack".ljust(50),"String".ljust(10),"Action"
	while input_string:
		char = input_string[0]
		print str(stack).ljust(50),str(''.join(input_string)).ljust(10),
		if stack[-1] == "~":
			error = True
			break
		if char in table[int(stack[-1])]:
			action = table[int(stack[-1])][char]
			print action
			to_do = action[0]
			if not to_do == "A":
				num = int(action[1])
			if to_do == "s":
				stack.append(char)
				stack.append(num)
				if not 	char == "~":
					waste = input_string.pop(0)
			elif to_do == "g":
				stack.append(num)
			elif to_do == "r":
				(lhs,rhs) = productions_tuple[num]
				rhs = rhs[::-1]
				for sym in rhs:
					discard = stack.pop()
					if stack.pop() == sym:
						pass
					else:
						error = True
						break
				stack.append(lhs)
				if lhs in table[int(stack[-2])]:
					temp = table[int(stack[-2])][lhs]
					stack.append(temp[1])
				else:
					error = True
					break
			elif to_do == "A":
				accept = True
				print "String accepted! :)"
				exit()
		else: 
			error = True
			break
	if not accept:
		print
		print "String not accepted :("

start = str()
non_terminals = list()
terminals = list()
productions = parse_grammar("grammar.txt")
nullable = compute_nullable(productions)
first = compute_first(productions,nullable)
follow = compute_follow(productions,first,nullable)
productions_tuple = generate_productions()
print "Productions"
print_prod()
dfa = dfa()
dfa.construct()
dfa.print_dfa()
table = generate_table(dfa)
print
print_table(table)
print
if flag_SLR == True:
	input_string = raw_input("Enter the string to be parsed : ")
	parse(table,input_string)
if shift_reduce == True:
	print ("Shift reduce conflict! Not SLR grammar! Table formed taking reduce")
elif reduce_reduce == True:
	print ("Reduce reduce conflict! Not SLR grammar!")