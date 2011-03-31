#!/usr/bin/python

class RiskNode:
	def __init__(self, desc, prWin=None):
		self.__prWin__ = prWin
		self.desc = desc
		self.children = []

	def addChild(self, child, prChild):
		self.children.append((child, prChild))

	def prWin(self):
		if self.__prWin__ != None:
			return self.__prWin__

		self.__prWin__ = 0
		for child, prChild in self.children:
			self.__prWin__ += child.prWin() * prChild
		return self.__prWin__

	def __str__(self, depth=0, prNode=1):
		s = "%s%.2f -> %s\n" % ( "  "*depth, prNode, self.desc )
		for child, childPr in self.children:
			s += child.__str__(depth+1, childPr)
		return s

riskDags = {}
def riskDag(attackers, defendingCountries):
	""" attackers is the number of attackers
		defenders is an array of defending countries """
	defendingCountries = tuple(defendingCountries)
	stateTuple = (attackers, defendingCountries)
	if stateTuple in riskDags:
		return riskDags[stateTuple]

	state = "%sv%s" % stateTuple
	if len(defendingCountries) == 0:
		return RiskNode("W!" + state, 1)

	# attacker and defender always roll the maximum # of dice available to them
	defenders = defendingCountries[0]
	remainingCountries = list(defendingCountries[1:])
	attackDice = min(3, attackers-1)
	defendDice = min(2, defenders)
	if attackDice == 0:
		return RiskNode("L!" + state, 0)
	
	node = RiskNode(state)
	if defendDice == 0:
		assert attackers > 1
		# if there are no defenders, move on to the next country
		node.addChild(riskDag(attackers-1, remainingCountries), 1)
	else:
		deathDist = deathDistribution(attackDice, defendDice)
		for (deadAttackers, deadDefenders), prNextState in deathDist.iteritems():
		#for deaths, prNextState in deathDist.iteritems():
			#deadAttackers, deadDefenders = deaths
			nextState = riskDag(attackers-deadAttackers, [ defenders-deadDefenders ] + remainingCountries)
			node.addChild(nextState, prNextState)

	riskDags[stateTuple] = node
	return node

def allRolls(diceCount, previousDice=[], sideCount=6):
	if diceCount == 0:
		return [ previousDice ]
	
	rolls = []
	for roll in range(1, sideCount+1):
		rolls += allRolls(diceCount-1, previousDice + [ roll ])
	return rolls

deathDists = {}
def deathDistribution(attackDice, defendDice):
	assert attackDice > 0 and defendDice > 0
	diceTuple = ( attackDice, defendDice )
	if diceTuple in deathDists:
		return deathDists[diceTuple]

	deathDist = Distribution()
	allAttackerRolls = allRolls(attackDice)
	allDefenderRolls = allRolls(defendDice)
	for attackerRoll in allAttackerRolls:
		for defenderRoll in allDefenderRolls:
			deadAttackers = 0
			deadDefenders = 0
			attackerRoll.sort(reverse=True)
			defenderRoll.sort(reverse=True)
			for attackDie, defendDie in zip(attackerRoll, defenderRoll):
				if defendDie >= attackDie:
					deadAttackers += 1
				else:
					deadDefenders += 1
			deathTuple = (deadAttackers, deadDefenders)
			deathDist[deathTuple] += 1

	deathDist.normalize()
	deathDists[diceTuple] = deathDist
	return deathDist

class Distribution(dict):
	def __init__(self, d={}):
		for key, val in d.iteritems():
			self[key] = val

	def __getitem__(self, key):
		#if key in self:
			#return self[key]
		#else:
			#return 0
		try:
			return dict.__getitem__(self, key)
		except KeyError:
			return 0

	def normalize(self):
		s = 1.0*sum(self.values())
		for key in self:
			self[key] /= s

	def __mul__(self, scale):
		dist = Distribution(self)
		for key, val in dist.iteritems():
			dist[key] *= scale
		return dist

import sys
argv = sys.argv
#argv = [ 'foo', 2, 1 ]

if len(argv) < 3:
	print "Usage: %s [-p] attackerCount defendingCountry1 [defendingCountry2 ...]" % argv[0]
	sys.exit()

onlyPr = False
if '-p' in argv:
	onlyPr = True
	argv.remove('-p')

attackers = int(argv[1])
defendingCountries = []
for country in argv[2:]:
	defendingCountries.append(int(country))

dag = riskDag(attackers, defendingCountries)
# TODO - debug/help/precision options would be nice
#print dag
if onlyPr:
	print "%.3f" % dag.prWin()
else:
	print "%.3f chance of %d attackers defeating %s defenders" % ( dag.prWin(), attackers, defendingCountries )
